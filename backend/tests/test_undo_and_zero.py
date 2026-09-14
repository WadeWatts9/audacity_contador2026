import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.engine.effects_engine import EffectsEngine
from app.engine.undo_manager import UndoManager
from app.models.ledger import LedgerEntry

@pytest.mark.asyncio
async def test_undo_transfer(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]  # 1.000 TDL (100.000 cents)
    team_b = sample_game["team_b"]  # 600 TDL (60.000 cents)
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Transferencia de 200 TDL (20.000 cents) de A a B
    entry = await EffectsEngine.create_transfer_entry(
        session=db_session,
        game_id=game.id,
        source=team_a,
        destination=team_b,
        amount=20000,
        operation_type="transferencia",
        reason="Transferencia de prueba",
        actor_id=team_a.user_id,
        approver_id=admin.id
    )
    assert team_a.balance_available == 80000
    assert team_b.balance_available == 80000

    # Deshacer (Undo)
    undo_res = await UndoManager.revert_entry(db_session, entry.id, admin.id)
    assert undo_res["amount_reverted"] == 20000
    assert team_a.balance_available == 100000
    assert team_b.balance_available == 60000

    # Verificar que no se puede deshacer dos veces
    with pytest.raises(ValueError, match="ya fue revertida"):
        await UndoManager.revert_entry(db_session, entry.id, admin.id)

@pytest.mark.asyncio
async def test_undo_insurance_consumed(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Activar seguro E11
    await EffectsEngine.apply_e11(db_session, game, team_a, True, admin.id)
    assert team_a.has_insurance_e11 is True

    # Consumir seguro por E08
    await EffectsEngine.apply_e08(db_session, game, team_a, admin.id)
    assert team_a.has_insurance_e11 is False

    # Buscar asiento donde se consumió el seguro
    res = await db_session.execute(
        select(LedgerEntry).where(LedgerEntry.operation_type == "seguro_consumido_e08")
    )
    entry = res.scalar_one()

    # Deshacer el consumo del seguro
    await UndoManager.revert_entry(db_session, entry.id, admin.id)
    assert team_a.has_insurance_e11 is True  # Seguro restaurado
