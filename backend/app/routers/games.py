import csv
import io
import secrets
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from app.database import get_db, get_server_time
from app.config import settings
from app.models.user import User
from app.models.game import Game
from app.models.account import Account
from app.models.card import Card, CardInstance
from app.models.contract import Contract, ScheduledEvent
from app.models.turn import TurnRecord
from app.models.ledger import LedgerEntry
from app.schemas.game import (
    GameCreate, GameResponse, TeamCredentials, RankingItem, GameSummaryResponse
)
from app.security import hash_password, generate_secure_password, generate_simple_team_password
from app.routers.auth import get_current_user, get_admin_user
from app.routers.ws import manager
from app.engine.cards_data import CARDS_CATALOG
from app.engine.pdf_report import generate_game_audit_pdf
from app.engine.student_guide_pdf import generate_student_guide_pdf

router = APIRouter(prefix="/games", tags=["games"])

# Perfiles de equipos con usuario animal_contador estricto y sin sufijos
GENIALLY_TEAMS = [
    {"username": "gallo_contador", "animal": "gallo", "display_name": "Contador Gallo", "symbol": "🐓", "color": "#9ed7ef"},
    {"username": "leon_contador", "animal": "leon", "display_name": "Contador León", "symbol": "🦁", "color": "#f6d662"},
    {"username": "perro_contador", "animal": "perro", "display_name": "Contador Perro", "symbol": "🐕", "color": "#f39192"},
    {"username": "mano_contador", "animal": "mano", "display_name": "Contador Mano", "symbol": "✋", "color": "#add475"},
    {"username": "estrella_contador", "animal": "estrella", "display_name": "Contador Estrella", "symbol": "★", "color": "#d9b2e9"}
]

PREZI_TEAMS = [
    {"username": "diamante_contador", "animal": "diamante", "display_name": "Contador Diamante", "symbol": "💎", "color": "#0875be"},
    {"username": "auto_contador", "animal": "auto", "display_name": "Contador Auto", "symbol": "🚗", "color": "#169260"},
    {"username": "sombrero_contador", "animal": "sombrero", "display_name": "Contador Sombrero", "symbol": "🎩", "color": "#dfa72a"},
    {"username": "cerdo_contador", "animal": "cerdo", "display_name": "Contador Cerdo", "symbol": "🐷", "color": "#d45a8d"}
]

def sanitize_csv_cell(value: Any) -> str:
    """Evita inyección de fórmulas en CSV (CWE-1236)."""
    s = str(value if value is not None else "")
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + s
    return s

async def create_game_core(
    db: AsyncSession,
    admin_user: User,
    data: GameCreate
) -> tuple[Game, List[TeamCredentials]]:
    """
    Función base reutilizable para crear una partida:
    - Genera código corto de 4 caracteres legibles (ej: 'ECO1', 'A7B2')
    - Configura Banco Central y cuenta de ajustes
    - Reutiliza o crea usuarios fijos 'animal_contador' con contraseñas sencillas
    - Instancia tarjetas
    """
    while True:
        code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4))
        existing = await db.execute(select(Game).where(Game.code == code))
        if not existing.scalar_one_or_none():
            break

    profile = data.profile.lower()
    teams_def = PREZI_TEAMS if profile == "prezi" else GENIALLY_TEAMS

    game = Game(
        code=code,
        name=data.name,
        profile=profile,
        status="activa",
        initial_team_balance=data.initial_team_balance,
        initial_bank_balance=data.initial_bank_balance,
        rules_config=data.rules_config or {}
    )
    db.add(game)
    await db.flush()

    # 1. Cuenta del Banco
    bank_account = Account(
        game_id=game.id,
        user_id=admin_user.id,
        account_type="banco",
        account_name="BANCO CENTRAL AUDACITY",
        balance_available=data.initial_bank_balance,
        balance_reserved=0
    )
    db.add(bank_account)

    # 2. Cuenta de Ajustes / Emisión
    adjustments_account = Account(
        game_id=game.id,
        user_id=admin_user.id,
        account_type="ajustes_emision",
        account_name="CUENTA DE EMISIÓN Y AJUSTES",
        balance_available=0,
        balance_reserved=0
    )
    db.add(adjustments_account)
    await db.flush()

    # 3. Equipos y Cuentas (Usuario animal_contador estricto sin sufijo y contraseña sencilla)
    credentials_sheet: List[TeamCredentials] = []
    account_ids = []

    for t in teams_def:
        uname = t["username"]
        plain_pwd = generate_simple_team_password(t["animal"])
        
        # Si el usuario ya existe de una partida previa, actualizar su contraseña y datos
        user_res = await db.execute(select(User).where(User.username == uname))
        user = user_res.scalar_one_or_none()
        if user:
            user.password_hash = hash_password(plain_pwd)
            user.display_name = t["display_name"]
            user.token_symbol = t["symbol"]
            user.token_color = t["color"]
            user.is_active = True
        else:
            user = User(
                username=uname,
                password_hash=hash_password(plain_pwd),
                role="equipo",
                display_name=t["display_name"],
                token_symbol=t["symbol"],
                token_color=t["color"],
                is_active=True
            )
            db.add(user)
            await db.flush()

        acc = Account(
            game_id=game.id,
            user_id=user.id,
            account_type="equipo",
            account_name=t["display_name"],
            balance_available=data.initial_team_balance,
            balance_reserved=0
        )
        db.add(acc)
        await db.flush()
        account_ids.append(acc.id)

        credentials_sheet.append(TeamCredentials(
            username=uname,
            display_name=t["display_name"],
            password=plain_pwd,
            token_symbol=t["symbol"],
            token_color=t["color"],
            account_id=acc.id
        ))

    # Orden inicial
    game.turn_order = account_ids
    await db.flush()

    # 4. Catálogo base
    for c in CARDS_CATALOG:
        card_exist = await db.execute(select(Card).where(Card.code == c["code"]))
        if not card_exist.scalar_one_or_none():
            new_card = Card(
                code=c["code"],
                deck_type=c["deck_type"],
                title=c["title"],
                text=c["text"],
                teacher_answer=c.get("teacher_answer"),
                source=c.get("source"),
                engine_rule=c.get("engine_rule"),
                target_description=c.get("target_description"),
                image_path=c["image_path"]
            )
            db.add(new_card)
    await db.flush()

    # 5. Instancias de 30 tarjetas
    for c in CARDS_CATALOG:
        inst = CardInstance(
            game_id=game.id,
            card_code=c["code"],
            status="disponible"
        )
        db.add(inst)

    await db.commit()
    await db.refresh(game)
    return game, credentials_sheet

@router.post("", response_model=GameResponse)
async def create_game(
    data: GameCreate,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea una nueva partida con código de sala corto (4 caracteres),
    usuarios 'animal_contador' y contraseñas sencillas.
    """
    game, credentials_sheet = await create_game_core(db, admin_user, data)
    resp = GameResponse.from_orm(game)
    resp.credentials_sheet = credentials_sheet
    return resp

@router.get("/{code}", response_model=GameSummaryResponse)
async def get_game_summary(code: str, db: AsyncSession = Depends(get_db)):
    """Obtiene el estado completo de la partida y ranking actualizado."""
    g_res = await db.execute(select(Game).where(Game.code == code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    # Banco
    b_res = await db.execute(select(Account).where(Account.game_id == game.id, Account.account_type == "banco"))
    bank = b_res.scalar_one_or_none()

    # Cuentas de equipos
    t_res = await db.execute(
        select(Account)
        .join(User, Account.user_id == User.id)
        .where(Account.game_id == game.id, Account.account_type == "equipo")
    )
    teams = t_res.scalars().all()

    # Contratos pendientes de deuda por equipo
    debts_res = await db.execute(
        select(Contract).where(Contract.game_id == game.id, Contract.status.in_(["activo", "vencido_impago"]))
    )
    active_contracts = debts_res.scalars().all()

    ranking_items = []
    for team in teams:
        user_res = await db.execute(select(User).where(User.id == team.user_id))
        user = user_res.scalar_one_or_none()

        pending_debts_cents = sum(
            (c.fixed_repayment_amount or c.principal_amount) - c.total_repaid
            for c in active_contracts if c.debtor_account_id == team.id
        )
        active_credits_cents = sum(
            c.principal_amount - c.total_repaid
            for c in active_contracts if c.creditor_account_id == team.id
        )

        ranking_items.append({
            "account_id": team.id,
            "team_name": team.account_name,
            "token_symbol": user.token_symbol if user else "★",
            "token_color": user.token_color if user else "#9ed7ef",
            "balance_available": team.balance_available,
            "balance_reserved": team.balance_reserved,
            "balance_total": team.balance_total,
            "lost_turns": team.lost_turns,
            "has_insurance_e11": team.has_insurance_e11,
            "pending_debts": pending_debts_cents,
            "active_credits": active_credits_cents
        })

    # Ordenar por balance total (disponible + reservado) descendente
    ranking_items.sort(key=lambda x: (-x["balance_total"], x["team_name"]))

    # Asignar puestos con soporte de empates
    ranked_list: List[RankingItem] = []
    current_rank = 1
    for idx, item in enumerate(ranking_items):
        if idx > 0 and item["balance_total"] == ranking_items[idx - 1]["balance_total"]:
            item_rank = ranked_list[idx - 1].rank
        else:
            item_rank = current_rank
        current_rank = idx + 2
        ranked_list.append(RankingItem(rank=item_rank, **item))

    # Equipo activo en turno
    active_team_id = None
    active_team_name = None
    if game.turn_order and len(game.turn_order) > 0:
        order_idx = game.current_team_order_index % len(game.turn_order)
        active_team_id = game.turn_order[order_idx]
        for t in teams:
            if t.id == active_team_id:
                active_team_name = t.account_name
                break

    tz = pytz.timezone(settings.TIMEZONE)
    server_time_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")

    return GameSummaryResponse(
        game=GameResponse.from_orm(game),
        bank_balance=bank.balance_available if bank else 0,
        bank_account_id=bank.id if bank else 0,
        active_team_id=active_team_id,
        active_team_name=active_team_name,
        ranking=ranked_list,
        server_time=server_time_str
    )

@router.get("/{code}/feed")
async def get_game_feed(
    code: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Feed de auditoría en tiempo real de transacciones."""
    g_res = await db.execute(select(Game).where(Game.code == code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    entries_res = await db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.game_id == game.id)
        .order_by(LedgerEntry.id.desc())
        .limit(limit)
    )
    entries = entries_res.scalars().all()
    
    tz = pytz.timezone(settings.TIMEZONE)
    feed = []
    for e in entries:
        dt_local = e.created_at.replace(tzinfo=pytz.utc).astimezone(tz)
        feed.append({
            "id": e.id,
            "transaction_id": e.transaction_id,
            "operation_type": e.operation_type,
            "amount": e.amount,
            "amount_tdl": f"{e.amount / 100:.2f}",
            "reason": e.reason,
            "source_id": e.source_account_id,
            "destination_id": e.destination_account_id,
            "is_reverted": e.is_reverted,
            "timestamp": dt_local.strftime("%H:%M:%S"),
            "full_timestamp": dt_local.strftime("%Y-%m-%d %H:%M:%S")
        })
    return feed

@router.get("/{code}/export-csv")
async def export_csv(
    code: str,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Exportación de auditoría completa a CSV protegida contra inyección de fórmulas.
    """
    g_res = await db.execute(select(Game).where(Game.code == code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    entries_res = await db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.game_id == game.id)
        .order_by(LedgerEntry.id.asc())
    )
    entries = entries_res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output, dialect="excel")
    
    # Encabezados
    writer.writerow([
        "ID Asiento", "Hora Local (Montevideo)", "Tipo Operación", "Monto TDL",
        "Motivo", "Cuenta Origen ID", "Disponible Origen Después",
        "Cuenta Destino ID", "Disponible Destino Después", "Revertido"
    ])

    tz = pytz.timezone(settings.TIMEZONE)
    for e in entries:
        dt_local = e.created_at.replace(tzinfo=pytz.utc).astimezone(tz)
        writer.writerow([
            sanitize_csv_cell(e.id),
            sanitize_csv_cell(dt_local.strftime("%Y-%m-%d %H:%M:%S")),
            sanitize_csv_cell(e.operation_type),
            sanitize_csv_cell(f"{e.amount / 100:.2f}"),
            sanitize_csv_cell(e.reason),
            sanitize_csv_cell(e.source_account_id),
            sanitize_csv_cell(f"{e.source_available_after / 100:.2f}" if e.source_available_after is not None else ""),
            sanitize_csv_cell(e.destination_account_id),
            sanitize_csv_cell(f"{e.dest_available_after / 100:.2f}" if e.dest_available_after is not None else ""),
            sanitize_csv_cell("SI" if e.is_reverted else "NO")
        ])

    csv_data = output.getvalue()
    filename = f"audacity_partida_{game.code}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/{code}/end-game")
async def end_game(
    code: str,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cierra oficialmente la partida, fija el tablero y cuentas, e impide nuevos movimientos.
    """
    g_res = await db.execute(select(Game).where(Game.code == code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    if game.status == "finalizada":
        return {"status": "finalizada", "message": "La partida ya se encuentra finalizada y fijada."}

    game.status = "finalizada"

    tz = pytz.timezone(settings.TIMEZONE)
    dt_now = datetime.now(tz)

    close_entry = LedgerEntry(
        game_id=game.id,
        transaction_id=f"TX-END-{game.code}",
        operation_type="cierre_partida",
        source_account_id=None,
        destination_account_id=None,
        amount=0,
        reason=f"FIN DE PARTIDA: Cierre oficial y congelamiento de tablero ({dt_now.strftime('%H:%M:%S')})",
        actor_id=admin_user.id,
        approver_id=admin_user.id,
        state_snapshot={"status": "finalizada", "finalized_at": dt_now.isoformat()}
    )
    db.add(close_entry)
    await db.commit()
    await db.refresh(game)

    # Difundir cierre a todos los clientes por WebSocket
    await manager.broadcast(game.code, "GAME_ENDED", {
        "game_code": game.code,
        "status": "finalizada",
        "message": "¡La partida ha finalizado! El tablero y las posiciones finales han quedado fijados."
    })

    return {"status": "finalizada", "message": "Partida finalizada con éxito. Tablero fijado."}

@router.get("/{code}/export-pdf")
async def export_pdf(
    code: str,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Genera el informe oficial completo de auditoría y cierre de partida en PDF (ReportLab).
    """
    g_res = await db.execute(select(Game).where(Game.code == code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    # Banco
    b_res = await db.execute(select(Account).where(Account.game_id == game.id, Account.account_type == "banco"))
    bank = b_res.scalar_one_or_none()
    bank_tdl = (bank.balance_available / 100) if bank else 0.0

    # Cuentas de equipos
    t_res = await db.execute(
        select(Account)
        .join(User, Account.user_id == User.id)
        .where(Account.game_id == game.id, Account.account_type == "equipo")
    )
    teams = t_res.scalars().all()

    # Contratos
    debts_res = await db.execute(
        select(Contract).where(Contract.game_id == game.id)
    )
    all_contracts = debts_res.scalars().all()

    # Ranking
    ranking_items = []
    for team in teams:
        user_res = await db.execute(select(User).where(User.id == team.user_id))
        user = user_res.scalar_one_or_none()

        pending_debts = sum(
            (c.fixed_repayment_amount or c.principal_amount) - c.total_repaid
            for c in all_contracts if c.debtor_account_id == team.id and c.status in ["activo", "vencido_impago"]
        )

        ranking_items.append({
            "account_id": team.id,
            "team_name": team.account_name,
            "token_symbol": user.token_symbol if user else "★",
            "balance_available": team.balance_available,
            "balance_reserved": team.balance_reserved,
            "balance_total": team.balance_total,
            "pending_debts": pending_debts
        })

    ranking_items.sort(key=lambda x: (-x["balance_total"], x["team_name"]))

    ranked_list = []
    current_rank = 1
    for idx, item in enumerate(ranking_items):
        if idx > 0 and item["balance_total"] == ranking_items[idx - 1]["balance_total"]:
            item_rank = ranked_list[idx - 1]["rank"]
        else:
            item_rank = current_rank
        current_rank = idx + 2
        ranked_list.append({"rank": item_rank, **item})

    # Diccionario de nombres de cuentas para fácil resolución
    acc_res = await db.execute(select(Account).where(Account.game_id == game.id))
    all_accounts = {a.id: a.account_name for a in acc_res.scalars().all()}

    # Formatear contratos
    contract_data = []
    for c in all_contracts:
        contract_data.append({
            "id": c.id,
            "contract_type": c.contract_type,
            "creditor_name": all_accounts.get(c.creditor_account_id, "Banco"),
            "debtor_name": all_accounts.get(c.debtor_account_id, "Equipo"),
            "principal_amount": c.principal_amount,
            "total_repaid": c.total_repaid,
            "status": c.status
        })

    # Asientos de ledger
    entries_res = await db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.game_id == game.id)
        .order_by(LedgerEntry.id.asc())
    )
    entries = entries_res.scalars().all()

    tz = pytz.timezone(settings.TIMEZONE)
    ledger_data = []
    for e in entries:
        dt_local = e.created_at.replace(tzinfo=pytz.utc).astimezone(tz)
        ledger_data.append({
            "id": e.id,
            "timestamp": dt_local.strftime("%H:%M:%S"),
            "operation_type": e.operation_type,
            "amount": e.amount,
            "source_name": all_accounts.get(e.source_account_id),
            "destination_name": all_accounts.get(e.destination_account_id),
            "reason": e.reason,
            "is_reverted": e.is_reverted
        })

    pdf_bytes = generate_game_audit_pdf(
        game_code=game.code,
        game_name=game.name,
        game_profile=game.profile,
        game_status=game.status,
        created_at=game.created_at,
        finalized_at=datetime.utcnow() if game.status == "finalizada" else None,
        bank_balance_tdl=bank_tdl,
        ranked_teams=ranked_list,
        ledger_entries=ledger_data,
        contracts=contract_data,
        timezone_name=settings.TIMEZONE
    )

    filename = f"audacity_auditoria_{game.code}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/admin/clean-database")
@router.post("/clean-database")
async def clean_database(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina todos los datos de partidas, cuentas, contratos, transacciones y usuarios de equipos,
    dejando la base de datos completamente limpia y lista para nuevas partidas.
    Preserva intacto al usuario administrador docente.
    """
    # 1. Eventos programados y contratos/deudas
    await db.execute(delete(ScheduledEvent))
    await db.execute(delete(Contract))

    # 2. Libro diario contable
    await db.execute(delete(LedgerEntry))

    # 3. Tarjetas asignadas y turnos jugados
    await db.execute(delete(CardInstance))
    await db.execute(delete(TurnRecord))

    # 4. Cuentas bancarias y de equipos
    await db.execute(delete(Account))

    # 5. Partidas creadas
    await db.execute(delete(Game))

    # 6. Usuarios contadores de equipos (conservando el administrador docente)
    await db.execute(delete(User).where(User.id != admin_user.id, User.role != "admin_docente"))

    await db.commit()

    return {
        "status": "success",
        "message": "Base de datos reiniciada con éxito. Todos los registros y usuarios contadores fueron eliminados. Podés crear una nueva partida limpia."
    }


@router.get("/student-guide-pdf")
async def download_student_guide_pdf():
    """Descarga directa del PDF oficial de la Guía del Estudiante."""
    guide_bytes = generate_student_guide_pdf()
    return Response(
        content=guide_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=guia_estudiante_audacity.pdf"}
    )
