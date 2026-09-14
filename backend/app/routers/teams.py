from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.user import User
from app.models.game import Game
from app.models.account import Account
from app.models.ledger import LedgerEntry
from app.models.contract import Contract
from app.routers.auth import get_current_user
from app.engine.effects_engine import EffectsEngine
from app.routers.ws import manager
from pydantic import BaseModel, Field

router = APIRouter(prefix="/teams", tags=["teams"])

class TeamTransferRequest(BaseModel):
    destination_account_id: int
    amount_cents: int = Field(..., gt=0)
    reason: str = Field(..., min_length=3, max_length=255)

@router.get("/me/status")
async def get_my_team_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retorna el estado patrimonial, deudas, seguros y turno del equipo autenticado."""
    acc_res = await db.execute(select(Account).where(Account.user_id == current_user.id))
    account = acc_res.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="No se encontró una cuenta para este usuario.")

    game_res = await db.execute(select(Game).where(Game.id == account.game_id))
    game = game_res.scalar_one()

    # Contratos y deudas
    c_res = await db.execute(
        select(Contract).where(
            Contract.game_id == game.id,
            Contract.debtor_account_id == account.id,
            Contract.status.in_(["activo", "vencido_impago"])
        )
    )
    debts = c_res.scalars().all()

    # Créditos a favor
    cr_res = await db.execute(
        select(Contract).where(
            Contract.game_id == game.id,
            Contract.creditor_account_id == account.id,
            Contract.status == "activo"
        )
    )
    credits = cr_res.scalars().all()

    # ¿Es su turno?
    is_my_turn = False
    if game.turn_order and len(game.turn_order) > 0:
        current_active_id = game.turn_order[game.current_team_order_index % len(game.turn_order)]
        is_my_turn = (current_active_id == account.id)

    # Últimos 10 movimientos propios
    ledger_res = await db.execute(
        select(LedgerEntry)
        .where(
            (LedgerEntry.source_account_id == account.id) |
            (LedgerEntry.destination_account_id == account.id)
        )
        .order_by(desc(LedgerEntry.id))
        .limit(10)
    )
    entries = ledger_res.scalars().all()

    history = []
    for e in entries:
        is_outgoing = (e.source_account_id == account.id)
        history.append({
            "id": e.id,
            "operation_type": e.operation_type,
            "amount": e.amount,
            "amount_tdl": f"{e.amount / 100:.2f}",
            "direction": "debito" if is_outgoing else "credito",
            "reason": e.reason,
            "timestamp": e.created_at.strftime("%H:%M:%S")
        })

    # Otros equipos activos y Banco Central para transferencias / pagos
    opponents_res = await db.execute(
        select(Account)
        .where(
            Account.game_id == game.id,
            Account.account_type.in_(["equipo", "banco"]),
            Account.id != account.id,
            Account.is_closed == False
        )
        .order_by(Account.account_type.asc(), Account.account_name.asc())
    )
    opponents = [
        {
            "id": a.id,
            "name": f"🏛️ {a.account_name}" if a.account_type == "banco" else f"👥 {a.account_name}"
        }
        for a in opponents_res.scalars().all()
    ]

    return {
        "account_id": account.id,
        "team_name": account.account_name,
        "symbol": current_user.token_symbol,
        "color": current_user.token_color,
        "balance_available": account.balance_available,
        "balance_reserved": account.balance_reserved,
        "balance_total": account.balance_total,
        "lost_turns": account.lost_turns,
        "has_insurance_e11": account.has_insurance_e11,
        "is_my_turn": is_my_turn,
        "current_round": game.current_turn_number,
        "debts_count": len(debts),
        "credits_count": len(credits),
        "history": history,
        "available_opponents": opponents
    }

@router.post("/transfer")
async def team_transfer(
    data: TeamTransferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permite a un equipo transferir desde su disponible a otro equipo o al Banco.
    No permite transferencias a sí mismo ni saldo negativo.
    """
    acc_res = await db.execute(select(Account).where(Account.user_id == current_user.id))
    source = acc_res.scalar_one_or_none()
    if not source or source.is_closed:
        raise HTTPException(status_code=400, detail="Cuenta origen inválida o cerrada.")

    if source.id == data.destination_account_id:
        raise HTTPException(status_code=400, detail="No podés transferirte a vos mismo.")

    dest_res = await db.execute(select(Account).where(Account.id == data.destination_account_id))
    destination = dest_res.scalar_one_or_none()
    if not destination or destination.is_closed or destination.game_id != source.game_id:
        raise HTTPException(status_code=400, detail="Cuenta destino no válida en esta partida.")

    if source.balance_available < data.amount_cents:
        raise HTTPException(
            status_code=400,
            detail=f"Saldo disponible insuficiente. Tenés {source.balance_available/100:.2f} TDL pero intentás transferir {data.amount_cents/100:.2f} TDL."
        )

    game_res = await db.execute(select(Game).where(Game.id == source.game_id))
    game = game_res.scalar_one()

    if game.status == "finalizada":
        raise HTTPException(status_code=400, detail="La partida está finalizada y el tablero se encuentra fijado.")

    entry = await EffectsEngine.create_transfer_entry(
        session=db,
        game_id=source.game_id,
        source=source,
        destination=destination,
        amount=data.amount_cents,
        operation_type="transferencia_equipo",
        reason=f"Transferencia de equipo: {data.reason}",
        actor_id=current_user.id,
        approver_id=None
    )
    await db.commit()

    await manager.broadcast(game.code, "BALANCE_UPDATE", {
        "source_id": source.id,
        "dest_id": destination.id,
        "amount": data.amount_cents,
        "reason": data.reason
    })

    return {
        "message": "Transferencia completada con éxito.",
        "entry_id": entry.id,
        "amount_transferred": data.amount_cents,
        "new_balance_available": source.balance_available
    }
