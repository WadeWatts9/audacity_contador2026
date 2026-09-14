import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.card import Card, CardInstance
from app.models.user import User
from app.routers.cards import get_deck_status, set_card_status
from app.schemas.card import CardStatusUpdateRequest

@pytest.mark.asyncio
async def test_card_visibility_and_status_update(db_session: AsyncSession, sample_game):
    game = sample_game["game"]
    admin = sample_game["admin"]
    team_user = User(
        username="team_test",
        password_hash="test",
        role="equipo",
        display_name="Contador Test"
    )
    db_session.add(team_user)
    await db_session.flush()

    # Create 1 P card and 1 E card
    card_p = Card(
        code="P01",
        deck_type="P",
        title="Pregunta Costo Oportunidad",
        text="¿Qué es el costo de oportunidad?",
        image_path="/cards/P01.png"
    )
    card_e = Card(
        code="E01",
        deck_type="E",
        title="Reto Inversión a Futuro",
        text="Inversión que produce un 15% de beneficio.",
        image_path="/cards/E01.png"
    )
    db_session.add_all([card_p, card_e])
    await db_session.flush()

    inst_p = CardInstance(game_id=game.id, card_code="P01", status="disponible")
    inst_e = CardInstance(game_id=game.id, card_code="E01", status="disponible")
    db_session.add_all([inst_p, inst_e])
    await db_session.commit()

    # 1. Non-admin calls get_deck_status when available -> text should be protected
    res_non_admin = await get_deck_status(game.code, current_user=team_user, db=db_session)
    p_card = res_non_admin["p_deck"][0]
    e_card = res_non_admin["e_deck"][0]

    assert p_card["status"] == "disponible"
    assert "protegida" in p_card["text"].lower()
    assert e_card["status"] == "disponible"
    assert "protegido" in e_card["text"].lower()

    # 2. Admin calls get_deck_status when available -> full text visible
    res_admin = await get_deck_status(game.code, current_user=admin, db=db_session)
    assert res_admin["p_deck"][0]["text"] == "¿Qué es el costo de oportunidad?"
    assert res_admin["e_deck"][0]["text"] == "Inversión que produce un 15% de beneficio."

    # 3. Admin marks E01 and P01 as resuelta_usada (NO DISPONIBLE)
    await set_card_status(game.code, CardStatusUpdateRequest(card_code="E01", status="resuelta_usada"), admin_user=admin, db=db_session)
    await set_card_status(game.code, CardStatusUpdateRequest(card_code="P01", status="resuelta_usada"), admin_user=admin, db=db_session)

    # 4. Non-admin calls get_deck_status -> since they are now resuelta_usada (no disponibles), real text is revealed
    res_after = await get_deck_status(game.code, current_user=team_user, db=db_session)
    p_used = res_after["p_deck"][0]
    e_used = res_after["e_deck"][0]

    assert p_used["status"] == "resuelta_usada"
    assert p_used["text"] == "¿Qué es el costo de oportunidad?"
    assert e_used["status"] == "resuelta_usada"
    assert e_used["text"] == "Inversión que produce un 15% de beneficio."

    # 5. Admin reactivates E01 back to disponible
    await set_card_status(game.code, CardStatusUpdateRequest(card_code="E01", status="disponible"), admin_user=admin, db=db_session)

    res_reactivated = await get_deck_status(game.code, current_user=team_user, db=db_session)
    e_reactivated = res_reactivated["e_deck"][0]
    assert e_reactivated["status"] == "disponible"
    assert "protegido" in e_reactivated["text"].lower()
