from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_db
from app.models.user import User
from app.models.game import Game
from app.models.account import Account
from app.models.card import Card, CardInstance
from app.schemas.card import (
    CardPublicResponse, CardPrivateResponse, CardInstanceResponse,
    CardDrawRequest, CardValidatePRequest, CardExecuteERequest,
    CardStatusUpdateRequest
)
from app.routers.auth import get_current_user, get_admin_user, get_optional_user
from app.engine.effects_engine import EffectsEngine, compute_pct
from app.routers.ws import manager

router = APIRouter(prefix="/cards", tags=["cards"])

@router.get("/decks/{game_code}")
async def get_deck_status(
    game_code: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna el estado de los dos mazos (P y E) sin respuestas docentes.
    Apto para equipos, proyección y tablero general.
    Si el solicitante no es admin_docente, las consignas de tarjetas aún 'disponibles'
    se protegen y se revelan únicamente al pasar a 'resuelta_usada'.
    """
    g_res = await db.execute(select(Game).where(Game.code == game_code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    query = (
        select(CardInstance, Card)
        .join(Card, CardInstance.card_code == Card.code)
        .where(CardInstance.game_id == game.id)
    )
    res = await db.execute(query)
    rows = res.all()

    is_admin = current_user is not None and current_user.role == "admin_docente"

    p_cards = []
    e_cards = []
    for inst, card in rows:
        item = {
            "instance_id": inst.id,
            "code": card.code,
            "deck_type": card.deck_type,
            "title": card.title,
            "text": card.text,
            "image_path": card.image_path,
            "engine_rule": card.engine_rule,
            "status": inst.status,
            "assigned_to": inst.assigned_to_account_id
        }
        if card.deck_type == "P":
            p_item = dict(item)
            if not is_admin and inst.status == "disponible":
                p_item["title"] = f"Pregunta {card.code}"
                p_item["text"] = "Pregunta protegida en el mazo. Se revelará cuando el docente la seleccione y marque como no disponible."
                p_item["image_path"] = ""
            p_cards.append(p_item)
        else:
            e_item = dict(item)
            if not is_admin and inst.status == "disponible":
                e_item["title"] = f"Reto {card.code}"
                e_item["text"] = "Reto protegido en el mazo. Se revelará cuando el docente lo seleccione y marque como no disponible."
                e_item["image_path"] = ""
            e_cards.append(e_item)

    p_cards.sort(key=lambda x: x["code"])
    e_cards.sort(key=lambda x: x["code"])

    return {
        "count_p_available": sum(1 for c in p_cards if c["status"] == "disponible"),
        "count_e_available": sum(1 for c in e_cards if c["status"] == "disponible"),
        "p_deck": p_cards,
        "e_deck": e_cards
    }

@router.get("/admin/deck-p/{game_code}")
async def get_admin_p_deck(
    game_code: str,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Catálogo de preguntas P01-P15 CON claves de respuesta docente.
    Estrictamente protegido: solo accesible para rol admin_docente.
    """
    g_res = await db.execute(select(Game).where(Game.code == game_code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    query = (
        select(CardInstance, Card)
        .join(Card, CardInstance.card_code == Card.code)
        .where(CardInstance.game_id == game.id, Card.deck_type == "P")
        .order_by(Card.code.asc())
    )
    res = await db.execute(query)
    rows = res.all()

    catalog = []
    for inst, card in rows:
        catalog.append({
            "instance_id": inst.id,
            "code": card.code,
            "title": card.title,
            "text": card.text,
            "teacher_answer": card.teacher_answer,
            "source": card.source,
            "image_path": card.image_path,
            "status": inst.status,
            "assigned_to": inst.assigned_to_account_id
        })
    return catalog

@router.post("/draw/{game_code}")
async def draw_card(
    game_code: str,
    data: CardDrawRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Extracción atómica de una tarjeta del mazo con bloqueo de fila.
    Evita que dos equipos tomen la misma instancia simultáneamente.
    """
    g_res = await db.execute(select(Game).where(Game.code == game_code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    if game.status == "finalizada":
        raise HTTPException(status_code=400, detail="La partida está finalizada y el tablero se encuentra fijado.")

    # Buscar cuenta del solicitante o cuenta activa
    team = None
    if current_user.role == "admin_docente":
        if game.turn_order and len(game.turn_order) > 0:
            order_idx = game.current_team_order_index % len(game.turn_order)
            active_id = game.turn_order[order_idx]
            t_res = await db.execute(select(Account).where(Account.id == active_id))
            team = t_res.scalar_one_or_none()
    else:
        acc_res = await db.execute(select(Account).where(Account.user_id == current_user.id, Account.game_id == game.id, Account.account_type == "equipo"))
        team = acc_res.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=400, detail="No se pudo determinar el equipo que toma la tarjeta.")

    # Consulta con FOR UPDATE para bloqueo concurrente
    query = (
        select(CardInstance)
        .join(Card, CardInstance.card_code == Card.code)
        .where(
            CardInstance.game_id == game.id,
            Card.deck_type == data.deck_type,
            CardInstance.status == "disponible"
        )
        .with_for_update()
    )
    if data.card_code:
        query = query.where(CardInstance.card_code == data.card_code.upper().strip())

    res = await db.execute(query)
    instance = res.scalars().first()
    if not instance:
        raise HTTPException(status_code=404, detail="No hay tarjetas disponibles en este mazo con ese criterio.")

    instance.status = "asignada"
    instance.assigned_to_account_id = team.id
    instance.assigned_at = datetime.utcnow()
    await db.commit()

    card_res = await db.execute(select(Card).where(Card.code == instance.card_code))
    card = card_res.scalar_one()

    # Difundir evento de extracción a todos los clientes
    await manager.broadcast(game.code, "CARD_DRAWN", {
        "instance_id": instance.id,
        "code": card.code,
        "deck_type": card.deck_type,
        "title": card.title,
        "text": card.text,
        "image_path": card.image_path,
        "team_name": team.account_name
    })

    return {
        "instance_id": instance.id,
        "code": card.code,
        "deck_type": card.deck_type,
        "title": card.title,
        "text": card.text,
        "image_path": card.image_path,
        "team_id": team.id,
        "team_name": team.account_name
    }

@router.post("/validate-p")
async def validate_p_card(
    data: CardValidatePRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Validación manual por el docente de una tarjeta de pregunta P01-P15.
    Permite elegir el efecto al acertar o errar entre:
    - Porcentajes (estándar, moderado, casilla 2 o personalizado)
    - Montos fijos específicos en TDL (+3.000 / -1.500, etc.)
    - 'Otros' para efectos no computacionales con descripción para auditoría
    """
    inst_res = await db.execute(select(CardInstance).where(CardInstance.id == data.instance_id))
    instance = inst_res.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instancia de tarjeta no encontrada.")

    team_res = await db.execute(select(Account).where(Account.id == instance.assigned_to_account_id))
    team = team_res.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=400, detail="La tarjeta no tiene equipo asignado.")

    game_res = await db.execute(select(Game).where(Game.id == team.game_id))
    game = game_res.scalar_one()

    if game.status == "finalizada":
        raise HTTPException(status_code=400, detail="La partida está finalizada y el tablero se encuentra fijado.")

    bank = await EffectsEngine.get_bank_account(db, game.id)

    base_b = team.balance_available
    amount_applied = 0
    enables_e_card = False
    effect_mode = data.effect_type or "percentage"
    msg = ""

    if effect_mode == "otros":
        if not data.other_description or not data.other_description.strip():
            raise HTTPException(status_code=400, detail="Debe ingresar una descripción obligatoria para el efecto 'Otros'.")
        
        desc = data.other_description.strip()
        outcome = "Acierto" if data.is_correct else "Error"
        reason = f"Efecto especial {instance.card_code} ({outcome}): {desc}"

        await EffectsEngine.create_transfer_entry(
            session=db,
            game_id=game.id,
            source=team,
            destination=team,
            amount=0,
            operation_type="efecto_otros",
            reason=reason,
            actor_id=admin_user.id,
            approver_id=admin_user.id,
            state_snapshot={"card_code": instance.card_code, "effect": desc, "is_correct": data.is_correct}
        )
        msg = f"Efecto especial registrado ({outcome}): {desc}"

    elif effect_mode == "fixed":
        if data.is_correct:
            gain_cents = int(round((data.gain_amount_tdl if data.gain_amount_tdl is not None else 3000) * 100))
            amount_applied = gain_cents
            if gain_cents > 0:
                await EffectsEngine.create_transfer_entry(
                    session=db,
                    game_id=game.id,
                    source=bank,
                    destination=team,
                    amount=gain_cents,
                    operation_type="premio_pregunta",
                    reason=f"Premio acierto {instance.card_code} (+{gain_cents / 100:.2f} TDL)",
                    actor_id=admin_user.id,
                    approver_id=admin_user.id,
                    state_snapshot={"card_code": instance.card_code, "fixed_gain": gain_cents}
                )
            msg = f"Respuesta correcta: premio fijo de +{gain_cents / 100:.2f} TDL acreditado."
        else:
            loss_cents = int(round((data.loss_amount_tdl if data.loss_amount_tdl is not None else 1500) * 100))
            amount_applied = loss_cents
            if loss_cents > 0:
                loss_to_debit = min(team.balance_available, loss_cents)
                await EffectsEngine.create_transfer_entry(
                    session=db,
                    game_id=game.id,
                    source=team,
                    destination=bank,
                    amount=loss_to_debit,
                    operation_type="descuento_pregunta",
                    reason=f"Descuento error {instance.card_code} (-{loss_cents / 100:.2f} TDL)",
                    actor_id=admin_user.id,
                    approver_id=admin_user.id,
                    state_snapshot={"card_code": instance.card_code, "fixed_loss": loss_cents}
                )
            msg = f"Respuesta incorrecta: descuento fijo de -{loss_cents / 100:.2f} TDL aplicado."

    else:  # percentage
        if data.gain_pct is not None and data.loss_pct is not None:
            gain_pct = data.gain_pct / 100.0
            loss_pct = data.loss_pct / 100.0
        elif data.variant_id == "var_50_30":
            gain_pct, loss_pct = 0.50, 0.30
        elif data.variant_id == "var_30_35":
            gain_pct, loss_pct = 0.30, 0.35
        elif data.variant_id == "casilla_2_reto":
            gain_pct, loss_pct = 0.0, 0.25
            if data.is_correct:
                enables_e_card = True
        else:
            gain_pct, loss_pct = 1.0, 0.60

        if data.is_correct:
            if enables_e_card:
                msg = "Respuesta correcta: se habilita tarjeta de Reto Económico (E)."
            else:
                amount_applied = compute_pct(base_b, gain_pct)
                await EffectsEngine.create_transfer_entry(
                    session=db,
                    game_id=game.id,
                    source=bank,
                    destination=team,
                    amount=amount_applied,
                    operation_type="premio_pregunta",
                    reason=f"Premio acierto {instance.card_code} (+{int(gain_pct*100)}% disponible)",
                    actor_id=admin_user.id,
                    approver_id=admin_user.id,
                    state_snapshot={"card_code": instance.card_code, "base": base_b}
                )
                msg = f"Respuesta correcta: premio de +{amount_applied/100:.2f} TDL acreditado."
        else:
            amount_applied = compute_pct(base_b, loss_pct)
            await EffectsEngine.create_transfer_entry(
                session=db,
                game_id=game.id,
                source=team,
                destination=bank,
                amount=amount_applied,
                operation_type="descuento_pregunta",
                reason=f"Descuento error {instance.card_code} (-{int(loss_pct*100)}% disponible)",
                actor_id=admin_user.id,
                approver_id=admin_user.id,
                state_snapshot={"card_code": instance.card_code, "base": base_b}
            )
            msg = f"Respuesta incorrecta: descuento de -{amount_applied/100:.2f} TDL aplicado."

    instance.status = "resuelta_usada"
    instance.resolved_at = datetime.utcnow()
    instance.execution_result = {
        "is_correct": data.is_correct,
        "effect_type": effect_mode,
        "amount_applied": amount_applied,
        "enables_e_card": enables_e_card,
        "other_description": data.other_description if effect_mode == "otros" else None
    }
    await db.commit()

    await manager.broadcast(game.code, "CARD_RESOLVED", {
        "instance_id": instance.id,
        "card_code": instance.card_code,
        "is_correct": data.is_correct,
        "message": msg,
        "enables_e_card": enables_e_card,
        "team_name": team.account_name
    })

    return {
        "status": "resuelta",
        "is_correct": data.is_correct,
        "amount_applied": amount_applied,
        "enables_e_card": enables_e_card,
        "message": msg
    }

@router.post("/execute-e")
async def execute_e_card(
    data: CardExecuteERequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ejecución del efecto exacto de una tarjeta de reto económico E01-E15.
    Aplica las reglas del motor y genera los asientos/contratos pertinentes.
    """
    inst_res = await db.execute(select(CardInstance).where(CardInstance.id == data.instance_id))
    instance = inst_res.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail="Instancia de tarjeta no encontrada.")
    if instance.status == "resuelta_usada":
        raise HTTPException(status_code=400, detail="Esta tarjeta ya fue resuelta y ejecutada.")

    team_res = await db.execute(select(Account).where(Account.id == instance.assigned_to_account_id))
    team = team_res.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=400, detail="Tarjeta sin equipo asignado.")

    game_res = await db.execute(select(Game).where(Game.id == team.game_id))
    game = game_res.scalar_one()

    if game.status == "finalizada":
        raise HTTPException(status_code=400, detail="La partida está finalizada y el tablero se encuentra fijado.")

    code = instance.card_code
    result = {}

    try:
        if code == "E01":
            result = await EffectsEngine.apply_e01(db, game, team, admin_user.id)
        elif code == "E02":
            if not data.target_account_id:
                raise HTTPException(status_code=400, detail="E02 requiere seleccionar un equipo deudor.")
            d_res = await db.execute(select(Account).where(Account.id == data.target_account_id))
            debtor = d_res.scalar_one_or_none()
            result = await EffectsEngine.apply_e02(db, game, team, debtor, admin_user.id)
        elif code == "E03":
            result = await EffectsEngine.apply_e03(db, game, team, admin_user.id)
        elif code == "E04":
            dice = tuple(data.dice_rolls) if data.dice_rolls and len(data.dice_rolls) == 3 else (4, 4, 4)
            result = await EffectsEngine.apply_e04(db, game, team, dice, admin_user.id)
        elif code == "E05":
            result = await EffectsEngine.apply_e05(db, game, team, admin_user.id)
        elif code == "E06":
            result = await EffectsEngine.apply_e06(db, game, team, admin_user.id)
        elif code == "E07":
            result = await EffectsEngine.apply_e07(db, game, team, admin_user.id)
        elif code == "E08":
            result = await EffectsEngine.apply_e08(db, game, team, admin_user.id)
        elif code == "E09":
            if not data.target_account_id:
                raise HTTPException(status_code=400, detail="E09 requiere seleccionar otro equipo para el intercambio.")
            b_res = await db.execute(select(Account).where(Account.id == data.target_account_id))
            team_b = b_res.scalar_one_or_none()
            result = await EffectsEngine.apply_e09(db, game, team, team_b, admin_user.id)
        elif code == "E10":
            result = await EffectsEngine.apply_e10(db, game, team, admin_user.id)
        elif code == "E11":
            accept = data.accept_insurance if data.accept_insurance is not None else True
            result = await EffectsEngine.apply_e11(db, game, team, accept, admin_user.id)
        elif code == "E12":
            if not data.target_account_id:
                raise HTTPException(status_code=400, detail="E12 requiere seleccionar un equipo receptor.")
            r_res = await db.execute(select(Account).where(Account.id == data.target_account_id))
            receiver = r_res.scalar_one_or_none()
            result = await EffectsEngine.apply_e12(db, game, team, receiver, admin_user.id)
        elif code == "E13":
            result = await EffectsEngine.apply_e13(db, game, team, admin_user.id)
        elif code == "E14":
            result = await EffectsEngine.apply_e14(db, game, team, admin_user.id)
        elif code == "E15":
            die = data.dice_rolls[0] if data.dice_rolls and len(data.dice_rolls) > 0 else 4
            result = await EffectsEngine.apply_e15(db, game, team, die, admin_user.id)
        else:
            raise HTTPException(status_code=400, detail=f"Código de reto desconocido: {code}")

        instance.status = "resuelta_usada"
        instance.resolved_at = datetime.utcnow()
        instance.execution_result = result
        await db.commit()

        await manager.broadcast(game.code, "CARD_RESOLVED", {
            "instance_id": instance.id,
            "card_code": code,
            "result": result,
            "team_name": team.account_name
        })

        return {"status": "ejecutada", "card_code": code, "result": result}

    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset/{game_code}")
async def reset_decks(
    game_code: str,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reinicia los dos mazos para la partida, volviendo a poner las tarjetas en disponible.
    No altera contratos u obligaciones financieras vigentes.
    """
    g_res = await db.execute(select(Game).where(Game.code == game_code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    res = await db.execute(select(CardInstance).where(CardInstance.game_id == game.id))
    instances = res.scalars().all()
    for inst in instances:
        inst.status = "disponible"
        inst.assigned_to_account_id = None
        inst.assigned_at = None

    await db.commit()
    await manager.broadcast(game.code, "DECKS_RESET", {"message": "Los dos mazos fueron reiniciados."})
    return {"message": "Mazos reiniciados con éxito."}

@router.post("/set-status/{game_code}")
async def set_card_status(
    game_code: str,
    data: CardStatusUpdateRequest,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Permite al docente marcar manualmente una tarjeta como disponible o no disponible (resuelta/usada).
    """
    g_res = await db.execute(select(Game).where(Game.code == game_code.upper().strip()))
    game = g_res.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Partida no encontrada.")

    query = select(CardInstance).where(
        CardInstance.game_id == game.id,
        CardInstance.card_code == data.card_code.upper().strip()
    )
    res = await db.execute(query)
    instance = res.scalars().first()
    if not instance:
        raise HTTPException(status_code=404, detail="Tarjeta no encontrada en esta partida.")

    instance.status = data.status
    if data.status == "resuelta_usada":
        instance.resolved_at = datetime.utcnow()
    else:
        instance.resolved_at = None
        instance.assigned_to_account_id = None
        instance.assigned_at = None

    await db.commit()

    action_label = "NO DISPONIBLE" if data.status == "resuelta_usada" else "DISPONIBLE"
    await manager.broadcast(game.code, "CARD_STATUS_CHANGED", {
        "card_code": instance.card_code,
        "status": instance.status,
        "message": f"Tarjeta {instance.card_code} marcada como {action_label} por el docente."
    })

    return {
        "card_code": instance.card_code,
        "status": instance.status,
        "message": f"Tarjeta {instance.card_code} actualizada a {action_label}."
    }

