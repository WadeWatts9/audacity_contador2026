# Antigravity: construir el sistema informático dockerizado de Audacity

Construí, ejecutá y verificá un sistema informático completo llamado **Audacity**, en español rioplatense, para gestionar una partida escolar presencial de Economía para Jóvenes. Entregá código fuente funcional y reproducible con Docker Compose. El producto debe permitir que varios equipos y el docente jueguen simultáneamente desde navegadores distintos. No entregues solamente un diseño, un prompt, una maqueta o saldos guardados en el navegador. El dinero es ficticio y se expresa en TDL.

Esta especificación es autocontenida y reemplaza los prompts anteriores. Existen exactamente dos mazos: preguntas P01-P15 y retos económicos E01-E15. No incluir los retos conceptuales R01-R15. Los catálogos completos y las respuestas para el banco aparecen al final de este documento.

## Resultado esperado y arquitectura

Usar React + TypeScript para la interfaz, FastAPI para la API, SQLAlchemy y Alembic para persistencia/migraciones, PostgreSQL como base de datos, y WebSocket o SSE para actualizaciones en tiempo real. Usar versiones compatibles y estables verificadas al implementar, fijarlas y entregar lockfiles. No depender de Firebase, Supabase, cuentas cloud, APIs pagas o servicios externos para jugar. Después de descargar y construir las imágenes, el sistema debe funcionar sin Internet en la red local. Fuentes, iconos y assets servidos localmente; sin CDN obligatorio.

Docker Compose debe incluir:

- `db`: PostgreSQL con volumen nombrado persistente y healthcheck. No publicar el puerto de base de datos al host.
- `migrate`: proceso de una sola ejecución que espera a la base saludable y aplica las migraciones; debe fallar visiblemente si una migración falla.
- `api`: backend que arranca después de migraciones correctas, con healthcheck, cierre ordenado y usuario no root cuando sea viable.
- `web`: compilación multietapa del frontend y servidor Nginx que entrega los archivos y hace proxy a `/api` y `/ws` o `/events`. Soportar upgrade WebSocket o desactivar buffering para SSE; no usar el servidor de desarrollo como despliegue final.

Publicar un único puerto configurable, por defecto 8080. Usar URLs relativas y mismo origen para API y eventos: jamás incluir `localhost` como destino de API en el bundle que usan los celulares. Dentro de Compose conectar a `db` y `api` por nombres de servicio. Configurar `BIND_ADDRESS` y `APP_PORT`; acceso inicial local `127.0.0.1:8080`, y modo aula documentado enlazando a `0.0.0.0` para acceder mediante la IP LAN del equipo docente. Documentar cómo descubrir esa IP y permitir el puerto en el firewall sin desactivarlo. Ofrecer configuración de HTTPS para exposición fuera de una LAN controlada y cookies seguras apropiadas al entorno. No publicar nada en Internet por defecto.

Entregar `compose.yaml`, Dockerfiles, `.dockerignore`, `.env.example` sin secretos, migraciones, lockfiles, datos iniciales de tarjetas, scripts de inicialización, pruebas, README y manuales breves del banco y de estudiantes. Un arranque nuevo debe realizarse con `docker compose up -d --build`; proporcionar un comando adicional explícito para crear el primer banco y generar sus credenciales de un solo uso, sin imprimirlas en logs generales. El arranque repetido no recrea usuarios, saldos o partidas ni resetea contraseñas. Validar variables y evitar claves universales predeterminadas.

Entregar comandos exactos de arranque, estado, logs, pruebas, parada, backup y restauración. `docker compose down` conserva datos; señalar en el procedimiento administrativo que `down -v` elimina volúmenes, sin usarlo en pasos ordinarios. Backup consistente con `pg_dump` y restauración con `pg_restore`, incluyendo migraciones/versiones compatibles. Probar que partidas e historial sobreviven a reinicio de contenedores y que un backup se restaura en una base de prueba. No hacer backups públicos dentro del frontend.

## Alcance del juego

El tablero físico o Genially puede seguir mostrándose aparte: no es necesario reconstruir su editor o arrastre de fichas. La aplicación sí registra el turno activo, la casilla elegida por el banco, la tarjeta seleccionada, su resolución, todos los efectos económicos y vencimientos. No inventar compra de propiedades, casas, rentas o premio por pasar la salida. La moneda, fichas, casillas y variantes verificadas se especifican más abajo.

Flujo completo: el banco inicia sesión, crea partida, elige perfil de tablero, confirma saldos iniciales y reglas, entrega credenciales, fija orden de equipos e inicia. Cada equipo entra con código de partida, usuario y contraseña. El banco registra lanzamiento/movimiento y casilla; cuando corresponde, el equipo elige una P o E disponible. El banco valida la pregunta o la ejecución de E; el servidor aplica el efecto una sola vez, actualiza saldos, ranking e historial y programa los compromisos futuros. El banco avanza el turno. Al terminar, guarda y exporta el cierre y las obligaciones pendientes.

## Roles e interfaz

El docente usa `admin_docente` y representa al banco. No compite ni tiene turno de ficha. Puede operar cualquier cuenta, confirmar resultados, gestionar turnos, realizar ajustes, poner saldos en cero, cerrar cuentas y deshacer movimientos y sus efectos asociados. El ranking excluye al banco, pero el panel muestra sus fondos por separado.

En el perfil principal crear los equipos `contador_gallo`, `contador_leon`, `contador_perro`, `contador_mano` y `contador_estrella`, con ficha y color coherentes. Generar contraseñas aleatorias únicas de al menos 12 caracteres. Guardarlas mediante Argon2id o mecanismo equivalente; permitir restablecerlas sin consultar las anteriores. El banco recibe una hoja de credenciales únicamente al crearlas; nunca se muestra en proyección ni a otros equipos. No requerir correos ni nombres personales de estudiantes. Aislar cuentas repetidas mediante código de partida y membresías.

Interfaz del equipo: ficha, saldo total, disponible y reservado; deudas/cuotas y premios pendientes; turno y turnos perdidos; dos mazos; último movimiento e historial propio. Permitir pagos y transferencias desde su propio disponible con vista previa. Las ganancias, descuentos especiales, préstamos, intercambios y efectos E requieren aprobación del banco. Una solicitud pendiente no mueve dinero. Permitir al banco activar aprobación de todos los pagos ordinarios.

Interfaz del banco: ranking descendente por disponible + reservado, empates con mismo puesto y orden visual estable; cuenta del banco; feed en tiempo real; solicitudes; tablero de turnos; mazos y respuestas; reservas, préstamos, seguros y vencimientos; editor de parámetros antes de iniciar; ajustes y reversiones; filtros y exportación CSV protegida contra inyección de fórmulas. Fecha/hora del servidor mostrada en America/Montevideo. Modo proyección con ranking y tarjeta activa, sin respuestas, credenciales o controles administrativos.

La pantalla de tarjetas debe inspirarse en el HTML Audacity entregado: fondo verde de tablero, superficie marfil, marca roja, bordes negros, preguntas azules y retos económicos verdes. Mostrar primero la actividad, no una página promocional. Códigos visibles, contraste suficiente, tipografía legible, navegación por teclado, foco y retorno de foco en diálogos, controles táctiles y responsive para celulares. No depender solo del color. Las tarjetas abiertas mantienen el texto accesible aunque usen su ilustración. Si se entregan imágenes P/E, reutilizarlas; si no, renderizar fielmente sus textos en tarjetas estilizadas, sin bloquear la implementación por un asset faltante.

## Selección de tarjetas y privacidad de respuestas

Solo P y E. Estado de mazo por partida: disponible, asignada, resuelta/usada, devuelta. La asignación es atómica: dos equipos no pueden tomar la misma instancia. Un equipo toma tarjeta únicamente cuando el banco habilita la selección según casilla. Abrir/consultar una tarjeta usada no vuelve a ejecutarla. Reiniciar mazos requiere banco; genera nuevas instancias y no altera efectos o contratos anteriores.

Las P usan 60 segundos sugeridos, con posibilidad de pausa/ampliación del banco. Su respuesta se valida manualmente contra la clave docente; aceptar equivalentes, sin evaluación automática por coincidencia literal. El servidor entrega las respuestas solamente a usuarios con rol banco. No empaquetar claves en el bundle, HTML, mapas de código, respuestas de API de equipos ni eventos de proyección.

Cuando la casilla diga «elige un reto», usar E. Aplicar el efecto de E exactamente una vez, sin premio adicional genérico por acierto. Si una P acertada habilita reto, habilitar E como siguiente paso del mismo turno sin cobrar dos veces la resolución de P. En E no hay un cronómetro obligatorio ni respuestas correctas: el banco confirma decisiones, objetivos y tiradas.

## Contabilidad, concurrencia y seguridad

PostgreSQL es la fuente única de verdad. Guardar importes como centésimos enteros y tasas como valores exactos; calcular y redondear half-up en servidor. Capturar base previa a cada efecto. Disponible + reservado = saldo total. Cada transacción tiene asientos balanceados, origen, destino, actor, aprobador, causa, fecha, versión de regla y saldos antes/después. Premios/pérdidas usan el banco como contraparte; capitalizaciones/ajustes usan cuenta de emisión/ajustes explícita.

Transferencias y efectos compuestos son atómicos. Bloqueos de filas en orden estable o control de versiones, restricciones e idempotency keys deben evitar sobregiro, dobles cobros y carreras concurrentes. Los reintentos, doble clic y reconexiones no duplican tarjetas, pagos, cuotas, turnos o eventos. No aceptar montos negativos, no finitos, destinos ajenos a la partida ni transferencias a sí mismo. No crear dinero automáticamente cuando el banco queda sin fondos.

Autorizar en backend todos los endpoints y canales realtime. Sesiones seguras, expiración, logout, limitación de intentos, protección CSRF donde corresponda y secretos fuera de código/logs. Un equipo no puede concederse rol banco, tocar otro saldo, aprobarse solicitudes, leer claves docentes ni suscribirse a otra partida. Eventos con identificador/cursor: tras reconexión recuperar estado canónico e historial faltante, sin duplicación. Las operaciones rechazadas no dejan efectos parciales. Auditoría persistente incluso para acciones del banco.

## Entrega y verificación que se considera terminada

Construir el producto completo, ejecutarlo en contenedores y documentar resultados reales. Comprobar `docker compose config`, construcción desde cero, salud de servicios, migraciones, inicio de sesión, acceso simultáneo de cinco equipos y banco, y funcionamiento desde otro dispositivo/host de la LAN cuando el entorno lo permita. Si el entorno no permite probar LAN o Docker, decir exactamente qué quedó sin verificar; no declarar éxito sin ejecutar.

Probar autenticación y aislamiento de partidas; extracción concurrente de la misma tarjeta; claves P inaccesibles a equipos; respuesta P y encadenamiento a E; transferencias concurrentes sin sobregiro; idempotencia; todos los casos numéricos del catálogo; reversión simple y dependiente; puesta en cero; cierre; turnos perdidos con cuotas; reconexión; persistencia tras reinicio; backup/restauración. Probar también el perfil Prezi con cuatro equipos. Ranking y feed deben reflejar una transacción confirmada en menos de 2 segundos en el entorno de prueba. Interfaz usable en móvil y escritorio.

Incluir pruebas del motor de reglas y pruebas de integración con PostgreSQL real en un entorno Docker de pruebas aislado. No usar datos reales de aula ni borrar volúmenes de producción durante pruebas. Entregar un informe breve de pruebas, limitaciones concretas y comandos reproducibles. El resultado no está completo si faltan contenedores, backend, persistencia, roles, realtime, contratos por turnos o restauración de datos.


## Tablero principal y saldos iniciales

Referencia: https://view.genially.com/67f650696eafa23e8c4cc1b8 . Perfil predeterminado Genially, con cinco fichas. Moneda ficticia TDL. Propuesta configurable: 10.000 TDL por equipo y 100.000 para el banco. Estos saldos no están fijados en las fuentes. El banco confirma los parámetros antes de iniciar.

## Reglas de casillas


Incluir un editor de reglas y presets. Las siguientes mecánicas fueron leídas del tablero; las interpretaciones propuestas se identifican como tales en la configuración y deben confirmarse antes de jugar. Por defecto, porcentajes de saldo propio usan el disponible anterior a la operación y las ganancias/pérdidas se liquidan con el banco. El docente puede cambiar la base a total antes de la partida; si ello exige fondos reservados, no liberarlos automáticamente.

1. Pregunta: acierto +100% / error -60%; otra +50% / -30%; otra +30% / -35%; otra +3.000 / -1.500 TDL. Elegir casilla y resultado; aplicar una sola vez tras validación docente.
2. «Responde: acierto reto / error -25%»: acertar habilita una tarjeta E, sin ganancia monetaria automática; fallar descuenta 25%.
3. «Elige un reto»: seleccionar E01-E15 y aplicar su efecto tras validación del banco, sin añadir premio genérico. Los efectos E sí modifican saldos y compromisos de la partida.
4. «Pagas con crédito, pierdes el 15% al Banco»: transferir 15% del saldo base propio al banco. Es un efecto lúdico, no un préstamo real.
5. «Pierde la mitad»: transferir 50% del saldo base al banco.
6. «Pierde un turno, gana 35%»: acreditar 35% y marcar un turno perdido, con contador explícito que consume el admin al pasar ese turno.
7. «Ahorras tu 50%, un turno con la mitad»: propuesta: mover 50% de disponible a reservado sin alterar total; liberarlo al inicio del próximo turno de ese equipo. Registrar apertura y liberación una única vez.
8. «Plazo fijo por un turno, ganas +25%»: no fija capital invertido. Exigir al docente elegir capital al crear el depósito; propuesta: 50% del disponible. Reservar ese capital durante un turno y, al inicio del próximo turno del equipo, devolver principal y acreditar 25% del principal desde el banco. Si el banco carece de fondos, mantener vencimiento pendiente, sin duplicar principal ni interés. Mostrar base y vencimiento. Esta interpretación es editable y no se presenta como texto literal del tablero.
9. «Ganas el 15% del menor saldo. Vuelve a lanzar»: propuesta: 15% del menor saldo base de otro equipo activo, pagado por el banco; no descontar al rival salvo configuración confirmada. Resolver empates sin cobro duplicado; con un solo equipo activo, deshabilitar. Marcar lanzamiento extra.
10. «Si el banco está vacío transfiere 15%, sino cobra 15%»: propuesta: base = saldo propio; banco en cero recibe 15% del equipo; banco positivo paga ese importe al equipo. Si el banco es positivo pero insuficiente, detener y solicitar decisión docente; no cambiar silenciosamente de regla.
11. «Duplica tu saldo, divide el saldo de otro equipo»: el divisor no está especificado. Exigir divisor mayor que 1 en configuración (propuesta 2) y equipo objetivo distinto. Propuesta: duplicar disponible del actor y dividir disponible del objetivo; diferencias contra banco en una única transacción atómica. No tocar reservas.
12. «Cambia los saldos de los adversarios»: seleccionar dos rivales distintos y, como propuesta, intercambiar sus saldos disponibles; reservas permanecen asociadas a sus dueños. Mostrar vista previa y exigir aprobación admin.

La transcripción del Genially también contiene comodines: dividir saldo entre 5; perder 20% y lanzar otra vez; sumar dado × 10; recibir 10% de todos los demás; ganar 10.000 TDL; lanzar otra vez; retirar otro comodín una sola vez; intercambiar comodín; ganar 20% descontado de otro equipo y perder un turno. Crear presets opcionales separados, desactivados hasta confirmación docente. Para 20% de otro equipo, propuesta = 20% de su disponible previo. Para 10% de todos, calcular cada contribución sobre la misma instantánea y liquidar todo atómicamente. Dado validado entre 1 y 6; comodines con propiedad, estado y uso único auditados. No inventar reglas de casas, propiedades o salida que no están especificadas.



## Referencia complementaria: Prezi y versiones del tablero

Se revisó «Gamificación Juego Audacity», de Alan Canto: https://prezi.com/view/88pfnuMHeuZRG3E45kdz/ . La presentación destaca decisiones, pensamiento estratégico, trabajo en equipo, ahorro, inversión y reserva. Sus ejemplos de reto producen movimientos de saldo y compromisos por varios turnos: esto orienta el nuevo mazo E.

El Prezi y el Genially enlazado inicialmente muestran variantes distintas. No mezclar sus parámetros. Mantener como predeterminado el perfil Genially con gallo, león, perro, mano y estrella. En el Prezi se ven cuatro fichas diferentes: diamante azul, auto verde, sombrero amarillo y cerdo rosa. Si el docente elige el perfil Prezi, generar solamente sus cuatro cuentas contador_diamante, contador_auto, contador_sombrero y contador_cerdo, además de admin_docente, con el mismo sistema de contraseñas seguras. El perfil y sus equipos quedan fijados al iniciar partida.

Diferencias comprobadas: Prezi muestra pregunta +300/-150, perder un turno con premio del 5%, pago con crédito del 5% y lanzamiento extra, y duplicar saldo propio sin dividir el de otro. Genially muestra +3.000/-1.500, premio del 35%, crédito del 15% y la casilla combinada de duplicar/dividir. En el Prezi también se muestra un préstamo con +30% y pagos del 5% durante tres turnos, distinto de las nuevas tarjetas E02 y E14. No activar ese préstamo de ejemplo automáticamente, pues la lámina no precisa todas sus bases ni el tratamiento del principal. Las nuevas tarjetas tienen reglas explícitas propias.

Agregar selector de versión y vista de parámetros antes de comenzar. El perfil Prezi replica únicamente los efectos verificados y permite revisar los no definidos antes de habilitarlos; no inventar un reglamento completo a partir de las imágenes. Las tasas, importe inicial del banco/equipos y reglas no especificadas siguen siendo configurables. Los mazos E no cambian según el perfil salvo edición expresa del banco antes de iniciar una nueva partida.


## Banco, contratos y turnos: especificación operativa

### Admin = banco

admin_docente representa y opera el banco: paga premios, recibe pérdidas y tributos, concede y cobra créditos, controla reservas, contratos, seguros, vencimientos, turnos y dados. El banco tiene una cuenta propia visible en el panel y no compite en el ranking. No tiene ficha ni turno de jugador. Registrar quién hizo cada acción, incluso cuando se originó desde un estudiante. Los equipos solicitan operaciones especiales; solamente el banco las aprueba y ejecuta. Los pagos ordinarios de los equipos mantienen el modo de autorización configurado.

Agregar botones «Pagar a equipo», «Cobrar a equipo», «Transferir», «Prestar», «Cobrar cuota», «Ajustar saldo», «Poner saldo en cero», «Deshacer» y «Cerrar partida». Ajustar saldo recibe un saldo objetivo, calcula la diferencia y crea asientos contra una cuenta explícita de ajustes; nunca hace UPDATE directo sin historial. Se permite corregir tanto equipos como banco. Motivo obligatorio, vista previa de afectados y confirmación para ajustes, cero y deshacer.

«Poner saldo en cero» y «Cerrar saldo» son acciones diferentes. Poner en cero crea un ajuste reversible por todo el dinero disponible y reservado de la cuenta seleccionada; la interfaz debe advertir sobre reservas y obligaciones vigentes. Si hay contratos afectados, exigir resolverlos explícitamente mediante cancelación auditada o reprogramación antes de ejecutar: no perdonar deudas de forma silenciosa. No anular créditos de otros equipos sin mostrar su impacto. Cerrar saldo significa bloquear nuevos movimientos de esa cuenta y conservar su dinero e historial; impedir nuevos vencimientos contra una cuenta cerrada sin que antes se resuelvan sus obligaciones. Poner todas las cuentas en cero requiere vista previa de todos los afectados; reiniciar una partida crea otra sala/partida y conserva el archivo.

«Deshacer» debe restaurar dinero Y estado asociado: cuota cobrada, reserva, seguro consumido/creado, lanzamiento registrado, premio pendiente y turnos perdidos. Crear una reversión enlazada al original; no borrar el original. Si existen operaciones dependientes, ofrecer una vista previa de reversión en cascada en orden inverso y ejecutar todo atómicamente tras confirmación. Si no puede restaurarse coherentemente, bloquear la reversión simple y ofrecer ajuste compensatorio manual claramente identificado. Un movimiento revertido no puede revertirse dos veces. No reproducir automáticamente eventos deshechos. Mostrar antes/después y motivos en la auditoría del banco y el feed del equipo.

### Convenciones fijas de esta edición

En E, «saldo» SIEMPRE significa saldo disponible inmediatamente anterior al efecto, salvo base expresamente fijada en otro momento. Reservado no se gasta. Guardar cada base como instantánea; no modificarla por cambios futuros de saldo. Dinero nominal = disponible + reservado. Ranking principal descendente por dinero nominal, como pide el juego; mostrar aparte deudas, créditos y compromisos, sin sumarlos/restarlos de ese ranking. Avisar que el ranking por dinero puede favorecer temporalmente a quien tomó un préstamo. No presentar un ranking patrimonial como si fuera el mismo indicador.

Numerar oportunidades de turno por equipo. Si E se toma en su turno n, próximo turno = n+1; segundo próximo = n+2; tercer próximo = n+3. Perder un turno impide lanzar/avanzar, pero su inicio ocurre y procesa vencimientos. Orden de inicio: (1) liberar depósitos y abonar sus intereses; (2) abonar bonificaciones diferidas; (3) cobrar cuotas y deudas por fecha de creación del contrato, con ID como desempate; (4) descontar un turno perdido o habilitar lanzamiento. Las cuotas E02 calculan su base justo antes de su propio débito: dos contratos pueden tener bases diferentes. Avanzar turno es una acción exclusiva del banco, idempotente y reversible; no avanzarlo por tiempo de reloj. Un evento bloqueado por fondos del banco conserva su pendiente y detiene el procesamiento del inicio hasta que el docente lo resuelva, sin ejecutar dos veces pasos ya completados.

El sistema registra los dados físicos (enteros 1-6) confirmados por admin; opcionalmente admite dados digitales generados en servidor. Guardar todas las tiradas, resultado y origen. Los dados de E04/E15 no mueven la ficha ni consumen el lanzamiento normal. No permitir que refrescar o reintentar cambie el resultado.

No inventar dinero si el banco no tiene fondos. El docente puede capitalizarlo mediante un ajuste de emisión explícito y auditado. No permitir saldo negativo. E14 insuficiente crea deuda vencida sin cobro parcial; no agrega interés automático ni desaparece. El banco tiene una bandeja de pendientes y un botón de reintento que conserva el importe pactado. Cualquier condonación exige ajuste contractual y registro de motivo, no edición del saldo ocultando la deuda.

Al finalizar la partida no anticipar vencimientos ni borrar obligaciones. Mostrar y exportar saldos, reservas, premios pendientes, préstamos y deudas. Ofrecer al docente «continuar hasta liquidar», «cerrar con obligaciones informadas» o «resolver mediante ajustes explícitos». En el cierre con obligaciones informadas, bloquear nuevos cobros y conservar una instantánea del estado pendiente. Esta excepción de archivo de toda la partida no es cerrar unilateralmente una cuenta durante el juego.

### Contratos y estados

Agregar entidades para tarjeta_instancia, efecto, contrato, cuota, póliza y evento_programado; versión de regla, base, tasa, importe pactado, acreedor, deudor, turno de creación/vencimiento y estados pendiente, ejecutado, vencido, cancelado, revertido. Restricción única sobre (contrato, número de cuota) y (equipo, número de inicio) evita duplicación. Cada ejecución de E necesita una clave única y un estado que impida volver a aplicar la misma tarjeta-instancia. Volver a sacar E en otro momento crea una instancia distinta.

E02 es un préstamo lúdico de devolución variable: las tres cuotas del 20% del disponible vigente extinguen el contrato incluso si su suma es menor que el capital prestado. No sumar una devolución final del capital ni limitar las cuotas al capital. Registrar monto desembolsado y total recuperado por separado; antes del cobro futuro no hay valor fijo para esa cuota. E14 sí tiene devolución fija: capital más interés pactado. No usar el mismo esquema de amortización para ambos.

### Casos adicionales obligatorios

Probar E01: dos oportunidades perdidas y cobro 15% de la base original en n+3, aunque el saldo haya cambiado. E02: A=1.000, B=600, préstamo 400, cuotas 200/160/128 sin otros movimientos; finales A=1.088, B=512; contrato extinguido. Cuota cero cuenta y no se reintenta. Turno perdido del deudor sí cobra cuota. Dos préstamos en un inicio respetan orden fijo.

Probar E03: base 1.000 produce débito 100. E04: suma 6 pierde 200, suma 7 gana 300, con base 1.000. E05: reserva 300 de 1.000 y devuelve capital más 60 una sola vez. E09: A=1.000/B=600 termina 960/640. E10: 1.000 -> 950 -> 1.140. E11 protege una sola E08 o E13 y jamás una cuota. E14: base 1.000, desembolso 300 y devolución fija 330 en n+2; fondos insuficientes conserva deuda, no cobra parcial. E15: par +20%, impar -10%.

Probar deshacer un préstamo antes y después de una cuota; deshacer un inicio con cobro y turno perdido; restaurar seguro consumido; cero con y sin contratos; banco insuficiente; reversión repetida; todos los cambios visibles en ranking y feed en tiempo real. No reemplazar pruebas existentes: ampliar la batería.


## Catálogo P01-P15: seed privado para el banco

Las consignas y títulos son públicos; respuestas y fuentes de validación son campos protegidos por rol. No enviar todo este objeto a estudiantes.

### P01 - De la naturaleza

Consigna: ¿A qué sector pertenecen la agricultura, la pesca y la minería? Explicá qué tienen en común.

Respuesta del banco: Primario: obtienen recursos de la naturaleza.

Fuente: Registro, p. 1

### P02 - Transformar

Consigna: Una fábrica convierte leche en yogur. ¿A qué sector pertenece esa actividad y por qué?

Respuesta del banco: Secundario: transforma una materia prima en un bien elaborado.

Fuente: Registro, p. 1

### P03 - Conectar

Consigna: Un camión lleva yogures al supermercado, que los vende. ¿A qué sector pertenecen ambas actividades?

Respuesta del banco: Terciario: transporte y comercio son servicios de distribución y venta.

Fuente: Registro, p. 1

### P04 - Conocimiento

Consigna: Un equipo investiga una nueva técnica de conservación. ¿Qué sector representa en la clasificación de cinco sectores?

Respuesta del banco: Cuaternario: genera conocimiento e innovación.

Fuente: Registro, p. 1

### P05 - Decidir

Consigna: La alta dirección define la estrategia de una empresa. ¿Qué sector representa según el registro?

Respuesta del banco: Quinario: decisiones de alto nivel. La división en cinco sectores no es universal.

Fuente: Registro, p. 1

### P06 - Mercado digital

Consigna: En una tienda virtual, ¿quién es oferente y quién es demandante? ¿Es necesario un local físico para que exista mercado?

Respuesta del banco: Oferente: quien vende. Demandante: quien desea comprar. No: el mercado puede ser físico o virtual.

Fuente: Registro, p. 1

### P07 - Mercado abierto

Consigna: Muchos vendedores ofrecen un producto homogéneo, con información amplia y entrada fácil. ¿Qué estructura describe?

Respuesta del banco: Competencia perfecta. Ningún participante controla por sí solo el precio.

Fuente: Registro, p. 2

### P08 - Un solo vendedor

Consigna: Hay un único oferente, fuertes barreras de entrada y pocos sustitutos. ¿Qué estructura es y quién concentra poder?

Respuesta del banco: Monopolio: el vendedor concentra poder de mercado.

Fuente: Registro, p. 2

### P09 - Pocos competidores

Consigna: Tres empresas dominan la oferta y cada una observa las decisiones de las otras. ¿Qué estructura representa?

Respuesta del banco: Oligopolio: pocos oferentes cuyas decisiones afectan a los demás.

Fuente: Registro, p. 2

### P10 - Un gran comprador

Consigna: Muchos productores venden a un comprador principal. ¿Qué estructura es y quién tiene más poder de negociación?

Respuesta del banco: Monopsonio: el comprador principal concentra poder de negociación.

Fuente: Registro, p. 2

### P11 - Ser diferente

Consigna: Muchos comercios compiten con productos diferenciados por diseño y atención. ¿Qué estructura representa?

Respuesta del banco: Competencia monopolística: numerosos oferentes con productos diferenciados.

Fuente: Registro, p. 2

### P12 - Nicho y sector

Consigna: Una fábrica produce ropa para ciclistas urbanos. Identificá el sector de fabricación y el nicho al que apunta.

Respuesta del banco: Sector secundario; nicho: ciclistas urbanos. El nicho no permite deducir por sí solo la estructura del mercado.

Fuente: Registro, pp. 1-2

### P13 - Presupuesto

Consigna: Un equipo recibe 1.000 TDL y gasta 650 TDL. ¿Cuánto le queda? Si reserva 200 TDL, ¿cuánto puede gastar todavía?

Respuesta del banco: Quedan 350 TDL en total; 200 reservados y 150 disponibles. Reservar no equivale a gastar.

Fuente: Programa, p. 5, unidad 5; ejercicio original

### P14 - Elegir tiene costo

Consigna: Solo podés elegir entre ir al cine o ir a un partido. Elegís el cine. ¿Cuál es el costo de oportunidad?

Respuesta del banco: La alternativa a la que renunciás: ir al partido (el beneficio de la mejor alternativa descartada).

Fuente: Programa, p. 4, unidad 1; aplicación didáctica

### P15 - Proyecto en marcha

Consigna: Antes de organizar una feria estudiantil, nombrá tres decisiones que permitan planificar el proyecto.

Respuesta del banco: Se aceptan tres decisiones pertinentes: objetivo, recursos y presupuesto, tareas y responsables, cronograma o evaluación de riesgos/resultados.

Fuente: Programa, pp. 3 y 5-6, unidad 6; aplicación didáctica


## Catálogo E01-E15: efectos obligatorios

En E02/E09/E12 debe haber otro equipo activo; si no, devolver la tarjeta y extraer otra. Montos cero se registran sin inventar un mínimo. Mantener reglas y ejemplos separados de las consignas públicas.

### E01 - Inversión a futuro

Consigna: Perdés tus próximos 2 turnos. Al comenzar el tercero, el banco te paga el 15% del saldo que tenías al tomar esta tarjeta.

Regla del motor: Fijar B al activar, marcar dos turnos sin lanzamiento y pagar 0,15B al inicio del tercer turno propio. No se descuenta ni inmoviliza capital: es una bonificación lúdica por esperar.

Objetivo: Costo de oportunidad y espera.

Ejemplo de prueba: Con B=1.000, premio diferido 150 TDL. Si no hubo otros movimientos, terminás con 1.150.

### E02 - Préstamo entre equipos

Consigna: Elegí otro equipo y prestale el 40% de tu saldo. Cobrá 3 cuotas: cada una será el 20% del saldo disponible del deudor al inicio de sus próximos 3 turnos.

Regla del motor: Transferir 0,40B del prestamista al deudor. Cada cuota usa el disponible del deudor justo antes de cobrarla. Tres cuotas extinguen el contrato: no se devuelve además el principal ni se garantiza recuperar lo prestado. Una cuota calculada en cero cuenta como cuota cumplida. Registrar consentimiento de reglas al iniciar partida, no exigir nueva negociación para esta tarjeta.

Objetivo: Crédito, riesgo y pagos variables.

Ejemplo de prueba: Prestamista 1.000, deudor 600: préstamo 400; deudor queda en 1.000. Sin otros movimientos paga 200, 160 y 128: cobro total 488. Prestamista termina con 1.088 y deudor con 512.

### E03 - Inflación

Consigna: La inflación reduce tu poder de compra. Como efecto del juego, pagá al banco el 10% de tu saldo.

Regla del motor: Debitar 0,10B y acreditar al banco. Aclarar: la inflación no retira automáticamente dinero nominal; este descuento es una simplificación del juego. Una suba de precios del 10% tampoco equivale exactamente a una caída del 10% del poder de compra.

Objetivo: Distinguir dinero nominal y poder adquisitivo.

Ejemplo de prueba: Con 1.000, pagás 100 y conservás 900 TDL.

### E04 - Tres dados, una decisión

Consigna: Tirá el dado 3 veces y sumá. Si el total es 6 o menos, pagá al banco el 20% de tu saldo. Si es mayor, el banco te paga un 30%.

Regla del motor: Registrar tres enteros de 1 a 6; calcular sobre B previo a las tiradas. Solo una rama. No altera el movimiento de la ficha. Con dados justos, 20 de 216 resultados suman 6 o menos; la regla favorece la ganancia y no representa una inversión equilibrada.

Objetivo: Probabilidad y riesgo.

Ejemplo de prueba: B=1.000: suma 6 deja 800; suma 7 deja 1.300.

### E05 - Ahorro programado

Consigna: Reservá el 30% de tu saldo hasta el inicio de tu próximo turno. Entonces recuperás ese capital y el banco agrega un 20% del monto reservado.

Regla del motor: Mover 0,30B a reserva; al próximo inicio propio liberar capital y acreditar interés fijo 0,20 del capital reservado. Sin turno perdido. El total no baja al reservar.

Objetivo: Ahorro, liquidez e interés.

Ejemplo de prueba: B=1.000: disponible 700 y reserva 300; al vencer se liberan 300 y se ganan 60; total 1.060.

### E06 - Contribución tributaria

Consigna: Pagá al banco el 12% de tu saldo por una contribución tributaria. El banco administra esos fondos durante la partida.

Regla del motor: Transferir 0,12B al banco. Tasa ficticia; el banco es contraparte lúdica, no una representación exacta del Estado.

Objetivo: Tributos y financiamiento colectivo.

Ejemplo de prueba: B=1.000: pago 120; saldo 880.

### E07 - Apoyo al emprendimiento

Consigna: Tu proyecto recibe un apoyo. El banco te entrega el 25% de tu saldo actual. No debés devolverlo.

Regla del motor: Banco acredita 0,25B sin deuda ni cuotas. Si B=0, el apoyo es cero; el docente puede hacer un rescate separado y auditado.

Objetivo: Diferenciar un apoyo no reembolsable de un préstamo.

Ejemplo de prueba: B=1.000: ganás 250; saldo 1.250.

### E08 - Reparación urgente

Consigna: Una máquina se avería. Pagá al banco el 15% de tu saldo para repararla. Podés seguir jugando.

Regla del motor: Transferir 0,15B al banco. No perder turno. Es uno de los dos eventos cubiertos por el seguro E11.

Objetivo: Costos imprevistos y reserva de liquidez.

Ejemplo de prueba: B=1.000: pago 150; saldo 850.

### E09 - Intercambio comercial

Consigna: Elegí otro equipo. Pagale el 10% de tu saldo y recibí el 10% del suyo. Calculen ambos importes antes de transferir.

Regla del motor: Dos flujos simultáneos en una transacción atómica sobre las bases previas de ambos equipos. Sin banco. No calcular el segundo porcentaje después del primer pago.

Objetivo: Transferencias y bases porcentuales distintas.

Ejemplo de prueba: A=1.000 y B=600: A entrega 100 y recibe 60. Quedan A=960, B=640.

### E10 - Campaña de ventas

Consigna: Invertís en publicidad: pagá al banco el 5% de tu saldo. Luego, el banco te paga el 20% del saldo que te quedó.

Regla del motor: Aplicar débito 0,05B y luego crédito 0,20 del saldo disponible resultante; guardar ambas bases en una operación compuesta.

Objetivo: Porcentajes sucesivos y costo-beneficio.

Ejemplo de prueba: B=1.000: pagás 50, quedan 950; cobrás 190 y terminás con 1.140.

### E11 - Seguro del negocio

Consigna: Podés pagar al banco el 5% de tu saldo. Si lo hacés, evitás la próxima pérdida por Reparación urgente (E08) o Fraude (E13). Se usa una sola vez.

Regla del motor: Ofrecer aceptar o rechazar. Si acepta, cobrar 0,05B y activar protección sin vencimiento dentro de esta partida. Cubre toda la próxima pérdida de E08 o E13, luego se consume. No acumular seguros: si ya tiene uno, conservarlo y no cobrar otra prima. No cubre inflación, impuestos, deudas ni otras tarjetas.

Objetivo: Prima, cobertura y decisión bajo riesgo.

Ejemplo de prueba: B=1.000: prima 50, saldo 950; si luego sale E08, evita 142,50 de pérdida y consume el seguro.

### E12 - Cooperación solidaria

Consigna: Elegí otro equipo y transferile el 10% de tu saldo. Ese equipo recibe el dinero sin obligación de devolverlo.

Regla del motor: Debitar 0,10B del actor y acreditar al elegido. No crear contrato de préstamo ni restitución posterior.

Objetivo: Cooperación y diferencia entre donación y crédito.

Ejemplo de prueba: A=1.000 y B=600: A queda con 900 y B con 700.

### E13 - Fraude comercial

Consigna: Una oferta engañosa te provoca una pérdida. Pagá al banco el 20% de tu saldo. Si tenés el seguro E11 activo, usalo y no pagues.

Regla del motor: Si hay seguro activo, consumirlo y registrar pérdida evitada sin transferencia. Si no, transferir 0,20B al banco. El banco registra la pérdida simulada, no actúa como defraudador.

Objetivo: Riesgo de fraude y cobertura.

Ejemplo de prueba: Sin seguro y B=1.000: saldo 800. Con seguro: no hay débito y la póliza se consume.

### E14 - Crédito del banco

Consigna: El banco te presta el 30% de tu saldo. Al inicio de tu segundo próximo turno, devolvé ese monto más un 10% de interés sobre el préstamo.

Regla del motor: Fijar capital C=0,30B; banco transfiere C. Programar pago C+0,10C al inicio propio n+2. No hay turno perdido. Si el disponible no alcanza, queda una deuda vencida por el importe completo, sin pago parcial ni nuevo interés automático; el banco decide luego cobro o ajuste auditado.

Objetivo: Capital prestado, deuda e interés.

Ejemplo de prueba: B=1.000: recibís 300 y quedás con 1.300. Deuda fija 330. Sin otros movimientos, luego quedan 970.

### E15 - Demanda cambiante

Consigna: Tirá el dado una vez. Si sale par, el banco te paga el 20% de tu saldo. Si sale impar, pagá al banco un 10%.

Regla del motor: Validar dado 1 a 6. Par: +0,20B; impar: -0,10B. Solo una rama; no mueve ficha. Es un modelo lúdico de demanda, no una predicción.

Objetivo: Incertidumbre en ventas y resultados.

Ejemplo de prueba: B=1.000: par deja 1.200; impar deja 900.
