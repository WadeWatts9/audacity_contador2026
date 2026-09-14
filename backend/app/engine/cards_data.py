"""
Catálogo completo de tarjetas P01-P15 y E01-E15 según la especificación Audacity.
Las respuestas de las preguntas (P) son estrictamente privadas para el docente/banco.
"""

CARDS_CATALOG = [
    # --- PREGUNTAS P01 - P15 ---
    {
        "code": "P01",
        "deck_type": "P",
        "title": "De la naturaleza",
        "text": "¿A qué sector pertenecen la agricultura, la pesca y la minería? Explicá qué tienen en común.",
        "teacher_answer": "Primario: obtienen recursos de la naturaleza.",
        "source": "Registro, p. 1",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P01.png"
    },
    {
        "code": "P02",
        "deck_type": "P",
        "title": "Transformar",
        "text": "Una fábrica convierte leche en yogur. ¿A qué sector pertenece esa actividad y por qué?",
        "teacher_answer": "Secundario: transforma una materia prima en un bien elaborado.",
        "source": "Registro, p. 1",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P02.png"
    },
    {
        "code": "P03",
        "deck_type": "P",
        "title": "Conectar",
        "text": "Un camión lleva yogures al supermercado, que los vende. ¿A qué sector pertenecen ambas actividades?",
        "teacher_answer": "Terciario: transporte y comercio son servicios de distribución y venta.",
        "source": "Registro, p. 1",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P03.png"
    },
    {
        "code": "P04",
        "deck_type": "P",
        "title": "Conocimiento",
        "text": "Un equipo investiga una nueva técnica de conservación. ¿Qué sector representa en la clasificación de cinco sectores?",
        "teacher_answer": "Cuaternario: genera conocimiento e innovación.",
        "source": "Registro, p. 1",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P04.png"
    },
    {
        "code": "P05",
        "deck_type": "P",
        "title": "Decidir",
        "text": "La alta dirección define la estrategia de una empresa. ¿Qué sector representa según el registro?",
        "teacher_answer": "Quinario: decisiones de alto nivel. La división en cinco sectores no es universal.",
        "source": "Registro, p. 1",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P05.png"
    },
    {
        "code": "P06",
        "deck_type": "P",
        "title": "Mercado digital",
        "text": "En una tienda virtual, ¿quién es oferente y quién es demandante? ¿Es necesario un local físico para que exista mercado?",
        "teacher_answer": "Oferente: quien vende. Demandante: quien desea comprar. No: el mercado puede ser físico o virtual.",
        "source": "Registro, p. 1",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P06.png"
    },
    {
        "code": "P07",
        "deck_type": "P",
        "title": "Mercado abierto",
        "text": "Muchos vendedores ofrecen un producto homogéneo, con información amplia y entrada fácil. ¿Qué estructura describe?",
        "teacher_answer": "Competencia perfecta. Ningún participante controla por sí solo el precio.",
        "source": "Registro, p. 2",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P07.png"
    },
    {
        "code": "P08",
        "deck_type": "P",
        "title": "Un solo vendedor",
        "text": "Hay un único oferente, fuertes barreras de entrada y pocos sustitutos. ¿Qué estructura es y quién concentra poder?",
        "teacher_answer": "Monopolio: el vendedor concentra poder de mercado.",
        "source": "Registro, p. 2",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P08.png"
    },
    {
        "code": "P09",
        "deck_type": "P",
        "title": "Pocos competidores",
        "text": "Tres empresas dominan la oferta y cada una observa las decisiones de las otras. ¿Qué estructura representa?",
        "teacher_answer": "Oligopolio: pocos oferentes cuyas decisiones afectan a los demás.",
        "source": "Registro, p. 2",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P09.png"
    },
    {
        "code": "P10",
        "deck_type": "P",
        "title": "Un gran comprador",
        "text": "Muchos productores venden a un comprador principal. ¿Qué estructura es y quién tiene más poder de negociación?",
        "teacher_answer": "Monopsonio: el comprador principal concentra poder de negociación.",
        "source": "Registro, p. 2",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P10.png"
    },
    {
        "code": "P11",
        "deck_type": "P",
        "title": "Ser diferente",
        "text": "Muchos comercios compiten con productos diferenciados por diseño y atención. ¿Qué estructura representa?",
        "teacher_answer": "Competencia monopolística: numerosos oferentes con productos diferenciados.",
        "source": "Registro, p. 2",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P11.png"
    },
    {
        "code": "P12",
        "deck_type": "P",
        "title": "Nicho y sector",
        "text": "Una fábrica produce ropa para ciclistas urbanos. Identificá el sector de fabricación y el nicho al que apunta.",
        "teacher_answer": "Sector secundario; nicho: ciclistas urbanos. El nicho no permite deducir por sí solo la estructura del mercado.",
        "source": "Registro, pp. 1-2",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P12.png"
    },
    {
        "code": "P13",
        "deck_type": "P",
        "title": "Presupuesto",
        "text": "Un equipo recibe 1.000 TDL y gasta 650 TDL. ¿Cuánto le queda? Si reserva 200 TDL, ¿cuánto puede gastar todavía?",
        "teacher_answer": "Quedan 350 TDL en total; 200 reservados y 150 disponibles. Reservar no equivale a gastar.",
        "source": "Programa, p. 5, unidad 5; ejercicio original",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P13.png"
    },
    {
        "code": "P14",
        "deck_type": "P",
        "title": "Elegir tiene costo",
        "text": "Solo podés elegir entre ir al cine o ir a un partido. Elegís el cine. ¿Cuál es el costo de oportunidad?",
        "teacher_answer": "La alternativa a la que renunciás: ir al partido (el beneficio de la mejor alternativa descartada).",
        "source": "Programa, p. 4, unidad 1; aplicación didáctica",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P14.png"
    },
    {
        "code": "P15",
        "deck_type": "P",
        "title": "Proyecto en marcha",
        "text": "Antes de organizar una feria estudiantil, nombrá tres decisiones que permitan planificar el proyecto.",
        "teacher_answer": "Se aceptan tres decisiones pertinentes: objetivo, recursos y presupuesto, tareas y responsables, cronograma o evaluación de riesgos/resultados.",
        "source": "Programa, pp. 3 y 5-6, unidad 6; aplicación didáctica",
        "engine_rule": None,
        "target_description": "Validación manual docente contra respuesta de referencia.",
        "image_path": "/cards/P15.png"
    },

    # --- RETOS ECONÓMICOS E01 - E15 ---
    {
        "code": "E01",
        "deck_type": "E",
        "title": "Inversión a futuro",
        "text": "Perdés tus próximos 2 turnos. Al comenzar el tercero, el banco te paga el 15% del saldo que tenías al tomar esta tarjeta.",
        "teacher_answer": None,
        "source": "Costo de oportunidad y espera.",
        "engine_rule": "E01_INVERSION_FUTURO",
        "target_description": "Dos turnos perdidos. Al 3er turno propio (n+3), el banco paga 15% de la base B original.",
        "image_path": "/cards/E01.png"
    },
    {
        "code": "E02",
        "deck_type": "E",
        "title": "Préstamo entre equipos",
        "text": "Elegí otro equipo y prestale el 40% de tu saldo. Cobrá 3 cuotas: cada una será el 20% del saldo disponible del deudor al inicio de sus próximos 3 turnos.",
        "teacher_answer": None,
        "source": "Crédito, riesgo y pagos variables.",
        "engine_rule": "E02_PRESTAMO_INTEREQUIPOS",
        "target_description": "Transfiere 40% de B al deudor. Cobro de 3 cuotas de 20% del disponible variable al inicio de sus 3 próximos turnos.",
        "image_path": "/cards/E02.png"
    },
    {
        "code": "E03",
        "deck_type": "E",
        "title": "Inflación",
        "text": "La inflación reduce tu poder de compra. Como efecto del juego, pagá al banco el 10% de tu saldo.",
        "teacher_answer": None,
        "source": "Distinguir dinero nominal y poder adquisitivo.",
        "engine_rule": "E03_INFLACION",
        "target_description": "Debitar 10% de B disponible y acreditar al banco.",
        "image_path": "/cards/E03.png"
    },
    {
        "code": "E04",
        "deck_type": "E",
        "title": "Tres dados, una decisión",
        "text": "Tirá el dado 3 veces y sumá. Si el total es 6 o menos, pagá al banco el 20% de tu saldo. Si es mayor, el banco te paga un 30%.",
        "teacher_answer": None,
        "source": "Probabilidad y riesgo.",
        "engine_rule": "E04_TRES_DADOS",
        "target_description": "3 dados. Suma <= 6: paga 20% B al banco; suma > 6: banco paga 30% B.",
        "image_path": "/cards/E04.png"
    },
    {
        "code": "E05",
        "deck_type": "E",
        "title": "Ahorro programado",
        "text": "Reservá el 30% de tu saldo hasta el inicio de tu próximo turno. Entonces recuperás ese capital y el banco agrega un 20% del monto reservado.",
        "teacher_answer": None,
        "source": "Ahorro, liquidez e interés.",
        "engine_rule": "E05_AHORRO_PROGRAMADO",
        "target_description": "Mover 30% B a reserva. Al próximo turno se libera y el banco abona 20% sobre lo reservado.",
        "image_path": "/cards/E05.png"
    },
    {
        "code": "E06",
        "deck_type": "E",
        "title": "Contribución tributaria",
        "text": "Pagá al banco el 12% de tu saldo por una contribución tributaria. El banco administra esos fondos durante la partida.",
        "teacher_answer": None,
        "source": "Tributos y financiamiento colectivo.",
        "engine_rule": "E06_CONTRIBUCION_TRIBUTARIA",
        "target_description": "Transferir 12% de B disponible al banco.",
        "image_path": "/cards/E06.png"
    },
    {
        "code": "E07",
        "deck_type": "E",
        "title": "Apoyo al emprendimiento",
        "text": "Tu proyecto recibe un apoyo. El banco te entrega el 25% de tu saldo actual. No debés devolverlo.",
        "teacher_answer": None,
        "source": "Diferenciar un apoyo no reembolsable de un préstamo.",
        "engine_rule": "E07_APOYO_EMPRENDIMIENTO",
        "target_description": "Banco acredita 25% de B disponible como subsidio a fondo perdido.",
        "image_path": "/cards/E07.png"
    },
    {
        "code": "E08",
        "deck_type": "E",
        "title": "Reparación urgente",
        "text": "Una máquina se avería. Pagá al banco el 15% de tu saldo para repararla. Podés seguir jugando.",
        "teacher_answer": None,
        "source": "Costos imprevistos y reserva de liquidez.",
        "engine_rule": "E08_REPARACION_URGENTE",
        "target_description": "Pagar 15% B al banco. Cubierto por seguro E11 si está activo.",
        "image_path": "/cards/E08.png"
    },
    {
        "code": "E09",
        "deck_type": "E",
        "title": "Intercambio comercial",
        "text": "Elegí otro equipo. Pagale el 10% de tu saldo y recibí el 10% del suyo. Calculen ambos importes antes de transferir.",
        "teacher_answer": None,
        "source": "Transferencias y bases porcentuales distintas.",
        "engine_rule": "E09_INTERCAMBIO_COMERCIAL",
        "target_description": "Intercambio cruzado simultáneo: Actor paga 10% de B_A a B; B paga 10% de B_B a Actor.",
        "image_path": "/cards/E09.png"
    },
    {
        "code": "E10",
        "deck_type": "E",
        "title": "Campaña de ventas",
        "text": "Invertís en publicidad: pagá al banco el 5% de tu saldo. Luego, el banco te paga el 20% del saldo que te quedó.",
        "teacher_answer": None,
        "source": "Porcentajes sucesivos y costo-beneficio.",
        "engine_rule": "E10_CAMPANA_VENTAS",
        "target_description": "Paga 5% de B al banco; luego banco paga 20% sobre el saldo disponible resultante.",
        "image_path": "/cards/E10.png"
    },
    {
        "code": "E11",
        "deck_type": "E",
        "title": "Seguro del negocio",
        "text": "Podés pagar al banco el 5% de tu saldo. Si lo hacés, evitás la próxima pérdida por Reparación urgente (E08) o Fraude (E13). Se usa una sola vez.",
        "teacher_answer": None,
        "source": "Prima, cobertura y decisión bajo riesgo.",
        "engine_rule": "E11_SEGURO_NEGOCIO",
        "target_description": "Opcional: paga 5% de B. Activa cobertura de 1 uso para E08 o E13. No acumulable.",
        "image_path": "/cards/E11.png"
    },
    {
        "code": "E12",
        "deck_type": "E",
        "title": "Cooperación solidaria",
        "text": "Elegí otro equipo y transferile el 10% de tu saldo. Ese equipo recibe el dinero sin obligación de devolverlo.",
        "teacher_answer": None,
        "source": "Cooperación y diferencia entre donación y crédito.",
        "engine_rule": "E12_COOPERACION_SOLIDARIA",
        "target_description": "Transfiere 10% de B a otro equipo como donación.",
        "image_path": "/cards/E12.png"
    },
    {
        "code": "E13",
        "deck_type": "E",
        "title": "Fraude comercial",
        "text": "Una oferta engañosa te provoca una pérdida. Pagá al banco el 20% de tu saldo. Si tenés el seguro E11 activo, usalo y no pagues.",
        "teacher_answer": None,
        "source": "Riesgo de fraude y cobertura.",
        "engine_rule": "E13_FRAUDE_COMERCIAL",
        "target_description": "Pérdida del 20% de B al banco. Si tiene seguro E11 activo, se consume y se evita la pérdida.",
        "image_path": "/cards/E13.png"
    },
    {
        "code": "E14",
        "deck_type": "E",
        "title": "Crédito del banco",
        "text": "El banco te presta el 30% de tu saldo. Al inicio de tu segundo próximo turno, devolvé ese monto más un 10% de interés sobre el préstamo.",
        "teacher_answer": None,
        "source": "Capital prestado, deuda e interés.",
        "engine_rule": "E14_CREDITO_BANCO",
        "target_description": "Banco presta capital C = 30% B. A devolver al inicio de n+2 con C + 10% de interés.",
        "image_path": "/cards/E14.png"
    },
    {
        "code": "E15",
        "deck_type": "E",
        "title": "Demanda cambiante",
        "text": "Tirá el dado una vez. Si sale par, el banco te paga el 20% de tu saldo. Si sale impar, pagá al banco un 10%.",
        "teacher_answer": None,
        "source": "Incertidumbre en ventas y resultados.",
        "engine_rule": "E15_DEMANDA_CAMBIANTE",
        "target_description": "Dado 1-6. Par: +20% B desde el banco. Impar: -10% B al banco.",
        "image_path": "/cards/E15.png"
    }
]
