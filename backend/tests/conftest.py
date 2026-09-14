import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base
from app.models.user import User
from app.models.game import Game
from app.models.account import Account
from app.models.card import Card, CardInstance
from app.security import hash_password

# Use an in-memory SQLite database for unit tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def sample_game(db_session: AsyncSession):
    """Crea una partida de prueba con un docente, el banco y dos equipos (A y B)."""
    admin = User(
        username="admin_docente",
        password_hash=hash_password("admin_pass_1234"),
        role="admin_docente",
        display_name="Docente / Banco"
    )
    db_session.add(admin)
    await db_session.flush()

    game = Game(
        code="TEST-001",
        name="Partida de Prueba",
        profile="genially",
        status="activa",
        initial_team_balance=100000,  # 1.000 TDL = 100.000 centésimos
        initial_bank_balance=10000000  # 100.000 TDL = 10.000.000 centésimos
    )
    db_session.add(game)
    await db_session.flush()

    # Banco
    bank = Account(
        game_id=game.id,
        user_id=admin.id,
        account_type="banco",
        account_name="BANCO CENTRAL",
        balance_available=10000000,
        balance_reserved=0
    )
    db_session.add(bank)

    # Equipo A (1.000 TDL = 100.000 cents)
    user_a = User(
        username="equipo_a",
        password_hash=hash_password("password_a_1234"),
        role="equipo",
        display_name="Equipo A",
        token_symbol="🐓",
        token_color="#9ed7ef"
    )
    db_session.add(user_a)
    await db_session.flush()

    team_a = Account(
        game_id=game.id,
        user_id=user_a.id,
        account_type="equipo",
        account_name="Equipo A",
        balance_available=100000,
        balance_reserved=0
    )
    db_session.add(team_a)

    # Equipo B (600 TDL = 60.000 cents)
    user_b = User(
        username="equipo_b",
        password_hash=hash_password("password_b_1234"),
        role="equipo",
        display_name="Equipo B",
        token_symbol="🦁",
        token_color="#f6d662"
    )
    db_session.add(user_b)
    await db_session.flush()

    team_b = Account(
        game_id=game.id,
        user_id=user_b.id,
        account_type="equipo",
        account_name="Equipo B",
        balance_available=60000,
        balance_reserved=0
    )
    db_session.add(team_b)

    game.turn_order = [team_a.id, team_b.id]
    await db_session.commit()

    return {
        "admin": admin,
        "game": game,
        "bank": bank,
        "team_a": team_a,
        "team_b": team_b
    }
