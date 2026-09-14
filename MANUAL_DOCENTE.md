# Manual Operativo del Docente / Banco · Audacity

Guía de referencia rápida para el docente administrador del Banco Central de **Audacity**.

---

## 1. Inicio de la Partida

1. Inicie sesión con su usuario (`admin_docente`) y contraseña.
2. Si es la primera partida, haga clic en **"Nueva Partida"**:
   - Asigne un nombre al grupo/clase.
   - Elija el perfil del tablero:
     - **Genially (Predeterminado)**: 5 equipos (`Contador Gallo`, `León`, `Perro`, `Mano`, `Estrella`).
     - **Prezi**: 4 equipos (`Contador Diamante`, `Auto`, `Sombrero`, `Cerdo`).
   - Confirme los saldos iniciales (por defecto 10.000 TDL por equipo y 100.000 TDL para el Banco).
3. Al crear la partida, se abrirá la **Hoja de Credenciales de Equipos**:
   - Contiene el código de partida (ej. `ECO-AB12`) y las contraseñas generadas al azar para cada equipo.
   - Copie o distribuya las claves a cada mesa de estudiantes. Esta hoja no volverá a mostrarse en pantallas públicas.

---

## 2. Gestión de Turnos y Casillas

El turno avanza en orden cíclico entre los equipos activos.

1. **Registrar lanzamiento**: Ingrese el número del dado físico (1 a 6) que sacó el equipo, o presione el botón de dados para generar una tirada digital.
2. **Seleccionar casilla**: Indique la casilla del tablero físico/digital donde cayó la ficha del equipo.
3. **Presione "Avanzar Turno"**:
   - El sistema ejecuta automáticamente los compromisos al inicio de turno en el orden estricto de la regla:
     1. **Paso 1**: Libera depósitos a plazo o ahorros programados (E05, casillas) y abona sus intereses pactados desde el Banco.
     2. **Paso 2**: Abona bonificaciones diferidas (E01).
     3. **Paso 3**: Cobra cuotas de préstamos (E02: 20% del disponible variable del deudor; E14: cuota fija del crédito bancario).
     4. **Paso 4**: Si el equipo tenía un turno perdido, lo descuenta y pasa el turno impidiéndole jugar esta ronda. Si no, le permite operar.

---

## 3. Dinámica de Tarjetas (P y E)

### Tarjetas de Pregunta (P01 - P15)
- Cuando el equipo cae en una casilla de Pregunta (ej. Casilla 1 o 2), se extrae una tarjeta P.
- El panel docente muestra la consigna y la **Clave de Respuesta Protegida del Banco** con sus fuentes bibliográficas.
- El docente valida si la respuesta del estudiante es conceptualmente correcta o incorrecta:
  - Casilla 1: Aplica premio (+100%, +50%, etc.) o descuento (-60%, -30%, etc.).
  - Casilla 2: Si acierta, **habilita automáticamente la extracción de un Reto Económico (E)** en el mismo turno; si falla, descuenta 25% del disponible al Banco.
- Las respuestas docentes nunca son visibles para los estudiantes ni en el modo proyección.

### Tarjetas de Reto Económico (E01 - E15)
- Las tarjetas de reto económico aplican efectos automáticos con impacto contable y financiero:
  - **E01 (Inversión a futuro)**: Marca 2 turnos perdidos y programa un bono del 15% para el inicio del turno n+3.
  - **E02 (Préstamo entre equipos)**: Transfiere 40% del saldo del prestamista al deudor seleccionado y programa 3 cuotas del 20% del disponible variable del deudor al inicio de sus siguientes 3 turnos.
  - **E03 (Inflación)**: Paga 10% del disponible al Banco.
  - **E04 (Tres dados)**: Suma de 3 dados. Si suma &le; 6, paga 20% al Banco; si suma &gt; 6, el Banco abona 30%.
  - **E05 (Ahorro programado)**: Reserva 30% del disponible; al siguiente turno se libera con 20% de interés abonado por el Banco.
  - **E06 (Tributos)**: Paga 12% al Banco.
  - **E07 (Apoyo)**: El Banco entrega subsidio del 25% sin obligación de reintegro.
  - **E08 (Reparación urgente)**: Paga 15% al Banco. *Si el equipo tiene el Seguro E11 activo, la pérdida se evita y el seguro se consume.*
  - **E09 (Intercambio comercial)**: Transfiere 10% cruzado simultáneo entre dos equipos sobre sus saldos base previos.
  - **E10 (Campaña de ventas)**: Paga 5% en publicidad y luego el Banco paga 20% sobre el saldo disponible resultante.
  - **E11 (Seguro del negocio)**: Opcional: paga 5% de prima y adquiere cobertura única ante E08 o E13. No acumulable.
  - **E12 (Cooperación solidaria)**: Donación del 10% a otro equipo.
  - **E13 (Fraude comercial)**: Pierde 20% al Banco. *Si tiene el Seguro E11 activo, se consume y evita pagar.*
  - **E14 (Crédito bancario)**: El Banco desembolsa 30% de capital; en el turno n+2 vence la cuota fija (capital + 10%). Si no hay fondos, se registra como deuda vencida sin cobro parcial.
  - **E15 (Demanda cambiante)**: 1 dado. Par: Banco paga 20%. Impar: equipo paga 10% al Banco.

---

## 4. Operaciones Bancarias y Ajustes

Presione el botón **"Operar Banco"** para realizar:
- **Pagar a equipo**: Acreditación manual desde los fondos del Banco.
- **Cobrar a equipo**: Débito manual a favor del Banco.
- **Transferir**: Mover fondos disponibles entre dos cuentas cualesquiera.
- **Ajustar saldo**: Establece un saldo disponible objetivo. El sistema calcula la diferencia y genera los asientos contra la cuenta del sistema `CUENTA DE EMISIÓN Y AJUSTES`, exigiendo motivo de auditoría.
- **Poner saldo en cero**: Liquida el dinero disponible y reservado de una cuenta. Requiere confirmación si la cuenta posee contratos vigentes.
- **Deshacer**: En el feed de auditoría inferior, cada movimiento posee el botón "Deshacer", el cual crea un asiento inverso enlazado, restaura los fondos y el estado asociado (seguros, turnos perdidos, contratos).

---

## 5. Modo Proyector para el Aula

Haga clic en **"Modo Proyector"** en la barra superior cuando proyecte hacia la pared o pizarra del aula:
- Oculta controles administrativos, claves de respuesta y credenciales.
- Muestra el Ranking gigante con las fichas, el dinero total nominal y el equipo que tiene el turno activo en letra grande y de alto contraste.

---

## 6. Exportación de Auditoría

Al finalizar la clase o partida, presione **"Exportar CSV Seguro"**. El archivo descargado contendrá la lista cronológica de todos los asientos contables con fecha/hora local de Montevideo, sanitizado contra inyección de fórmulas CSV.
