import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Audacity - Economía para Jóvenes"
    VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Secret Key for JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "audacity_super_secret_production_key_change_me_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Database configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "audacity_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "audacity_password_secure_2026")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "audacity_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # Async DB URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql+asyncpg://{os.getenv('POSTGRES_USER', 'audacity_user')}:{os.getenv('POSTGRES_PASSWORD', 'audacity_password_secure_2026')}@{os.getenv('POSTGRES_HOST', 'db')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'audacity_db')}"
    )
    
    # Sync DB URL for Alembic migrations
    SYNC_DATABASE_URL: str = os.getenv(
        "SYNC_DATABASE_URL",
        f"postgresql://{os.getenv('POSTGRES_USER', 'audacity_user')}:{os.getenv('POSTGRES_PASSWORD', 'audacity_password_secure_2026')}@{os.getenv('POSTGRES_HOST', 'db')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'audacity_db')}"
    )
    
    # Timezone
    TIMEZONE: str = "America/Montevideo"
    
    # Network / Host
    APP_PORT: int = int(os.getenv("APP_PORT", "8080"))
    BIND_ADDRESS: str = os.getenv("BIND_ADDRESS", "0.0.0.0")
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
