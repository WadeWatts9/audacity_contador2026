import asyncio
import sys
import argparse
import getpass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.security import hash_password, generate_secure_password

async def create_initial_admin(username: str = "admin_docente", password: str = None, display_name: str = "Docente / Banco"):
    async with AsyncSessionLocal() as session:
        # Verificar si ya existe
        res = await session.execute(select(User).where(User.username == username))
        existing = res.scalar_one_or_none()
        if existing:
            print(f"[INFO] El usuario docente '{username}' ya existe. No se modifican sus credenciales.")
            return

        if not password:
            password = generate_secure_password(16)
            is_generated = True
        else:
            is_generated = False

        admin = User(
            username=username,
            password_hash=hash_password(password),
            role="admin_docente",
            display_name=display_name,
            token_symbol="🏦",
            token_color="#db3448"
        )
        session.add(admin)
        await session.commit()

        print("==================================================")
        print("  USUARIO DOCENTE / BANCO CREADO CON ÉXITO")
        print("==================================================")
        print(f"  Usuario:      {username}")
        if is_generated:
            print(f"  Contraseña:   {password}")
            print("  (Guarde esta contraseña en un lugar seguro)")
        else:
            print("  Contraseña:   [Configurada manualmente]")
        print("==================================================")

def main():
    parser = argparse.ArgumentParser(description="Crear usuario inicial docente para Audacity")
    parser.add_argument("--username", default="admin_docente", help="Nombre de usuario del docente")
    parser.add_argument("--password", default=None, help="Contraseña (si se omite, se genera una aleatoria)")
    parser.add_argument("--name", default="Docente / Banco", help="Nombre visible")
    args = parser.parse_args()

    asyncio.run(create_initial_admin(args.username, args.password, args.name))

if __name__ == "__main__":
    main()
