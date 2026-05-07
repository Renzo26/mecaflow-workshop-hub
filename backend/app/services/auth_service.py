import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.user import User, UserRole
from app.models.workshop import Workshop

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_settings = get_settings()

ALGORITHM = "HS256"


class ConflictError(Exception):
    """Recurso já existe (HTTP 409)."""


class AuthError(Exception):
    """Credenciais inválidas ou token expirado (HTTP 401)."""


class ValidationError(Exception):
    """Entrada inválida (HTTP 422)."""


def hash_password(plain: str) -> str:
    if len(plain.encode("utf-8")) > 72:
        raise ValidationError("A senha não pode ter mais de 72 caracteres.")
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def _make_token(data: dict, ttl_ms: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(milliseconds=ttl_ms)
    return jwt.encode({**data, "exp": expire}, _settings.jwt_secret, algorithm=ALGORITHM)


def create_access_token(user: User) -> str:
    return _make_token(
        {
            "sub": str(user.id),
            "workshop_id": str(user.workshop_id),
            "role": user.role.value,
            "name": user.name,
            "type": "access",
        },
        _settings.jwt_access_ttl_ms,
    )


def create_refresh_token(user: User) -> str:
    return _make_token(
        {"sub": str(user.id), "type": "refresh"},
        _settings.jwt_refresh_ttl_ms,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, _settings.jwt_secret, algorithms=[ALGORITHM])


class AuthService:
    async def register(
        self,
        db: AsyncSession,
        workshop_name: str,
        name: str,
        email: str,
        password: str,
    ) -> tuple[User, Workshop]:
        existing = await db.scalar(select(User).where(User.email == email))
        if existing:
            raise ConflictError("E-mail já cadastrado")

        workshop = Workshop(name=workshop_name)
        db.add(workshop)
        await db.flush()

        user = User(
            workshop_id=workshop.id,
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
        )
        db.add(user)
        await db.flush()
        return user, workshop

    async def login(self, db: AsyncSession, email: str, password: str) -> tuple[User, Workshop]:
        user = await db.scalar(
            select(User)
            .where(User.email == email, User.is_active == True)  # noqa: E712
            .options(selectinload(User.workshop))
        )
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("E-mail ou senha inválidos")
        return user, user.workshop

    async def refresh(self, db: AsyncSession, refresh_token: str) -> tuple[User, Workshop]:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError()
            user_id = uuid.UUID(payload["sub"])
        except (JWTError, ValueError, KeyError):
            raise AuthError("Token inválido")

        user = await db.scalar(
            select(User)
            .where(User.id == user_id, User.is_active == True)  # noqa: E712
            .options(selectinload(User.workshop))
        )
        if not user:
            raise AuthError("Usuário não encontrado")
        return user, user.workshop

    async def get_current_user(self, db: AsyncSession, token: str) -> User:
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                raise AuthError("Token inválido")
            user_id = uuid.UUID(payload["sub"])
        except (JWTError, ValueError, KeyError):
            raise AuthError("Token inválido")

        user = await db.scalar(
            select(User)
            .where(User.id == user_id, User.is_active == True)  # noqa: E712
            .options(selectinload(User.workshop))
        )
        if not user:
            raise AuthError("Usuário não encontrado")
        return user


auth_service = AuthService()
