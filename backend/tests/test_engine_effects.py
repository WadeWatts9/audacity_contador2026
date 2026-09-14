import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.engine.effects_engine import EffectsEngine
from app.engine.turn_processor import TurnProcessor

@pytest.mark.asyncio
async def test_e01_inversion_futuro(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Base: 1.000 TDL (100.000 cents)
    res = await EffectsEngine.apply_e01(db_session, game, team_a, admin.id)
    assert res["card"] == "E01"
    assert res["bonus_expected"] == 15000  # 150 TDL
    assert res["lost_turns"] == 2
    assert team_a.lost_turns == 2

@pytest.mark.asyncio
async def test_e02_prestamo_interequipos(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]  # 1.000 TDL (100.000 cents)
    team_b = sample_game["team_b"]  # 600 TDL (60.000 cents)
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Desembolso: 40% de 1.000 = 400 TDL (40.000 cents)
    res = await EffectsEngine.apply_e02(db_session, game, team_a, team_b, admin.id)
    assert res["principal"] == 40000
    assert team_a.balance_available == 60000  # 600 TDL
    assert team_b.balance_available == 100000 # 1.000 TDL (600 + 400)

    # Simular 3 turnos del deudor B y cobrar cuotas
    # Cuota 1: 20% de 1.000 TDL = 200 TDL. B queda en 800 TDL. A queda en 800 TDL.
    res1 = await TurnProcessor.process_turn_start(db_session, game, team_b, admin.id)
    assert team_b.balance_available == 80000
    assert team_a.balance_available == 80000

    # Cuota 2: 20% de 800 TDL = 160 TDL. B queda en 640 TDL. A queda en 960 TDL.
    res2 = await TurnProcessor.process_turn_start(db_session, game, team_b, admin.id)
    assert team_b.balance_available == 64000
    assert team_a.balance_available == 96000

    # Cuota 3: 20% de 640 TDL = 128 TDL. B queda en 512 TDL. A queda en 1.088 TDL.
    res3 = await TurnProcessor.process_turn_start(db_session, game, team_b, admin.id)
    assert team_b.balance_available == 51200
    assert team_a.balance_available == 108800

@pytest.mark.asyncio
async def test_e03_inflacion(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Base: 1.000 TDL -> Paga 10% (100 TDL) al banco
    res = await EffectsEngine.apply_e03(db_session, game, team_a, admin.id)
    assert res["paid"] == 10000
    assert team_a.balance_available == 90000

@pytest.mark.asyncio
async def test_e04_tres_dados(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Caso suma <= 6 (ej. 2, 2, 2 = 6): pierde 20% (200 TDL) -> queda en 800 TDL
    res_loss = await EffectsEngine.apply_e04(db_session, game, team_a, (2, 2, 2), admin.id)
    assert res_loss["outcome"] == "perdida_20"
    assert team_a.balance_available == 80000

    # Caso suma > 6 (ej. 3, 3, 1 = 7) sobre base 800: gana 30% (240 TDL) -> queda en 1.040 TDL
    res_gain = await EffectsEngine.apply_e04(db_session, game, team_a, (3, 3, 1), admin.id)
    assert res_gain["outcome"] == "ganancia_30"
    assert team_a.balance_available == 104000

@pytest.mark.asyncio
async def test_e05_ahorro_programado(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]  # 1.000 TDL
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Reserva 30% (300 TDL) -> disponible 700, reservado 300, total 1.000
    res = await EffectsEngine.apply_e05(db_session, game, team_a, admin.id)
    assert res["reserved"] == 30000
    assert team_a.balance_available == 70000
    assert team_a.balance_reserved == 30000
    assert team_a.balance_total == 100000

    # Al inicio del siguiente turno, se libera principal y banco paga 20% interés (60 TDL)
    # Total final = 1.060 TDL (106.000 cents)
    await TurnProcessor.process_turn_start(db_session, game, team_a, admin.id)
    assert team_a.balance_available == 106000
    assert team_a.balance_reserved == 0
    assert team_a.balance_total == 106000

@pytest.mark.asyncio
async def test_e06_tributaria(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Paga 12% de 1.000 = 120 TDL -> queda en 880 TDL
    res = await EffectsEngine.apply_e06(db_session, game, team_a, admin.id)
    assert res["paid"] == 12000
    assert team_a.balance_available == 88000

@pytest.mark.asyncio
async def test_e07_apoyo_emprendimiento(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Banco paga 25% de 1.000 = 250 TDL -> queda en 1.250 TDL
    res = await EffectsEngine.apply_e07(db_session, game, team_a, admin.id)
    assert res["received"] == 25000
    assert team_a.balance_available == 125000

@pytest.mark.asyncio
async def test_e08_reparacion_urgente_con_y_sin_seguro(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]  # 1.000 TDL
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Sin seguro: paga 15% (150 TDL) -> queda en 850 TDL
    res = await EffectsEngine.apply_e08(db_session, game, team_a, admin.id)
    assert res["insurance_used"] is False
    assert res["paid"] == 15000
    assert team_a.balance_available == 85000

    # Ahora contratamos seguro E11: paga 5% de 850 = 42,50 TDL -> redondeo half-up: 42,50 = 4250 cents
    # Saldo disponible = 850 - 42,50 = 807,50 TDL (80750 cents)
    res_ins = await EffectsEngine.apply_e11(db_session, game, team_a, True, admin.id)
    assert team_a.has_insurance_e11 is True
    avail_after_ins = team_a.balance_available

    # Siguiente E08: el seguro SE CONSUME y evita la pérdida
    res_e08_shielded = await EffectsEngine.apply_e08(db_session, game, team_a, admin.id)
    assert res_e08_shielded["insurance_used"] is True
    assert res_e08_shielded["paid"] == 0
    assert team_a.has_insurance_e11 is False
    assert team_a.balance_available == avail_after_ins

@pytest.mark.asyncio
async def test_e09_intercambio_comercial(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]  # 1.000 TDL (100.000 cents)
    team_b = sample_game["team_b"]  # 600 TDL (60.000 cents)
    game = sample_game["game"]
    admin = sample_game["admin"]

    # A entrega 10% (100 TDL) y recibe 10% de B (60 TDL) -> A final = 960 TDL (96.000 cents)
    # B entrega 10% (60 TDL) y recibe 10% de A (100 TDL) -> B final = 640 TDL (64.000 cents)
    res = await EffectsEngine.apply_e09(db_session, game, team_a, team_b, admin.id)
    assert team_a.balance_available == 96000
    assert team_b.balance_available == 64000

@pytest.mark.asyncio
async def test_e10_campana_ventas(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]  # 1.000 TDL
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Paga 5% (50 TDL), quedan 950 TDL. Cobras 20% de 950 = 190 TDL. Final = 1.140 TDL (114.000 cents).
    res = await EffectsEngine.apply_e10(db_session, game, team_a, admin.id)
    assert res["cost"] == 5000
    assert res["gain"] == 19000
    assert team_a.balance_available == 114000

@pytest.mark.asyncio
async def test_e13_fraude_comercial_con_seguro(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]  # 1.000 TDL
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Activar seguro E11
    await EffectsEngine.apply_e11(db_session, game, team_a, True, admin.id)
    bal_before = team_a.balance_available
    assert team_a.has_insurance_e11 is True

    # Fraude E13 con seguro: evita la pérdida y consume póliza
    res = await EffectsEngine.apply_e13(db_session, game, team_a, admin.id)
    assert res["insurance_used"] is True
    assert team_a.has_insurance_e11 is False
    assert team_a.balance_available == bal_before

    # Siguiente Fraude E13 ya sin seguro: pierde 20%
    res2 = await EffectsEngine.apply_e13(db_session, game, team_a, admin.id)
    assert res2["insurance_used"] is False
    assert res2["paid"] > 0

@pytest.mark.asyncio
async def test_e14_credito_banco(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]  # 1.000 TDL
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Desembolso: 30% de 1.000 = 300 TDL. Saldo disponible pasa a 1.300 TDL.
    # Deuda fija pactada = 300 + 10% (30) = 330 TDL (33.000 cents) en n+2.
    res = await EffectsEngine.apply_e14(db_session, game, team_a, admin.id)
    assert res["disbursed"] == 30000
    assert res["repayment_due"] == 33000
    assert team_a.balance_available == 130000

    # Turno n+1: aún no vence
    await TurnProcessor.process_turn_start(db_session, game, team_a, admin.id)
    assert team_a.balance_available == 130000

    # Turno n+2: vence cuota fija de 330 TDL.
    # Saldo final = 1.300 - 330 = 970 TDL (97.000 cents)
    await TurnProcessor.process_turn_start(db_session, game, team_a, admin.id)
    assert team_a.balance_available == 97000

@pytest.mark.asyncio
async def test_e15_demanda_cambiante(db_session: AsyncSession, sample_game: dict):
    team_a = sample_game["team_a"]  # 1.000 TDL
    game = sample_game["game"]
    admin = sample_game["admin"]

    # Dado par (4): +20% (200 TDL) -> 1.200 TDL (120.000 cents)
    res_even = await EffectsEngine.apply_e15(db_session, game, team_a, 4, admin.id)
    assert res_even["outcome"] == "par_ganancia_20"
    assert team_a.balance_available == 120000

    # Dado impar (3) sobre base 1.200: -10% (120 TDL) -> 1.080 TDL (108.000 cents)
    res_odd = await EffectsEngine.apply_e15(db_session, game, team_a, 3, admin.id)
    assert res_odd["outcome"] == "impar_perdida_10"
    assert team_a.balance_available == 108000
