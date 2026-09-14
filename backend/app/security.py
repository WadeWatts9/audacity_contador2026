import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_secure_password(length: int = 14) -> str:
    """Generate a high-entropy random password with at least 12 characters."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Ensure at least one lowercase, uppercase, digit, and symbol
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%&*")
    ]
    password += [secrets.choice(alphabet) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(password)
    return "".join(password)

def generate_simple_team_password(animal: str = "equipo") -> str:
    """
    Genera contraseñas memorables para estudiantes con PIN numérico aleatorio de 4 dígitos único.
    Ejemplo: contadorgallo2026, contadorestrella1456, contadorleon4829
    """
    clean_animal = animal.lower().strip().replace("contador_", "").replace("_contador", "")
    pin = secrets.randbelow(9000) + 1000  # 4 dígitos aleatorios (1000 a 9999)
    return f"contador{clean_animal}{pin}"

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
