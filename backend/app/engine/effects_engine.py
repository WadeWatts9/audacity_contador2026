from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.account import Account
from app.models.ledger import LedgerEntry
from app.models.contract import Contract, ScheduledEvent
from app.models.game import Game

def round_half_up(value: Decimal) -> int:
    """Rounds a Decimal value half-up to the nearest integer (cents)."""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def compute_pct(base_cents: int, pct: float) -> int:
    """Compute percentage of integer cents with exact half-up rounding."""
    return round_half_up(Decimal(base_cents) * Decimal(str(pct)))

class EffectsEngine:
    """
    Motor de ejecución atómica para los 15 retos económicos E01-E15 y efectos de tablero.
    Garantiza contabilidad balanceada, prevención de sobregiro y registro de auditoría.
    """

    @staticmethod
    async def get_bank_account(session: AsyncSession, game_id: int) -> Account:
        query = select(Account).where(
            Account.game_id == game_id,
            Account.account_type == "banco"
        )
        res = await session.execute(query)
        bank = res.scalar_one_or_none()
        if not bank:
            raise ValueError("No se encontró la cuenta del Banco para esta partida.")
        return bank

    @staticmethod
    async def create_transfer_entry(
        session: AsyncSession,
        game_id: int,
        source: Optional[Account],
        destination: Optional[Account],
        amount: int,
        operation_type: str,
        reason: str,
        actor_id: Optional[int] = None,
        approver_id: Optional[int] = None,
        rule_version: str = "1.0",
        idempotency_key: Optional[str] = None,
        state_snapshot: Optional[Dict[str, Any]] = None
    ) -> LedgerEntry:
        """
        Crea un asiento balanceado y aplica la transferencia sobre los balances disponibles.
        """
        tx_id = str(uuid.uuid4())
        
        src_avail_before = source.balance_available if source else None
        src_res_before = source.balance_reserved if source else None
        dest_avail_before = destination.balance_available if destination else None
        dest_res_before = destination.balance_reserved if destination else None
        
        if source:
            if source.balance_available < amount:
                raise ValueError(f"Fondos disponibles insuficientes en {source.account_name}. Requiere {amount/100:.2f} TDL pero tiene {source.balance_available/100:.2f} TDL.")
            source.balance_available -= amount
            
        if destination:
            destination.balance_available += amount
            
        src_avail_after = source.balance_available if source else None
        src_res_after = source.balance_reserved if source else None
        dest_avail_after = destination.balance_available if destination else None
        dest_res_after = destination.balance_reserved if destination else None

        entry = LedgerEntry(
            transaction_id=tx_id,
            game_id=game_id,
            source_account_id=source.id if source else None,
            destination_account_id=destination.id if destination else None,
            amount=amount,
            operation_type=operation_type,
            reason=reason,
            rule_version=rule_version,
            idempotency_key=idempotency_key,
            source_available_before=src_avail_before,
            source_available_after=src_avail_after,
            source_reserved_before=src_res_before,
            source_reserved_after=src_res_after,
            dest_available_before=dest_avail_before,
            dest_available_after=dest_avail_after,
            dest_reserved_before=dest_res_before,
            dest_reserved_after=dest_res_after,
            actor_id=actor_id,
            approver_id=approver_id,
            state_snapshot=state_snapshot or {}
        )
        session.add(entry)
        await session.flush()
        return entry

    # ==================== EFECTOS E01 - E15 ====================

    @classmethod
    async def apply_e01(
        cls, session: AsyncSession, game: Game, team: Account, approver_id: int
    ) -> Dict[str, Any]:
        """
        E01 - Inversión a futuro:
        Pierde 2 turnos. Al comenzar el tercero (n+3), el banco paga 15% de la base B inicial.
        """
        base_b = team.balance_available
        bonus = compute_pct(base_b, 0.15)
        
        # Incrementar turnos perdidos
        team.lost_turns += 2
        
        current_opp = team.turn_opportunities_count
        due_opp = current_opp + 3
        
        bank = await cls.get_bank_account(session, game.id)
        
        contract = Contract(
            game_id=game.id,
            contract_type="inversion_e01",
            description=f"E01 - Inversión diferida: +{bonus/100:.2f} TDL en oportunidad {due_opp}",
            creditor_account_id=team.id,
            debtor_account_id=bank.id,
            principal_amount=bonus,
            created_at_opportunity=current_opp,
            total_installments=1,
            status="activo",
            metadata_json={"base_original": base_b, "bonus_amount": bonus, "due_opportunity": due_opp}
        )
        session.add(contract)
        await session.flush()
        
        sched = ScheduledEvent(
            contract_id=contract.id,
            game_id=game.id,
            target_account_id=team.id,
            due_opportunity_number=due_opp,
            priority_step=2,  # Paso 2: bonificaciones diferidas
            installment_number=1,
            event_type="bonificacion_diferida",
            amount_expected=bonus,
            metadata_json={"contract_id": contract.id}
        )
        session.add(sched)
        
        # Registro en ledger (sin movimiento inmediato de dinero, pero audita estado)
        entry = LedgerEntry(
            transaction_id=str(uuid.uuid4()),
            game_id=game.id,
            source_account_id=None,
            destination_account_id=team.id,
            amount=0,
            operation_type="efecto_e01",
            reason="E01 - Inversión a futuro: +2 turnos perdidos y bonificación programada 15%",
            actor_id=team.user_id,
            approver_id=approver_id,
            state_snapshot={"lost_turns_added": 2, "bonus_scheduled": bonus, "contract_id": contract.id}
        )
        session.add(entry)
        await session.flush()
        
        return {
            "card": "E01",
            "base": base_b,
            "bonus_expected": bonus,
            "lost_turns": 2,
            "due_opportunity": due_opp
        }

    @classmethod
    async def apply_e02(
        cls, session: AsyncSession, game: Game, lender: Account, debtor: Account, approver_id: int
    ) -> Dict[str, Any]:
        """
        E02 - Préstamo entre equipos:
        Presta 40% de B_prestamista al deudor.
        3 cuotas: cada una 20% del disponible del deudor al inicio de sus próximos 3 turnos.
        """
        if lender.id == debtor.id:
            raise ValueError("No podés prestarte dinero a vos mismo.")
            
        base_b = lender.balance_available
        loan_amount = compute_pct(base_b, 0.40)
        
        # Transferir capital del prestamista al deudor
        entry = await cls.create_transfer_entry(
            session=session,
            game_id=game.id,
            source=lender,
            destination=debtor,
            amount=loan_amount,
            operation_type="prestamo_e02",
            reason=f"E02 - Desembolso de préstamo de {lender.account_name} a {debtor.account_name}",
            actor_id=lender.user_id,
            approver_id=approver_id
        )
        
        debtor_opp = debtor.turn_opportunities_count
        
        contract = Contract(
            game_id=game.id,
            contract_type="prestamo_e02",
            description=f"E02 - Préstamo de {loan_amount/100:.2f} TDL a 3 cuotas del 20% disponible",
            creditor_account_id=lender.id,
            debtor_account_id=debtor.id,
            principal_amount=loan_amount,
            created_at_opportunity=debtor_opp,
            total_installments=3,
            status="activo",
            metadata_json={"disbursement_tx": entry.id, "principal": loan_amount}
        )
        session.add(contract)
        await session.flush()
        
        # Crear los 3 eventos programados para n+1, n+2, n+3 del deudor
        for inst in [1, 2, 3]:
            sched = ScheduledEvent(
                contract_id=contract.id,
                game_id=game.id,
                target_account_id=debtor.id,
                due_opportunity_number=debtor_opp + inst,
                priority_step=3,  # Paso 3: cuotas y deudas
                installment_number=inst,
                event_type="cuota_variable_e02",
                amount_expected=None,  # Variable (20% del disponible en ese momento)
                metadata_json={"contract_id": contract.id, "installment_number": inst, "lender_account_id": lender.id}
            )
            session.add(sched)
            
        entry.state_snapshot = {"contract_id": contract.id, "disbursed": loan_amount}
        await session.flush()
        
        return {
            "card": "E02",
            "principal": loan_amount,
            "lender": lender.account_name,
            "debtor": debtor.account_name,
            "contract_id": contract.id
        }

    @classmethod
    async def apply_e03(
        cls, session: AsyncSession, game: Game, team: Account, approver_id: int
    ) -> Dict[str, Any]:
        """E03 - Inflación: Paga al banco 10% del saldo."""
        base_b = team.balance_available
        loss = compute_pct(base_b, 0.10)
        bank = await cls.get_bank_account(session, game.id)
        
        entry = await cls.create_transfer_entry(
            session=session,
            game_id=game.id,
            source=team,
            destination=bank,
            amount=loss,
            operation_type="efecto_e03",
            reason="E03 - Inflación: pago del 10% del disponible al Banco",
            actor_id=team.user_id,
            approver_id=approver_id,
            state_snapshot={"base": base_b, "loss": loss}
        )
        return {"card": "E03", "base": base_b, "paid": loss, "remaining": team.balance_available}

    @classmethod
    async def apply_e04(
        cls, session: AsyncSession, game: Game, team: Account, dice_rolls: Tuple[int, int, int], approver_id: int
    ) -> Dict[str, Any]:
        """
        E04 - Tres dados, una decisión:
        3 dados (1-6). Suma <= 6: paga 20% al banco. Suma > 6: banco paga 30%.
        """
        for d in dice_rolls:
            if not (1 <= d <= 6):
                raise ValueError("Cada dado debe estar entre 1 y 6.")
                
        total_sum = sum(dice_rolls)
        base_b = team.balance_available
        bank = await cls.get_bank_account(session, game.id)
        
        if total_sum <= 6:
            amount = compute_pct(base_b, 0.20)
            entry = await cls.create_transfer_entry(
                session=session,
                game_id=game.id,
                source=team,
                destination=bank,
                amount=amount,
                operation_type="efecto_e04_perdida",
                reason=f"E04 - Tres dados (suma {total_sum} <= 6): pago del 20% al Banco",
                actor_id=team.user_id,
                approver_id=approver_id,
                state_snapshot={"dice": list(dice_rolls), "sum": total_sum, "base": base_b}
            )
            outcome = "perdida_20"
        else:
            amount = compute_pct(base_b, 0.30)
            entry = await cls.create_transfer_entry(
                session=session,
                game_id=game.id,
                source=bank,
                destination=team,
                amount=amount,
                operation_type="efecto_e04_ganancia",
                reason=f"E04 - Tres dados (suma {total_sum} > 6): cobro del 30% del Banco",
                actor_id=team.user_id,
                approver_id=approver_id,
                state_snapshot={"dice": list(dice_rolls), "sum": total_sum, "base": base_b}
            )
            outcome = "ganancia_30"
            
        return {
            "card": "E04",
            "dice": dice_rolls,
            "sum": total_sum,
            "outcome": outcome,
            "amount": amount,
            "final_balance": team.balance_available
        }

    @classmethod
    async def apply_e05(
        cls, session: AsyncSession, game: Game, team: Account, approver_id: int
    ) -> Dict[str, Any]:
        """
        E05 - Ahorro programado:
        Reserva 30% de disponible hasta inicio de próximo turno.
        Al vencer se liberan los 30% y banco paga 20% del monto reservado.
        """
        base_b = team.balance_available
        reserved_amount = compute_pct(base_b, 0.30)
        interest_amount = compute_pct(reserved_amount, 0.20)
        
        # Mover de disponible a reservado
        team.balance_available -= reserved_amount
        team.balance_reserved += reserved_amount
        
        due_opp = team.turn_opportunities_count + 1
        bank = await cls.get_bank_account(session, game.id)
        
        contract = Contract(
            game_id=game.id,
            contract_type="ahorro_e05",
            description=f"E05 - Ahorro: {reserved_amount/100:.2f} TDL reservados + 20% interés ({interest_amount/100:.2f} TDL)",
            creditor_account_id=team.id,
            debtor_account_id=bank.id,
            principal_amount=reserved_amount,
            fixed_repayment_amount=interest_amount,
            created_at_opportunity=team.turn_opportunities_count,
            total_installments=1,
            status="activo",
            metadata_json={"reserved_amount": reserved_amount, "interest_amount": interest_amount}
        )
        session.add(contract)
        await session.flush()
        
        sched = ScheduledEvent(
            contract_id=contract.id,
            game_id=game.id,
            target_account_id=team.id,
            due_opportunity_number=due_opp,
            priority_step=1,  # Paso 1: liberar depósitos y abonar sus intereses
            installment_number=1,
            event_type="liberar_ahorro_e05",
            amount_expected=interest_amount,
            metadata_json={"contract_id": contract.id, "reserved_amount": reserved_amount, "interest": interest_amount}
        )
        session.add(sched)
        
        entry = LedgerEntry(
            transaction_id=str(uuid.uuid4()),
            game_id=game.id,
            source_account_id=team.id,
            destination_account_id=team.id,
            amount=reserved_amount,
            operation_type="reserva_e05",
            reason=f"E05 - Constitución de ahorro programado 30% ({reserved_amount/100:.2f} TDL)",
            actor_id=team.user_id,
            approver_id=approver_id,
            source_available_before=base_b,
            source_available_after=team.balance_available,
            source_reserved_before=team.balance_reserved - reserved_amount,
            source_reserved_after=team.balance_reserved,
            state_snapshot={"reserved": reserved_amount, "interest": interest_amount, "contract_id": contract.id}
        )
        session.add(entry)
        await session.flush()
        
        return {
            "card": "E05",
            "reserved": reserved_amount,
            "interest": interest_amount,
            "due_opportunity": due_opp,
            "available": team.balance_available,
            "total": team.balance_total
        }

    @classmethod
    async def apply_e06(
        cls, session: AsyncSession, game: Game, team: Account, approver_id: int
    ) -> Dict[str, Any]:
        """E06 - Contribución tributaria: Paga 12% al banco."""
        base_b = team.balance_available
        tax = compute_pct(base_b, 0.12)
        bank = await cls.get_bank_account(session, game.id)
        
        entry = await cls.create_transfer_entry(
            session=session,
            game_id=game.id,
            source=team,
            destination=bank,
            amount=tax,
            operation_type="efecto_e06",
            reason="E06 - Contribución tributaria del 12% al Banco",
            actor_id=team.user_id,
            approver_id=approver_id,
            state_snapshot={"base": base_b, "tax": tax}
        )
        return {"card": "E06", "base": base_b, "paid": tax, "remaining": team.balance_available}

    @classmethod
    async def apply_e07(
        cls, session: AsyncSession, game: Game, team: Account, approver_id: int
    ) -> Dict[str, Any]:
        """E07 - Apoyo al emprendimiento: Banco paga 25% (no reembolsable)."""
        base_b = team.balance_available
        grant = compute_pct(base_b, 0.25)
        bank = await cls.get_bank_account(session, game.id)
        
        entry = await cls.create_transfer_entry(
            session=session,
            game_id=game.id,
            source=bank,
            destination=team,
            amount=grant,
            operation_type="efecto_e07",
            reason="E07 - Subsidio no reembolsable del 25% acreditado por el Banco",
            actor_id=team.user_id,
            approver_id=approver_id,
            state_snapshot={"base": base_b, "grant": grant}
        )
        return {"card": "E07", "base": base_b, "received": grant, "final": team.balance_available}

    @classmethod
    async def apply_e08(
        cls, session: AsyncSession, game: Game, team: Account, approver_id: int
    ) -> Dict[str, Any]:
        """
        E08 - Reparación urgente: Paga 15% al banco.
        Protegido por seguro E11 si está activo!
        """
        base_b = team.balance_available
        amount = compute_pct(base_b, 0.15)
        bank = await cls.get_bank_account(session, game.id)
        
        if team.has_insurance_e11:
            # Consume seguro y evita la pérdida
            team.has_insurance_e11 = False
            entry = LedgerEntry(
                transaction_id=str(uuid.uuid4()),
                game_id=game.id,
                source_account_id=team.id,
                destination_account_id=bank.id,
                amount=0,
                operation_type="seguro_consumido_e08",
                reason=f"E08 - Reparación urgente EVITADA mediante Seguro E11 (Pérdida evitada: {amount/100:.2f} TDL)",
                actor_id=team.user_id,
                approver_id=approver_id,
                state_snapshot={"insurance_consumed": True, "saved_amount": amount, "base": base_b}
            )
            session.add(entry)
            await session.flush()
            return {"card": "E08", "base": base_b, "insurance_used": True, "saved": amount, "paid": 0}
        else:
            entry = await cls.create_transfer_entry(
                session=session,
                game_id=game.id,
                source=team,
                destination=bank,
                amount=amount,
                operation_type="efecto_e08",
                reason="E08 - Reparación urgente: pago del 15% al Banco",
                actor_id=team.user_id,
                approver_id=approver_id,
                state_snapshot={"base": base_b, "paid": amount}
            )
            return {"card": "E08", "base": base_b, "insurance_used": False, "paid": amount, "remaining": team.balance_available}

    @classmethod
    async def apply_e09(
        cls, session: AsyncSession, game: Game, team_a: Account, team_b: Account, approver_id: int
    ) -> Dict[str, Any]:
        """
        E09 - Intercambio comercial:
        Ambos calculan 10% sobre sus disponibles iniciales y se transfieren simultáneamente.
        """
        if team_a.id == team_b.id:
            raise ValueError("Debés elegir a otro equipo para el intercambio comercial.")
            
        base_a = team_a.balance_available
        base_b = team_b.balance_available
        
        flow_a_to_b = compute_pct(base_a, 0.10)
        flow_b_to_a = compute_pct(base_b, 0.10)
        
        if team_a.balance_available < flow_a_to_b:
            raise ValueError(f"{team_a.account_name} no tiene fondos suficientes para el intercambio.")
        if team_b.balance_available < flow_b_to_a:
            raise ValueError(f"{team_b.account_name} no tiene fondos suficientes para el intercambio.")
            
        team_a.balance_available = team_a.balance_available - flow_a_to_b + flow_b_to_a
        team_b.balance_available = team_b.balance_available - flow_b_to_a + flow_a_to_b
        
        tx_id = str(uuid.uuid4())
        entry = LedgerEntry(
            transaction_id=tx_id,
            game_id=game.id,
            source_account_id=team_a.id,
            destination_account_id=team_b.id,
            amount=flow_a_to_b,
            operation_type="efecto_e09",
            reason=f"E09 - Intercambio comercial simultáneo: {team_a.account_name} paga {flow_a_to_b/100:.2f} y recibe {flow_b_to_a/100:.2f}",
            actor_id=team_a.user_id,
            approver_id=approver_id,
            source_available_before=base_a,
            source_available_after=team_a.balance_available,
            dest_available_before=base_b,
            dest_available_after=team_b.balance_available,
            state_snapshot={
                "base_a": base_a, "flow_a_to_b": flow_a_to_b,
                "base_b": base_b, "flow_b_to_a": flow_b_to_a
            }
        )
        session.add(entry)
        await session.flush()
        
        return {
            "card": "E09",
            "team_a": {"name": team_a.account_name, "base": base_a, "paid": flow_a_to_b, "received": flow_b_to_a, "final": team_a.balance_available},
            "team_b": {"name": team_b.account_name, "base": base_b, "paid": flow_b_to_a, "received": flow_a_to_b, "final": team_b.balance_available}
        }

    @classmethod
    async def apply_e10(
        cls, session: AsyncSession, game: Game, team: Account, approver_id: int
    ) -> Dict[str, Any]:
        """
        E10 - Campaña de ventas:
        Paga al banco 5% de disponible (B).
        Luego banco paga 20% del saldo resultante (B2).
        """
        base_1 = team.balance_available
        cost = compute_pct(base_1, 0.05)
        bank = await cls.get_bank_account(session, game.id)
        
        # Paso 1: débito de costo publicitario
        team.balance_available -= cost
        bank.balance_available += cost
        base_2 = team.balance_available
        
        # Paso 2: crédito de ventas
        gain = compute_pct(base_2, 0.20)
        bank.balance_available -= gain
        team.balance_available += gain
        
        entry = LedgerEntry(
            transaction_id=str(uuid.uuid4()),
            game_id=game.id,
            source_account_id=team.id,
            destination_account_id=bank.id,
            amount=cost,
            operation_type="efecto_e10",
            reason=f"E10 - Campaña de ventas: costo 5% ({cost/100:.2f} TDL) y retorno 20% ({gain/100:.2f} TDL)",
            actor_id=team.user_id,
            approver_id=approver_id,
            source_available_before=base_1,
            source_available_after=team.balance_available,
            state_snapshot={"base_1": base_1, "cost": cost, "base_2": base_2, "gain": gain}
        )
        session.add(entry)
        await session.flush()
        
        return {
            "card": "E10",
            "base_1": base_1,
            "cost": cost,
            "base_2": base_2,
            "gain": gain,
            "final": team.balance_available
        }

    @classmethod
    async def apply_e11(
        cls, session: AsyncSession, game: Game, team: Account, accept: bool, approver_id: int
    ) -> Dict[str, Any]:
        """
        E11 - Seguro del negocio:
        Opción de pagar 5% de B para activar cobertura única frente a E08 o E13.
        Si ya tiene seguro activo, no se cobra prima y se mantiene.
        """
        base_b = team.balance_available
        if not accept:
            return {"card": "E11", "accepted": False, "message": "Seguro rechazado."}
            
        if team.has_insurance_e11:
            return {
                "card": "E11",
                "accepted": True,
                "already_insured": True,
                "message": "Ya cuenta con una póliza de seguro activa. No se cobra nueva prima."
            }
            
        premium = compute_pct(base_b, 0.05)
        bank = await cls.get_bank_account(session, game.id)
        
        entry = await cls.create_transfer_entry(
            session=session,
            game_id=game.id,
            source=team,
            destination=bank,
            amount=premium,
            operation_type="prima_seguro_e11",
            reason="E11 - Prima del Seguro del Negocio (5% disponible)",
            actor_id=team.user_id,
            approver_id=approver_id,
            state_snapshot={"base": base_b, "premium": premium}
        )
        team.has_insurance_e11 = True
        return {"card": "E11", "accepted": True, "premium": premium, "insured": True, "final": team.balance_available}

    @classmethod
    async def apply_e12(
        cls, session: AsyncSession, game: Game, giver: Account, receiver: Account, approver_id: int
    ) -> Dict[str, Any]:
        """E12 - Cooperación solidaria: Transfiere 10% a otro equipo (donación)."""
        if giver.id == receiver.id:
            raise ValueError("Debés elegir a otro equipo para la cooperación solidaria.")
            
        base_b = giver.balance_available
        donation = compute_pct(base_b, 0.10)
        
        entry = await cls.create_transfer_entry(
            session=session,
            game_id=game.id,
            source=giver,
            destination=receiver,
            amount=donation,
            operation_type="efecto_e12",
            reason=f"E12 - Cooperación solidaria: donación de {giver.account_name} a {receiver.account_name}",
            actor_id=giver.user_id,
            approver_id=approver_id,
            state_snapshot={"base": base_b, "donation": donation}
        )
        return {
            "card": "E12",
            "giver": giver.account_name,
            "receiver": receiver.account_name,
            "amount": donation,
            "giver_final": giver.balance_available,
            "receiver_final": receiver.balance_available
        }

    @classmethod
    async def apply_e13(
        cls, session: AsyncSession, game: Game, team: Account, approver_id: int
    ) -> Dict[str, Any]:
        """
        E13 - Fraude comercial: Paga 20% al banco.
        Si tiene seguro E11 activo, se consume y evita la pérdida!
        """
        base_b = team.balance_available
        loss = compute_pct(base_b, 0.20)
        bank = await cls.get_bank_account(session, game.id)
        
        if team.has_insurance_e11:
            team.has_insurance_e11 = False
            entry = LedgerEntry(
                transaction_id=str(uuid.uuid4()),
                game_id=game.id,
                source_account_id=team.id,
                destination_account_id=bank.id,
                amount=0,
                operation_type="seguro_consumido_e13",
                reason=f"E13 - Fraude comercial EVITADO mediante Seguro E11 (Pérdida evitada: {loss/100:.2f} TDL)",
                actor_id=team.user_id,
                approver_id=approver_id,
                state_snapshot={"insurance_consumed": True, "saved_amount": loss, "base": base_b}
            )
            session.add(entry)
            await session.flush()
            return {"card": "E13", "base": base_b, "insurance_used": True, "saved": loss, "paid": 0}
        else:
            entry = await cls.create_transfer_entry(
                session=session,
                game_id=game.id,
                source=team,
                destination=bank,
                amount=loss,
                operation_type="efecto_e13",
                reason="E13 - Fraude comercial: pago del 20% al Banco",
                actor_id=team.user_id,
                approver_id=approver_id,
                state_snapshot={"base": base_b, "loss": loss}
            )
            return {"card": "E13", "base": base_b, "insurance_used": False, "paid": loss, "remaining": team.balance_available}

    @classmethod
    async def apply_e14(
        cls, session: AsyncSession, game: Game, team: Account, approver_id: int
    ) -> Dict[str, Any]:
        """
        E14 - Crédito del banco:
        Banco presta 30% de disponible (C).
        Al inicio de su segundo próximo turno (n+2), devuelve C + 10% de C.
        """
        base_b = team.balance_available
        capital_c = compute_pct(base_b, 0.30)
        interest_10 = compute_pct(capital_c, 0.10)
        repayment_fixed = capital_c + interest_10
        
        bank = await cls.get_bank_account(session, game.id)
        
        # Desembolso del banco al equipo
        entry = await cls.create_transfer_entry(
            session=session,
            game_id=game.id,
            source=bank,
            destination=team,
            amount=capital_c,
            operation_type="desembolso_e14",
            reason=f"E14 - Desembolso de crédito bancario ({capital_c/100:.2f} TDL)",
            actor_id=team.user_id,
            approver_id=approver_id
        )
        
        current_opp = team.turn_opportunities_count
        due_opp = current_opp + 2
        
        contract = Contract(
            game_id=game.id,
            contract_type="prestamo_e14",
            description=f"E14 - Crédito Banco: Principal {capital_c/100:.2f} TDL, vencimiento fijo {repayment_fixed/100:.2f} TDL en turno n+2",
            creditor_account_id=bank.id,
            debtor_account_id=team.id,
            principal_amount=capital_c,
            fixed_repayment_amount=repayment_fixed,
            created_at_opportunity=current_opp,
            total_installments=1,
            status="activo",
            metadata_json={"disbursement_tx": entry.id, "principal": capital_c, "interest": interest_10, "due_opportunity": due_opp}
        )
        session.add(contract)
        await session.flush()
        
        sched = ScheduledEvent(
            contract_id=contract.id,
            game_id=game.id,
            target_account_id=team.id,
            due_opportunity_number=due_opp,
            priority_step=3,  # Paso 3: cuotas y deudas
            installment_number=1,
            event_type="cuota_fija_e14",
            amount_expected=repayment_fixed,
            metadata_json={"contract_id": contract.id, "fixed_amount": repayment_fixed}
        )
        session.add(sched)
        
        entry.state_snapshot = {"contract_id": contract.id, "principal": capital_c, "repayment_fixed": repayment_fixed}
        await session.flush()
        
        return {
            "card": "E14",
            "base": base_b,
            "disbursed": capital_c,
            "repayment_due": repayment_fixed,
            "due_opportunity": due_opp,
            "final": team.balance_available
        }

    @classmethod
    async def apply_e15(
        cls, session: AsyncSession, game: Game, team: Account, die_roll: int, approver_id: int
    ) -> Dict[str, Any]:
        """
        E15 - Demanda cambiante:
        Dado (1-6). Par: +20% desde el banco. Impar: -10% al banco.
        """
        if not (1 <= die_roll <= 6):
            raise ValueError("El valor del dado debe ser un entero entre 1 y 6.")
            
        base_b = team.balance_available
        bank = await cls.get_bank_account(session, game.id)
        
        if die_roll % 2 == 0:  # Par
            amount = compute_pct(base_b, 0.20)
            entry = await cls.create_transfer_entry(
                session=session,
                game_id=game.id,
                source=bank,
                destination=team,
                amount=amount,
                operation_type="efecto_e15_par",
                reason=f"E15 - Demanda favorable (dado par {die_roll}): cobro del 20% del Banco",
                actor_id=team.user_id,
                approver_id=approver_id,
                state_snapshot={"die": die_roll, "is_even": True, "base": base_b, "amount": amount}
            )
            outcome = "par_ganancia_20"
        else:  # Impar
            amount = compute_pct(base_b, 0.10)
            entry = await cls.create_transfer_entry(
                session=session,
                game_id=game.id,
                source=team,
                destination=bank,
                amount=amount,
                operation_type="efecto_e15_impar",
                reason=f"E15 - Demanda desfavorable (dado impar {die_roll}): pago del 10% al Banco",
                actor_id=team.user_id,
                approver_id=approver_id,
                state_snapshot={"die": die_roll, "is_even": False, "base": base_b, "amount": amount}
            )
            outcome = "impar_perdida_10"
            
        return {
            "card": "E15",
            "die": die_roll,
            "outcome": outcome,
            "amount": amount,
            "final": team.balance_available
        }
