from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.account import Account
from app.models.game import Game
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.security import verify_password, create_access_token, oauth2_scheme, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    username: str = payload.get("sub")
    if not username:
        return None
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    return user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no provisto o sesión expirada.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no contiene sujeto.")
    
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario inactivo o inexistente.")
    return user

async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != "admin_docente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido: requiere rol docente / banco."
        )
    return current_user

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    raw_uname = data.username.strip().lower()
    possible_unames = {raw_uname}
    clean = raw_uname.replace("_", "").replace("-", "")
    if clean.startswith("contador"):
        animal = clean[8:]
        possible_unames.add(f"{animal}_contador")
        possible_unames.add(f"contador_{animal}")
        possible_unames.add(animal)
    elif clean.endswith("contador"):
        animal = clean[:-8]
        possible_unames.add(f"{animal}_contador")
        possible_unames.add(f"contador_{animal}")
        possible_unames.add(animal)
    else:
        possible_unames.add(f"{clean}_contador")
        possible_unames.add(f"contador_{clean}")

    query = select(User).where(User.username.in_(list(possible_unames)))
    result = await db.execute(query)
    user = result.scalars().first()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Verificá usuario y contraseña."
        )
    
    account_id = None
    game_id = None
    game_code = None
    
    if user.role == "equipo":
        acc_query = select(Account, Game).join(Game, Account.game_id == Game.id).where(Account.user_id == user.id)
        if data.game_code:
            acc_query = acc_query.where(Game.code == data.game_code.upper().strip())
        else:
            acc_query = acc_query.where(Game.status == "activa").order_by(Game.id.desc())
        
        acc_res = await db.execute(acc_query)
        row = acc_res.first()

        # Fallback 1: game_code provided but no match — try any active game for this user
        if not row:
            fallback_active = (
                select(Account, Game)
                .join(Game, Account.game_id == Game.id)
                .where(Account.user_id == user.id, Game.status == "activa")
                .order_by(Game.id.desc())
            )
            fb_res = await db.execute(fallback_active)
            row = fb_res.first()

        # Fallback 2: no active game — try the most recent game of any status
        if not row:
            fallback_any = (
                select(Account, Game)
                .join(Game, Account.game_id == Game.id)
                .where(Account.user_id == user.id)
                .order_by(Game.id.desc())
            )
            fb2_res = await db.execute(fallback_any)
            row = fb2_res.first()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró una partida activa para este equipo. El docente debe iniciar la partida."
            )
        account, game = row[0], row[1]
        account_id = account.id
        game_id = game.id
        game_code = game.code

    elif user.role == "admin_docente":
        game = None
        if data.game_code:
            g_res = await db.execute(select(Game).where(Game.code == data.game_code.upper().strip()))
            game = g_res.scalar_one_or_none()
        else:
            g_res = await db.execute(select(Game).where(Game.status == "activa").order_by(Game.id.desc()))
            game = g_res.scalar_one_or_none()
            if not game:
                # Generar automáticamente una partida corta si el admin ingresa sin salas activas
                from app.routers.games import create_game_core
                from app.schemas.game import GameCreate
                game, _ = await create_game_core(
                    db=db,
                    admin_user=user,
                    data=GameCreate(
                        name="Partida Audacity",
                        profile="genially",
                        initial_team_balance=1000000,
                        initial_bank_balance=5000000
                    )
                )
        if game:
            game_id = game.id
            game_code = game.code

    access_token = create_access_token(data={
        "sub": user.username,
        "role": user.role,
        "user_id": user.id,
        "account_id": account_id,
        "game_id": game_id,
        "game_code": game_code
    })
    
    user_resp = UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        display_name=user.display_name,
        token_symbol=user.token_symbol,
        token_color=user.token_color,
        account_id=account_id,
        game_id=game_id,
        game_code=game_code
    )
    
    return TokenResponse(access_token=access_token, token_type="bearer", user=user_resp)

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    account = None
    game_code = None
    game_id = None
    if current_user.role == "equipo":
        acc_res = await db.execute(
            select(Account, Game)
            .join(Game, Account.game_id == Game.id)
            .where(Account.user_id == current_user.id)
            .order_by(Game.id.desc())
        )
        row = acc_res.first()
        if row:
            account, game = row[0], row[1]
            game_code = game.code
            game_id = game.id
    elif current_user.role == "admin_docente":
        g_res = await db.execute(select(Game).where(Game.status == "activa").order_by(Game.id.desc()))
        game = g_res.scalar_one_or_none()
        if game:
            game_code = game.code
            game_id = game.id

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        display_name=current_user.display_name,
        token_symbol=current_user.token_symbol,
        token_color=current_user.token_color,
        account_id=account.id if account else None,
        game_id=game_id,
        game_code=game_code
    )

@router.post("/logout")
async def logout():
    return {"message": "Sesión cerrada correctamente."}
