import pytest
from datetime import datetime
from app.engine.pdf_report import generate_game_audit_pdf

def test_pdf_generation_basic():
    pdf_bytes = generate_game_audit_pdf(
        game_code="TEST-001",
        game_name="Partida de Prueba",
        game_profile="genially",
        game_status="finalizada",
        created_at=datetime.utcnow(),
        finalized_at=datetime.utcnow(),
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
                'created_at': datetime.utcnow(),
                'source': 'Banco Central',
                'target': 'Gallo',
                'operation_type': 'acierto_pregunta_otros',
                'amount_tdl': 0.0,
                'description': 'Premio especial por creatividad'
            },
            {
                'id': 2,
                'created_at': datetime.utcnow(),
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
