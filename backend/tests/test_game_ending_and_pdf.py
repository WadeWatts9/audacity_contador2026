import pytest
from datetime import datetime, timezone
from app.engine.pdf_report import generate_game_audit_pdf

def test_pdf_generation_basic():
    now = datetime.now(timezone.utc)
    pdf_bytes = generate_game_audit_pdf(
        game_code="TEST-001",
        game_name="Partida de Prueba",
        game_profile="genially",
        game_status="finalizada",
        created_at=now,
        finalized_at=now,
        bank_balance_tdl=100000.0,
        ranked_teams=[
            {
                'position': 1,
                'name': 'Gallo',
                'symbol': '🐓',
                'balance_tdl': 1500.0,
                'reserved_tdl': 0.0,
                'total_tdl': 1500.0,
                'status': 'Activo'
            },
            {
                'position': 2,
                'name': 'León',
                'symbol': '🦁',
                'balance_tdl': 800.0,
                'reserved_tdl': 0.0,
                'total_tdl': 800.0,
                'status': 'Activo'
            }
        ],
        ledger_entries=[
            {
                'id': 1,
                'created_at': now,
                'source': 'Banco Central',
                'target': 'Gallo',
                'operation_type': 'acierto_pregunta_otros',
                'amount_tdl': 0.0,
                'description': 'Premio especial por creatividad'
            },
            {
                'id': 2,
                'created_at': now,
                'source': 'Banco Central',
                'target': 'León',
                'operation_type': 'acierto_pregunta_fijo',
                'amount_tdl': 3000.0,
                'description': 'Acierto tarjeta P01 (+3.000 TDL)'
            }
        ],
        contracts=[]
    )
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")


def test_pdf_generation_full_emojis_and_long_text():
    now = datetime.now(timezone.utc)
    symbols = [
        ("🐓", "Contador Gallo"),
        ("🦁", "Contador León"),
        ("🐕", "Contador Perro"),
        ("✋", "Contador Mano"),
        ("★", "Contador Estrella"),
        ("💎", "Contador Diamante"),
        ("🚗", "Contador Auto"),
        ("🎩", "Contador Sombrero"),
        ("🐷", "Contador Cerdo"),
    ]
    ranked = []
    for idx, (sym, name) in enumerate(symbols, 1):
        ranked.append({
            "rank": idx,
            "team_name": name,
            "token_symbol": sym,
            "balance_available": 1000000 - idx * 50000,
            "balance_reserved": 20000,
            "balance_total": 1020000 - idx * 50000,
            "pending_debts": 50000 if idx % 2 == 0 else 0
        })

    long_reason = "Efecto personalizado muy extenso con caracteres especiales como < & > y fórmulas económicas complejas que anteriormente desbordaban los límites de la celda de la tabla provocando textos superpuestos en las columnas contiguas."
    
    entries = [
        {
            "id": 101,
            "timestamp": "14:32:05",
            "operation_type": "transferencia_entre_equipos_autorizada",
            "amount": 250000,
            "source_name": "Contador Diamante Con Nombre Muy Largo",
            "destination_name": "Contador Sombrero Con Destino Gigante",
            "reason": long_reason,
            "is_reverted": False
        },
        {
            "id": 102,
            "timestamp": "14:35:12",
            "operation_type": "ajuste_manual_docente",
            "amount": 50000,
            "source_name": "Banco Central del Uruguay",
            "destination_name": "Contador Cerdo",
            "reason": "Resolución de seguro por quiebra técnica <urgente>",
            "is_reverted": True
        }
    ]

    contracts = [
        {
            "id": 1,
            "contract_type": "préstamo_emergencia",
            "creditor_name": "Banco Central",
            "debtor_name": "Contador Diamante",
            "principal_amount": 500000,
            "total_repaid": 200000,
            "status": "activo"
        }
    ]

    pdf_bytes = generate_game_audit_pdf(
        game_code="FULL-EMOJI",
        game_name="Partida Completa con Emojis y Textos Largos",
        game_profile="genially",
        game_status="finalizada",
        created_at=now,
        finalized_at=now,
        bank_balance_tdl=85000.0,
        ranked_teams=ranked,
        ledger_entries=entries,
        contracts=contracts,
        timezone_name="America/Montevideo"
    )

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")
