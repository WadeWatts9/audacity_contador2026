from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, asc
from app.models.account import Account
from app.models.contract import Contract, ScheduledEvent
from app.models.game import Game
from app.models.turn import TurnRecord
from app.engine.effects_engine import EffectsEngine, compute_pct

class TurnProcessor:
    """
    Procesa el ciclo de turnos e inicios de turno según el orden estricto de la especificación:
    Paso 1: Liberar depósitos y abonar intereses (E05, plazo fijo, ahorro)
    Paso 2: Abonar bonificaciones diferidas (E01)
    Paso 3: Cobrar cuotas y deudas por fecha de creación (desempate por ID) (E02, E14)
    Paso 4: Descontar un turno perdido o habilitar lanzamiento
    """

    @classmethod
    async def process_turn_start(
        cls,
        session: AsyncSession,
        game: Game,
        team_account: Account,
        approver_id: int
    ) -> Dict[str, Any]:
        """
        Ejecuta los eventos programados al inicio del turno para el equipo activo.
        """
        # Incrementar contador de oportunidades de turno del equipo
        team_account.turn_opportunities_count += 1
        opp = team_account.turn_opportunities_count
        
        bank = await EffectsEngine.get_bank_account(session, game.id)
        
        events_executed = []
        
        # Consultar eventos programados pendientes para este equipo con due_opportunity_number <= opp
        query = (
            select(ScheduledEvent)
            .where(
                ScheduledEvent.game_id == game.id,
                ScheduledEvent.target_account_id == team_account.id,
                ScheduledEvent.status.in_(["pendiente", "vencido_pendiente"]),
                ScheduledEvent.due_opportunity_number <= opp
            )
            .order_by(
                ScheduledEvent.priority_step.asc(),
                ScheduledEvent.created_at.asc(),
                ScheduledEvent.id.asc()
            )
        )
        res = await session.execute(query)
        scheduled_events = res.scalars().all()

        # =========================================================
        # PASO 1: Liberar depósitos y abonar sus intereses
        # =========================================================
        step1_events = [e for e in scheduled_events if e.priority_step == 1]
        for event in step1_events:
            contract_res = await session.execute(select(Contract).where(Contract.id == event.contract_id))
            contract = contract_res.scalar_one_or_none()
            
            if event.event_type == "liberar_ahorro_e05":
                reserved = contract.principal_amount
                interest = contract.fixed_repayment_amount or 0
                
                # Liberar capital reservado
                if team_account.balance_reserved >= reserved:
                    team_account.balance_reserved -= reserved
                    team_account.balance_available += reserved
                else:
                    # Fallback si reserva fue afectada
                    avail_res = team_account.balance_reserved
                    team_account.balance_reserved = 0
                    team_account.balance_available += avail_res
                
                # Abonar interés desde el banco si tiene fondos
                if bank.balance_available >= interest:
                    await EffectsEngine.create_transfer_entry(
                        session=session,
                        game_id=game.id,
                        source=bank,
                        destination=team_account,
                        amount=interest,
                        operation_type="interes_e05",
                        reason=f"E05 - Pago de interés de ahorro programado (+{interest/100:.2f} TDL)",
                        actor_id=approver_id,
                        approver_id=approver_id,
                        state_snapshot={"contract_id": contract.id, "principal_released": reserved}
                    )
                else:
                    # Banco con fondos insuficientes: mantener pendiente de resolución docente
                    event.status = "vencido_pendiente"
                    continue
                
                event.status = "ejecutado"
                event.executed_at = datetime.utcnow()
                event.amount_executed = interest
                contract.status = "ejecutado"
                events_executed.append({
                    "type": "liberar_ahorro",
                    "reserved_released": reserved,
                    "interest_paid": interest
                })

        # =========================================================
        # PASO 2: Abonar bonificaciones diferidas (E01)
        # =========================================================
        step2_events = [e for e in scheduled_events if e.priority_step == 2]
        for event in step2_events:
            contract_res = await session.execute(select(Contract).where(Contract.id == event.contract_id))
            contract = contract_res.scalar_one_or_none()
            
            if event.event_type == "bonificacion_diferida":
                bonus = event.amount_expected or contract.principal_amount
                if bank.balance_available >= bonus:
                    await EffectsEngine.create_transfer_entry(
                        session=session,
                        game_id=game.id,
                        source=bank,
                        destination=team_account,
                        amount=bonus,
                        operation_type="bonificacion_e01",
                        reason=f"E01 - Acreditación de bonificación diferida (+{bonus/100:.2f} TDL)",
                        actor_id=approver_id,
                        approver_id=approver_id,
                        state_snapshot={"contract_id": contract.id}
                    )
                    event.status = "ejecutado"
                    event.executed_at = datetime.utcnow()
                    event.amount_executed = bonus
                    contract.status = "ejecutado"
                    events_executed.append({"type": "bonificacion_e01", "bonus": bonus})
                else:
                    event.status = "vencido_pendiente"

        # =========================================================
        # PASO 3: Cobrar cuotas y deudas por fecha de creación (E02, E14)
        # =========================================================
        step3_events = [e for e in scheduled_events if e.priority_step == 3]
        for event in step3_events:
            contract_res = await session.execute(select(Contract).where(Contract.id == event.contract_id))
            contract = contract_res.scalar_one_or_none()
            if not contract:
                continue

            if event.event_type == "cuota_variable_e02":
                # La cuota E02 se calcula justo antes de su propio débito: 20% del disponible actual
                cuota_amount = compute_pct(team_account.balance_available, 0.20)
                
                # Obtener prestamista
                lender_res = await session.execute(select(Account).where(Account.id == contract.creditor_account_id))
                lender = lender_res.scalar_one_or_none()
                
                if lender and cuota_amount > 0:
                    await EffectsEngine.create_transfer_entry(
                        session=session,
                        game_id=game.id,
                        source=team_account,
                        destination=lender,
                        amount=cuota_amount,
                        operation_type="cuota_e02",
                        reason=f"E02 - Cobro de cuota {event.installment_number}/3 ({cuota_amount/100:.2f} TDL) a favor de {lender.account_name}",
                        actor_id=approver_id,
                        approver_id=approver_id,
                        state_snapshot={"contract_id": contract.id, "installment": event.installment_number}
                    )
                
                contract.total_repaid += cuota_amount
                contract.installments_completed += 1
                event.status = "ejecutado"
                event.amount_executed = cuota_amount
                event.executed_at = datetime.utcnow()
                
                if contract.installments_completed >= 3:
                    contract.status = "ejecutado"
                    
                events_executed.append({
                    "type": "cuota_e02",
                    "installment": event.installment_number,
                    "amount": cuota_amount,
                    "lender": lender.account_name if lender else None
                })

            elif event.event_type == "cuota_fija_e14":
                # Cuota fija de E14 (capital + 10% de interés pactado)
                fixed_amount = event.amount_expected or contract.fixed_repayment_amount
                if team_account.balance_available >= fixed_amount:
                    await EffectsEngine.create_transfer_entry(
                        session=session,
                        game_id=game.id,
                        source=team_account,
                        destination=bank,
                        amount=fixed_amount,
                        operation_type="devolucion_e14",
                        reason=f"E14 - Devolución fija de crédito bancario ({fixed_amount/100:.2f} TDL)",
                        actor_id=approver_id,
                        approver_id=approver_id,
                        state_snapshot={"contract_id": contract.id}
                    )
                    event.status = "ejecutado"
                    event.amount_executed = fixed_amount
                    event.executed_at = datetime.utcnow()
                    contract.total_repaid += fixed_amount
                    contract.installments_completed += 1
                    contract.status = "ejecutado"
                    events_executed.append({
                        "type": "devolucion_e14",
                        "amount": fixed_amount,
                        "status": "pagada"
                    })
                else:
                    # Fondo insuficiente: queda deuda vencida sin cobro parcial
                    event.status = "vencido_pendiente"
                    contract.status = "vencido_impago"
                    events_executed.append({
                        "type": "devolucion_e14",
                        "amount": fixed_amount,
                        "status": "vencido_impago",
                        "warning": "Fondos insuficientes para cancelar crédito E14. Registrado como deuda vencida."
                    })

        # =========================================================
        # PASO 4: Descontar un turno perdido o habilitar lanzamiento
        # =========================================================
        turn_lost = False
        if team_account.lost_turns > 0:
            team_account.lost_turns -= 1
            turn_lost = True
            
        await session.flush()
        
        return {
            "team_id": team_account.id,
            "team_name": team_account.account_name,
            "opportunity_number": opp,
            "turn_lost": turn_lost,
            "remaining_lost_turns": team_account.lost_turns,
            "events_executed": events_executed,
            "balance_available": team_account.balance_available,
            "balance_reserved": team_account.balance_reserved,
            "balance_total": team_account.balance_total
        }
