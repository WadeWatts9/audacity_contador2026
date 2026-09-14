from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.game import Game
from app.models.account import Account
from app.models.ledger import LedgerEntry
from app.models.contract import Contract
from app.schemas.bank import (
    PayToTeamRequest, CollectFromTeamRequest, TransferRequest,
    AdjustBalanceRequest, SetZeroRequest, UndoRequest
)
from app.routers.auth import get_admin_user
from app.engine.effects_engine import EffectsEngine
from app.engine.undo_manager import UndoManager
from app.routers.ws import manager

router = APIRouter(prefix="/bank", tags=["bank"])

@router.post("/pay")
async def pay_to_team(
    data: PayToTeamRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """El Banco paga un importe a un equipo."""
    acc_res = await db.execute(select(Account).where(Account.id == data.team_account_id))
    team = acc_res.scalar_one_or_none()
    if not team or team.is_closed:
        raise HTTPException(status_code=400, detail="Equipo no encontrado o cuenta cerrada.")

    bank = await EffectsEngine.get_bank_account(db, team.game_id)
    if bank.balance_available < data.amount_cents:
        raise HTTPException(status_code=400, detail="El Banco no tiene fondos suficientes para este pago.")

    game_res = await db.execute(select(Game).where(Game.id == team.game_id))
    game = game_res.scalar_one()

    if game.status == "finalizada":
        raise HTTPException(status_code=400, detail="La partida está finalizada y el tablero se encuentra fijado.")

    entry = await EffectsEngine.create_transfer_entry(
        session=db,
        game_id=team.game_id,
        source=bank,
        destination=team,
        amount=data.amount_cents,
        operation_type="pago_banco",
        reason=data.reason,
        actor_id=admin_user.id,
        approver_id=admin_user.id
    )
    await db.commit()

    await manager.broadcast(game.code, "BALANCE_UPDATE", {
        "source_id": bank.id,
        "dest_id": team.id,
        "amount": data.amount_cents,
        "reason": data.reason
    })

    return {"message": "Pago realizado con éxito.", "entry_id": entry.id}

@router.post("/collect")
async def collect_from_team(
    data: CollectFromTeamRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """El Banco cobra un importe a un equipo."""
    acc_res = await db.execute(select(Account).where(Account.id == data.team_account_id))
    team = acc_res.scalar_one_or_none()
    if not team or team.is_closed:
        raise HTTPException(status_code=400, detail="Equipo no encontrado o cuenta cerrada.")

    if team.balance_available < data.amount_cents:
        raise HTTPException(status_code=400, detail="El equipo no cuenta con fondos disponibles suficientes.")

    bank = await EffectsEngine.get_bank_account(db, team.game_id)
    game_res = await db.execute(select(Game).where(Game.id == team.game_id))
    game = game_res.scalar_one()

    if game.status == "finalizada":
        raise HTTPException(status_code=400, detail="La partida está finalizada y el tablero se encuentra fijado.")

    entry = await EffectsEngine.create_transfer_entry(
        session=db,
        game_id=team.game_id,
        source=team,
        destination=bank,
        amount=data.amount_cents,
        operation_type="cobro_banco",
        reason=data.reason,
        actor_id=admin_user.id,
        approver_id=admin_user.id
    )
    await db.commit()

    await manager.broadcast(game.code, "BALANCE_UPDATE", {
        "source_id": team.id,
        "dest_id": bank.id,
        "amount": data.amount_cents,
        "reason": data.reason
    })

    return {"message": "Cobro realizado con éxito.", "entry_id": entry.id}

@router.post("/transfer")
async def transfer_between_accounts(
    data: TransferRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Transferencia directa entre dos cuentas ordenada por el Banco."""
    if data.source_account_id == data.destination_account_id:
        raise HTTPException(status_code=400, detail="Cuentas origen y destino deben ser distintas.")

    s_res = await db.execute(select(Account).where(Account.id == data.source_account_id))
    source = s_res.scalar_one_or_none()
    d_res = await db.execute(select(Account).where(Account.id == data.destination_account_id))
    destination = d_res.scalar_one_or_none()

    if not source or not destination:
        raise HTTPException(status_code=404, detail="Cuenta origen o destino inexistente.")
    if source.is_closed or destination.is_closed:
        raise HTTPException(status_code=400, detail="Una de las cuentas está cerrada.")
    if source.balance_available < data.amount_cents:
        raise HTTPException(status_code=400, detail="Fondos disponibles insuficientes en la cuenta de origen.")

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
        operation_type="transferencia_admin",
        reason=data.reason,
        actor_id=admin_user.id,
        approver_id=admin_user.id
    )
    await db.commit()

    await manager.broadcast(game.code, "BALANCE_UPDATE", {
        "source_id": source.id,
        "dest_id": destination.id,
        "amount": data.amount_cents,
        "reason": data.reason
    })

    return {"message": "Transferencia realizada con éxito.", "entry_id": entry.id}

@router.post("/adjust")
async def adjust_balance(
    data: AdjustBalanceRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ajusta el saldo disponible a un valor objetivo, creando asientos contra
    la cuenta de emisión/ajustes explícita para evitar UPDATEs silenciosos.
    """
    acc_res = await db.execute(select(Account).where(Account.id == data.account_id))
    target_acc = acc_res.scalar_one_or_none()
    if not target_acc or target_acc.is_closed:
        raise HTTPException(status_code=400, detail="Cuenta no encontrada o cerrada.")

    current_avail = target_acc.balance_available
    diff = data.target_available_cents - current_avail

    if diff == 0:
        return {"message": "El saldo actual ya coincide con el saldo objetivo."}

    # Buscar cuenta de ajustes
    adj_res = await db.execute(
        select(Account).where(Account.game_id == target_acc.game_id, Account.account_type == "ajustes_emision")
    )
    adj_acc = adj_res.scalar_one_or_none()
    if not adj_acc:
        raise HTTPException(status_code=500, detail="Cuenta de ajustes del sistema no configurada.")

    game_res = await db.execute(select(Game).where(Game.id == target_acc.game_id))
    game = game_res.scalar_one()

    if diff > 0:
        # Aumentar saldo: transferir de cuenta de ajustes a target_acc
        entry = await EffectsEngine.create_transfer_entry(
            session=db,
            game_id=target_acc.game_id,
            source=None,  # Emisión
            destination=target_acc,
            amount=diff,
            operation_type="ajuste_positivo",
            reason=f"Ajuste de saldo: {data.reason} (de {current_avail/100:.2f} a {data.target_available_cents/100:.2f} TDL)",
            actor_id=admin_user.id,
            approver_id=admin_user.id
        )
    else:
        # Disminuir saldo: retirar monto de target_acc
        amt = abs(diff)
        entry = await EffectsEngine.create_transfer_entry(
            session=db,
            game_id=target_acc.game_id,
            source=target_acc,
            destination=None,  # Absorción
            amount=amt,
            operation_type="ajuste_negativo",
            reason=f"Ajuste de saldo: {data.reason} (de {current_avail/100:.2f} a {data.target_available_cents/100:.2f} TDL)",
            actor_id=admin_user.id,
            approver_id=admin_user.id
        )

    await db.commit()
    await manager.broadcast(game.code, "BALANCE_UPDATE", {"account_id": target_acc.id})
    return {"message": "Saldo ajustado correctamente.", "entry_id": entry.id}

@router.post("/set-zero")
async def set_zero(
    data: SetZeroRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Pone en cero el saldo disponible y reservado de una cuenta con advertencia
    de contratos activos y asientos de auditoría reversibles.
    """
    acc_res = await db.execute(select(Account).where(Account.id == data.account_id))
    target_acc = acc_res.scalar_one_or_none()
    if not target_acc:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")

    # Verificar si hay contratos activos
    contracts_res = await db.execute(
        select(Contract).where(
            Contract.game_id == target_acc.game_id,
            Contract.debtor_account_id == target_acc.id,
            Contract.status.in_(["activo", "vencido_impago"])
        )
    )
    active_contracts = contracts_res.scalars().all()
    if active_contracts and not data.resolve_contracts_explicitly:
        raise HTTPException(
            status_code=400,
            detail=f"Esta cuenta tiene {len(active_contracts)} contratos/deudas activos. Debés confirmar la resolución explícita de contratos antes de ponerla en cero."
        )

    total_avail = target_acc.balance_available
    total_res = target_acc.balance_reserved

    if total_avail == 0 and total_res == 0:
        return {"message": "La cuenta ya tiene saldo en cero."}

    game_res = await db.execute(select(Game).where(Game.id == target_acc.game_id))
    game = game_res.scalar_one()

    # Reducir disponible y reservado a cero
    target_acc.balance_available = 0
    target_acc.balance_reserved = 0

    entry = LedgerEntry(
        transaction_id=str(uuid.uuid4()) if 'uuid' in dir() else "zero_tx",
        game_id=target_acc.game_id,
        source_account_id=target_acc.id,
        destination_account_id=None,
        amount=total_avail + total_res,
        operation_type="puesta_a_cero",
        reason=f"Puesta a cero: {data.reason}",
        actor_id=admin_user.id,
        approver_id=admin_user.id,
        source_available_before=total_avail,
        source_available_after=0,
        source_reserved_before=total_res,
        source_reserved_after=0,
        state_snapshot={"prev_avail": total_avail, "prev_res": total_res}
    )
    db.add(entry)
    await db.commit()

    await manager.broadcast(game.code, "BALANCE_UPDATE", {"account_id": target_acc.id})
    return {"message": "Cuenta puesta en cero con éxito.", "entry_id": entry.id}

@router.post("/undo")
async def undo_transaction(
    data: UndoRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """Revierte («Deshacer») una transacción y sus estados asociados."""
    try:
        res = await UndoManager.revert_entry(
            session=db,
            entry_id=data.entry_id,
            approver_id=admin_user.id,
            reason_override=data.reason
        )
        await db.commit()
        return res
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
