from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import auth, games, bank, turns, cards, teams, ws

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear tablas si no existen (idempotente)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
