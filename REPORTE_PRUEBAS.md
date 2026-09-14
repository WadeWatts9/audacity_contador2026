# Reporte de Pruebas y Verificación · Audacity 2.0

**Fecha de ejecución**: 2026-09-13  
**Entorno**: Windows 11 (Docker 29.7.2, Python 3.13.7, Node v24.19.0)  
**Estado**: 100% Satisfactorio (15/15 pruebas unitarias del motor financiero y reglas superadas).

---

## 1. Cobertura de Pruebas Automatizadas (Pytest)

Se ejecutó la suite de pruebas en el motor contable y de efectos (`backend/tests/`):

| Archivo / Prueba | Descripción de la Regla Verificada | Resultado |
|---|---|:---:|
| `test_e01_inversion_futuro` | Base 1.000 TDL. 2 turnos perdidos. Al 3er turno propio (n+3), el Banco acredita 150 TDL (+15%). | **PASSED** |
| `test_e02_prestamo_interequipos` | Prestamista A (1.000) presta 40% (400) a Deudor B (600). Deudor queda con 1.000. 3 cuotas variables al 20% del disponible de B: 200, 160 y 128 TDL. Total cobrado: 488 TDL. Saldo final A: 1.088 TDL; B: 512 TDL. Contrato extinguido. | **PASSED** |
| `test_e03_inflacion` | Base 1.000 TDL. Débito exacto del 10% (100 TDL) a favor del Banco. Saldo restante: 900 TDL. | **PASSED** |
| `test_e04_tres_dados` | Base 1.000 TDL. Suma &le; 6 (dados 2, 2, 2 = 6) debita 20% al Banco (saldo 800). Suma &gt; 6 (dados 3, 3, 1 = 7) sobre 800 acredita 30% del Banco (saldo 1.040). | **PASSED** |
| `test_e05_ahorro_programado` | Base 1.000 TDL. Reserva 30% (300 TDL, disponible 700, reservado 300, total 1.000). Al inicio del turno siguiente, se liberan los 300 y el Banco acredita 60 TDL (20% de lo reservado). Saldo final: 1.060 TDL. | **PASSED** |
| `test_e06_tributaria` | Base 1.000 TDL. Transferencia del 12% (120 TDL) al Banco. Saldo restante: 880 TDL. | **PASSED** |
| `test_e07_apoyo_emprendimiento` | Base 1.000 TDL. El Banco entrega 250 TDL (25%) como subsidio no reembolsable sin generar deuda. Saldo final: 1.250 TDL. | **PASSED** |
| `test_e08_reparacion_urgente` | Sin seguro: debita 15% (150 TDL) al Banco. Con seguro E11 activo: el seguro se consume y evita la pérdida del 15% sin descontar saldo. | **PASSED** |
| `test_e09_intercambio_comercial` | Equipos A (1.000 TDL) y B (600 TDL). A paga 10% de su saldo (100) y recibe 10% de B (60). B paga 10% de su saldo (60) y recibe 100. Cálculo atómico sobre bases previas. Saldos finales: A=960 TDL, B=640 TDL. | **PASSED** |
| `test_e10_campana_ventas` | Base 1.000 TDL. Gasta 5% (50 TDL) en publicidad (quedan 950 TDL). Luego el Banco abona 20% del saldo resultante (190 TDL). Saldo final: 1.140 TDL. | **PASSED** |
| `test_e13_fraude_comercial` | Base 1.000 TDL. Con seguro E11: se consume la póliza y se evita la pérdida del 20%. Sin seguro: débito del 20% (200 TDL) al Banco (saldo final 800 TDL). | **PASSED** |
| `test_e14_credito_banco` | Base 1.000 TDL. Banco presta 300 TDL (disponible pasa a 1.300). Se programa devolución fija de 330 TDL (300 + 10%) en turno n+2. Al cumplirse, se cancela y saldo final queda en 970 TDL. | **PASSED** |
| `test_e15_demanda_cambiante` | Base 1.000 TDL. Dado par (4) abona +20% (saldo 1.200 TDL). Dado impar (3) sobre 1.200 debita -10% (saldo 1.080 TDL). | **PASSED** |
| `test_undo_transfer` | Transferencia de 200 TDL entre equipos revertida mediante «Deshacer». Restaura exactamente los saldos previos e impide doble reversión. | **PASSED** |
| `test_undo_insurance_consumed` | Seguro E11 consumido por avería E08 restaurado a estado activo tras deshacer el asiento de avería. | **PASSED** |

---

## 2. Verificación de Compilación de Frontend

- **Vite & TypeScript**: Compilación exitosa en 9.38s.
- **Módulos**: 1.585 módulos transformados.
- **Bundle**: `dist/index.html` (0.49 kB), `dist/assets/index.css` (5.21 kB), `dist/assets/index.js` (201.72 kB).
- **Tarjetas estáticas**: 30 archivos PNG (`P01.png` a `P15.png` y `E01.png` a `E15.png`) integrados en `public/cards/`.
- **Cero dependencias CDN**: Fuentes del sistema y paquetes SVG locales (sin llamadas de red externas requeridas).
