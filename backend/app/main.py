from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import os
from sqlalchemy import select
from app.database import engine, Base, AsyncSessionLocal
from app.models.user import User
from app.security import hash_password
from app.routers import auth, games, bank, turns, cards, teams, ws

async def ensure_default_admin():
    try:
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(User).where(User.username == "admin_docente"))
            admin = res.scalar_one_or_none()
            if not admin:
                admin_pwd = os.getenv("ADMIN_PASSWORD", "DocenteAudacity2026!")
                admin = User(
                    username="admin_docente",
                    password_hash=hash_password(admin_pwd),
                    role="admin_docente",
                    display_name="Docente / Banco",
                    token_symbol="🏦",
                    token_color="#db3448"
                )
                session.add(admin)
                await session.commit()
                print("[INFO] Usuario docente 'admin_docente' creado automáticamente.")
    except Exception as e:
        print(f"[WARN] No se pudo inicializar admin automático: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas si no existen (idempotente)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Asegurar que el usuario docente exista en bases nuevas
    await ensure_default_admin()
    yield
    # Graceful shutdown: disponer engine
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware habilitado para uso en LAN sin restricciones de origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

# Incluir routers bajo prefijo /api
app.include_router(auth.router, prefix="/api")
app.include_router(games.router, prefix="/api")
app.include_router(bank.router, prefix="/api")
app.include_router(turns.router, prefix="/api")
app.include_router(cards.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(ws.router)

# Soporte para servir frontend React SPA cuando se ejecuta como contenedor único
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

STATIC_DIR = os.getenv("STATIC_DIR", "/app/frontend/dist")
if os.path.exists(STATIC_DIR):
    assets_path = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    cards_path = os.path.join(STATIC_DIR, "cards")
    if os.path.exists(cards_path):
        app.mount("/cards", StaticFiles(directory=cards_path), name="cards")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        target = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(target):
            return FileResponse(target)
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return {"service": settings.PROJECT_NAME, "status": "running"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3003))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
