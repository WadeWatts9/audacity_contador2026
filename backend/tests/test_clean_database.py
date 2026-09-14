import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.game import Game
from app.models.account import Account
from app.models.ledger import LedgerEntry
from app.models.contract import Contract
from app.routers.games import clean_database

@pytest.mark.asyncio
async def test_clean_database(db_session: AsyncSession, sample_game: dict):
    # sample_game has admin, bank, team_a, team_b, game
    admin = sample_game["admin"]
    game = sample_game["game"]
    team_a = sample_game["team_a"]

    # Verify initial data exists
    games_count = (await db_session.execute(select(Game))).scalars().all()
    assert len(games_count) >= 1

    accounts_count = (await db_session.execute(select(Account))).scalars().all()
    assert len(accounts_count) >= 3

    users_count = (await db_session.execute(select(User))).scalars().all()
    assert len(users_count) >= 3

    # Add a ledger entry and a contract to verify they get deleted
    entry = LedgerEntry(
        transaction_id="tx_test_clean_1",
        game_id=game.id,
        source_account_id=team_a.id,
        destination_account_id=sample_game["bank"].id,
        amount=1000,
        operation_type="pago",
        reason="Prueba para limpiar base de datos"
    )
    db_session.add(entry)

    contract = Contract(
        game_id=game.id,
        contract_type="préstamo",
        description="Préstamo de prueba",
        creditor_account_id=sample_game["bank"].id,
        debtor_account_id=team_a.id,
        principal_amount=5000,
        created_at_opportunity=1
    )
    db_session.add(contract)
    await db_session.commit()

    # Execute clean_database as admin
    result = await clean_database(admin_user=admin, db=db_session)
    assert result["status"] == "success"

    # Verify everything was wiped except admin_docente
    games_after = (await db_session.execute(select(Game))).scalars().all()
    assert len(games_after) == 0

    accounts_after = (await db_session.execute(select(Account))).scalars().all()
    assert len(accounts_after) == 0

    ledger_after = (await db_session.execute(select(LedgerEntry))).scalars().all()
    assert len(ledger_after) == 0

    contracts_after = (await db_session.execute(select(Contract))).scalars().all()
    assert len(contracts_after) == 0

    # Only admin_docente user remains
    users_after = (await db_session.execute(select(User))).scalars().all()
    assert len(users_after) == 1
    assert users_after[0].username == "admin_docente"
    assert users_after[0].role == "admin_docente"
