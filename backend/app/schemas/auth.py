from pydantic import BaseModel, Field
from typing import Optional

class LoginRequest(BaseModel):
    username: str = Field(..., description="Nombre de usuario (ej. admin_docente, contador_gallo)")
    password: str = Field(..., description="Contraseña de acceso")
    game_code: Optional[str] = Field(None, description="Código de partida (opcional para admin)")

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    display_name: str
    token_symbol: Optional[str] = None
    token_color: Optional[str] = None
    account_id: Optional[int] = None
    game_id: Optional[int] = None
    game_code: Optional[str] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class InitialAdminCreate(BaseModel):
    username: str = Field("admin_docente", min_length=4)
    password: str = Field(..., min_length=8)
    display_name: str = Field("Docente / Banco", min_length=2)
