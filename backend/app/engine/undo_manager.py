from typing import Dict, Any, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.ledger import LedgerEntry
from app.models.account import Account
from app.models.contract import Contract, ScheduledEvent

class UndoManager:
    """
    Gestor de reversión («Deshacer») atómica de movimientos y estados asociados.
    Restaura saldos, reservas, seguros, turnos perdidos y estados de contratos.
    """

    @classmethod
    async def revert_entry(
        cls,
        session: AsyncSession,
        entry_id: int,
        approver_id: int,
        reason_override: Optional[str] = None
    ) -> Dict[str, Any]:
        query = select(LedgerEntry).where(LedgerEntry.id == entry_id)
        res = await session.execute(query)
        entry = res.scalar_one_or_none()
        
        if not entry:
            raise ValueError(f"No se encontró el asiento contable con ID {entry_id}.")
        if entry.is_reverted:
            raise ValueError("Esta operación ya fue revertida previamente.")

        # Obtener cuentas involucradas
        source = None
        destination = None
        if entry.source_account_id:
            s_res = await session.execute(select(Account).where(Account.id == entry.source_account_id))
            source = s_res.scalar_one_or_none()
        if entry.destination_account_id:
            d_res = await session.execute(select(Account).where(Account.id == entry.destination_account_id))
            destination = d_res.scalar_one_or_none()

        amount = entry.amount
        snapshot = entry.state_snapshot or {}

        # 1. Revertir movimientos de dinero
        if source and destination and source.id != destination.id:
            # Revertir transferencia: devolver amount a source, restar de destination
            if destination.balance_available < amount:
                raise ValueError(
                    f"No se puede revertir: la cuenta destino ({destination.account_name}) no tiene fondos suficientes ({destination.balance_available/100:.2f} TDL) para devolver {amount/100:.2f} TDL."
                )
            destination.balance_available -= amount
            source.balance_available += amount

        elif entry.operation_type in ["reserva_e05", "reserva_casilla"]:
            # Revertir reserva dentro de la misma cuenta
            reserved_amt = snapshot.get("reserved", amount)
            if source:
                source.balance_reserved -= reserved_amt
                source.balance_available += reserved_amt

        # 2. Revertir estado asociado en snapshot
        # Turnos perdidos
        if "lost_turns_added" in snapshot and source:
            source.lost_turns = max(0, source.lost_turns - snapshot["lost_turns_added"])

        # Seguro E11 consumido
        if snapshot.get("insurance_consumed") and source:
            source.has_insurance_e11 = True  # Restaurar seguro

        # Seguro E11 contratado (prima pagada)
        if entry.operation_type == "prima_seguro_e11" and source:
            source.has_insurance_e11 = False

        # Contratos creados
        if "contract_id" in snapshot:
            contract_res = await session.execute(select(Contract).where(Contract.id == snapshot["contract_id"]))
            contract = contract_res.scalar_one_or_none()
            if contract:
                contract.status = "revertido"
                # Cancelar eventos programados asociados
                sched_res = await session.execute(
                    select(ScheduledEvent).where(ScheduledEvent.contract_id == contract.id)
                )
                for sched in sched_res.scalars().all():
                    sched.status = "revertido"

        # 3. Crear asiento inverso de reversión enlazado
        reversal_tx_id = str(uuid.uuid4())
        reversal_reason = reason_override or f"REVERSIÓN de asiento #{entry.id}: {entry.reason}"
        
        reversal_entry = LedgerEntry(
            transaction_id=reversal_tx_id,
            game_id=entry.game_id,
            source_account_id=entry.destination_account_id,
            destination_account_id=entry.source_account_id,
            amount=amount,
            operation_type="reversion",
            reason=reversal_reason,
            rule_version=entry.rule_version,
            source_available_before=destination.balance_available + amount if destination else None,
            source_available_after=destination.balance_available if destination else None,
            dest_available_before=source.balance_available - amount if source else None,
            dest_available_after=source.balance_available if source else None,
            actor_id=approver_id,
            approver_id=approver_id,
            reverts_entry_id=entry.id,
            state_snapshot={"reverted_entry_id": entry.id}
        )
        session.add(reversal_entry)
        await session.flush()

        # Marcar original como revertido
        entry.is_reverted = True
        entry.reverted_by_id = reversal_entry.id
        await session.flush()

        return {
            "original_entry_id": entry.id,
            "reversal_entry_id": reversal_entry.id,
            "amount_reverted": amount,
            "message": "Operación y estado revertidos con éxito."
        }
