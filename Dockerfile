# Multi-stage Dockerfile: Frontend Builder + Python Backend Runtime
# Etapa 1: Construcción del Frontend React + Vite
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Etapa 2: Runtime ligero de Python 3.12
FROM python:3.12-slim AS runtime

WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requerimientos del backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del backend y configuración
COPY backend/app ./app
COPY backend/alembic.ini ./

# Copiar build del frontend generado en Etapa 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Crear directorio para persistencia de datos (SQLite / logs / backups)
RUN mkdir -p /app/data

# Variables de entorno predeterminadas
ENV PORT=3003 \
    HOST=0.0.0.0 \
    DATABASE_URL=sqlite+aiosqlite:////app/data/audacity.db \
    STATIC_DIR=/app/frontend/dist \
    TIMEZONE=America/Montevideo \
    SECRET_KEY=audacity_production_secret_key_2026

EXPOSE 3003

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:/api/health || exit 1

# Comando de inicio: uvicorn sirviendo API, WebSockets y Frontend en el puerto 3003
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port "]
