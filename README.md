# Audacity · Sistema Informático de Gestión de Partidas Escolares (2.0)

Sistema informático completo, autocontenido y dockerizado para la gestión de partidas presenciales del juego escolar **Audacity** (Economía para Jóvenes), en español rioplatense.

El sistema permite la participación simultánea de hasta cinco equipos y el docente/banco desde cualquier navegador en red local (LAN) o en el mismo equipo, con dinero ficticio expresado en **TDL**, contabilidad de partida doble en centésimos enteros, motor de turnos y contratos pluriturnos, sincronización en tiempo real vía WebSockets y cero dependencias de servicios en la nube o CDNs externos (100% offline).

---

## 1. Arquitectura y Componentes

Docker Compose organiza la plataforma en 4 servicios:

- **`db`**: PostgreSQL 16 Alpine con persistencia en volumen nombrado `audacity_db_data`. Puerto no publicado al host por seguridad.
- **`migrate`**: Proceso one-shot que aguarda la salud de la base de datos y aplica las migraciones Alembic de forma estricta.
- **`api`**: Backend FastAPI (Python 3.12) con motor de reglas atómico, contabilidad de partida doble y WebSockets. Corre bajo usuario no-root.
- **`web`**: Servidor Nginx que entrega los activos compilados de React + TypeScript (Vite) y actúa como proxy inverso para `/api/` y `/ws/`.

---

## 2. Despliegue Ultrarrápido en ZimaOS / CasaOS (Recomendado)

Audacity está optimizado para ejecutarse en **ZimaOS** y **CasaOS** en el puerto **3003**, con imagen ligera precompilada y persistencia de datos automática:

### Opción A: Importar `docker-compose.yml` en ZimaOS / CasaOS
1. En el panel de **ZimaOS / CasaOS**, haz clic en **App Store** -> **Instalar aplicación personalizada** (Custom Install).
2. Haz clic en el ícono de **Importar** (arriba a la derecha) y pega el contenido del archivo `docker-compose.yml` de este repositorio:
```yaml
name: audacity-contador
version: '3.8'

services:
  audacity:
    image: ghcr.io/wadewatts9/audacity_contador2026:latest
    container_name: audacity-contador
    restart: unless-stopped
    ports:
      - "3003:3003"
    environment:
      - PORT=3003
      - TIMEZONE=America/Montevideo
      - SECRET_KEY=audacity_zimaos_secret_key_2026
    volumes:
      - ./data:/app/data
```
3. Haz clic en **Instalar**. ¡Listo! El sistema quedará disponible en `http://<IP-DE-TU-ZIMAOS>:3003`.

---

## 3. Puesta en Marcha en PC Local (Windows / Linux / macOS)

### Requisitos
- Docker Desktop instalado y corriendo en el equipo.
- Navegador moderno (Chrome, Edge, Firefox, Safari).

### Paso 1: Configurar variables de entorno (opcional)
El sistema ya se encuentra preconfigurado en el puerto **`3003`**:
```bash
cp .env.example .env
```

### Paso 2: Levantar los contenedores
Ejecutar en la raíz del proyecto:
```bash
docker compose up -d
```

### Paso 3: Acceder al sistema
- **En el equipo local**: Abrir el navegador en `http://127.0.0.1:3003` o `http://localhost:3003`.
- **En red local del aula (LAN)**: Compartir la URL `http://<IP_LOCAL_DOCENTE>:3003` a los estudiantes.

---

## 4. Modo Aula en Red Local (LAN)

Para que los estudiantes accedan desde sus celulares, tablets o laptops conectadas al Wi-Fi del aula:

1. **Descubrir la IP local del equipo docente**:
   - En Windows (PowerShell):
     ```powershell
     ipconfig
     ```
     Buscar la `Dirección IPv4` del adaptador Wi-Fi o Ethernet (ejemplo: `192.168.1.45`).
   - En Linux / macOS:
     ```bash
     ip a   # o ifconfig
     ```
2. **Permitir el puerto 8080 en el Firewall de Windows (sin desactivarlo)**:
   Ejecutar en PowerShell como Administrador:
   ```powershell
   New-NetFirewallRule -DisplayName "Audacity Aula 8080" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
   ```
3. **Acceso de los estudiantes**:
   Los estudiantes ingresan en su navegador a:
   `http://192.168.1.45:8080` (reemplazando por la IP del equipo docente).

---

## 4. Ejecución de Pruebas Automatizadas

La suite de pruebas cubre los 15 retos económicos (E01-E15), el avance de turnos, cobranza de cuotas variables y fijas, reversiones («Deshacer»), puesta a cero y seguros:

### Dentro del contenedor backend:
```bash
docker compose run --rm api pytest tests -v
```

### O localmente en Python (si cuenta con entorno local):
```powershell
cd backend
python -m pytest tests -v
```

---

## 5. Respaldos y Restauración (Backup & Restore)

Los datos de las partidas sobreviven al reinicio de los contenedores gracias al volumen nombrado `audacity_db_data`. `docker compose down` conserva la información. **No use `docker compose down -v` a menos que desee borrar intencionalmente toda la base de datos.**

### Crear un Respaldo consistente:
- **Windows PowerShell**:
  ```powershell
  .\scripts\backup.ps1
  ```
- **Linux / macOS**:
  ```bash
  ./scripts/backup.sh
  ```
El archivo `.sql` se guardará en la carpeta `./backups/`.

### Restaurar un Respaldo:
- **Windows PowerShell**:
  ```powershell
  .\scripts\restore.ps1 -BackupFile .\backups\audacity_backup_20260913_220000.sql
  ```
- **Linux / macOS**:
  ```bash
  ./scripts/restore.sh ./backups/audacity_backup_20260913_220000.sql
  ```

---

## 6. Comandos Operativos Frecuentes

| Acción | Comando |
|---|---|
| Iniciar contenedores | `docker compose up -d` |
| Ver registros (logs) | `docker compose logs -f` |
| Logs del backend API | `docker compose logs -f api` |
| Detener contenedores (conserva datos) | `docker compose down` |
| Reiniciar servicio | `docker compose restart api` |
| Exportar auditoría | Disponible desde el botón "Exportar CSV Seguro" en el panel docente |
