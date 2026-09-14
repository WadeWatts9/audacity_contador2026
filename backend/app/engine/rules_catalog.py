"""
Catálogo de casillas y variantes verificadas del tablero (Genially y Prezi).
"""

BOARD_SQUARES = [
    {
        "id": 1,
        "name": "Pregunta",
        "description": "Elegir variante de pregunta (P01-P15) y aplicar premio o descuento según resultado.",
        "requires_card": True,
        "card_type": "P",
        "variants": [
            {"id": "var_100_60", "label": "+100% acierto / -60% error", "gain_pct": 1.0, "loss_pct": 0.60},
            {"id": "var_50_30", "label": "+50% acierto / -30% error", "gain_pct": 0.50, "loss_pct": 0.30},
            {"id": "var_30_35", "label": "+30% acierto / -35% error", "gain_pct": 0.30, "loss_pct": 0.35},
            {"id": "var_fixed", "label": "+3.000 TDL acierto / -1.500 TDL error", "gain_fixed": 300000, "loss_fixed": 150000},
            {"id": "var_prezi", "label": "+300 TDL acierto / -150 TDL error (Prezi)", "gain_fixed": 30000, "loss_fixed": 15000}
        ]
    },
    {
        "id": 2,
        "name": "Responde: acierto reto / error -25%",
        "description": "Si acierta, habilita reto económico (E) en el mismo turno sin premio monetario directo; si falla, descuenta 25% al Banco.",
        "requires_card": True,
        "card_type": "P",
        "loss_pct": 0.25,
        "enables_e_on_correct": True
    },
    {
        "id": 3,
        "name": "Elige un reto",
        "description": "Seleccionar una tarjeta E01-E15 disponible y aplicar su efecto.",
        "requires_card": True,
        "card_type": "E"
    },
    {
        "id": 4,
        "name": "Pagas con crédito, pierdes el 15% al Banco",
        "description": "Transferir el 15% del saldo base propio al Banco. (Variante Prezi: 5% y lanzamiento extra).",
        "loss_pct_default": 0.15,
        "loss_pct_prezi": 0.05
    },
    {
        "id": 5,
        "name": "Pierde la mitad",
        "description": "Transferir el 50% del saldo base al Banco.",
        "loss_pct": 0.50
    },
    {
        "id": 6,
        "name": "Pierde un turno, gana 35%",
        "description": "Acredita 35% del saldo desde el Banco y marca un turno perdido. (Variante Prezi: gana 5%).",
        "gain_pct_default": 0.35,
        "gain_pct_prezi": 0.05,
        "lost_turns": 1
    },
    {
        "id": 7,
        "name": "Ahorras tu 50%, un turno con la mitad",
        "description": "Mueve 50% de disponible a reservado. Se libera al inicio del próximo turno de este equipo.",
        "reserve_pct": 0.50,
        "duration_turns": 1
    },
    {
        "id": 8,
        "name": "Plazo fijo por un turno, ganas +25%",
        "description": "El docente fija el capital invertido (propuesta 50% del disponible). Se reserva durante 1 turno y al inicio del próximo turno se devuelve el principal más un 25% de interés pagado por el Banco.",
        "interest_pct": 0.25,
        "duration_turns": 1
    },
    {
        "id": 9,
        "name": "Ganas el 15% del menor saldo. Vuelve a lanzar",
        "description": "El Banco paga el 15% del menor saldo base disponible entre los otros equipos activos. Otorga un lanzamiento extra.",
        "pct_lowest_rival": 0.15,
        "extra_roll": True
    },
    {
        "id": 10,
        "name": "Si el banco está vacío transfiere 15%, sino cobra 15%",
        "description": "Si el Banco tiene saldo 0, el equipo le transfiere 15% de su disponible. Si el Banco tiene saldo positivo, el Banco le paga 15% al equipo.",
        "pct": 0.15
    },
    {
        "id": 11,
        "name": "Duplica tu saldo, divide el saldo de otro equipo",
        "description": "Duplica el disponible del jugador y divide el disponible de un equipo rival entre el divisor configurado (por defecto 2). Las diferencias netas se liquidan con el Banco en una sola transacción atómica.",
        "divisor_default": 2
    },
    {
        "id": 12,
        "name": "Cambia los saldos de los adversarios",
        "description": "Intercambia los saldos disponibles de dos equipos rivales seleccionados. Las reservas permanecen con sus dueños. Requiere confirmación docente.",
        "requires_two_rivals": True
    }
]

COMODINES_PRESETS = [
    {"id": "comodin_div_5", "name": "Dividir saldo entre 5", "active": False},
    {"id": "comodin_perder_20_lanzar", "name": "Perder 20% y lanzar otra vez", "active": False},
    {"id": "comodin_dado_x10", "name": "Sumar dado x 10 TDL", "active": False},
    {"id": "comodin_10_todos", "name": "Recibir 10% de todos los demás", "active": False},
    {"id": "comodin_ganar_10000", "name": "Ganar 10.000 TDL del Banco", "active": False},
    {"id": "comodin_extra_roll", "name": "Lanzar otra vez", "active": False},
    {"id": "comodin_quitar_20_rival", "name": "Ganar 20% descontado de otro equipo y perder 1 turno", "active": False}
]
