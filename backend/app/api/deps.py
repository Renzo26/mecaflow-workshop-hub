import uuid

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import AuthError, decode_token
from app.services.redis_service import RedisService

from typing import AsyncGenerator

_bearer = HTTPBearer()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


async def get_redis_service(request: Request) -> RedisService:
    redis: Redis = request.app.state.redis
    return RedisService(redis)


async def get_workshop_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> uuid.UUID:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise AuthError("Token inválido")
        return uuid.UUID(payload["workshop_id"])
    except (JWTError, AuthError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
