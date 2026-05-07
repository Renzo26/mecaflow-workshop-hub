from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.auth import LoginIn, RefreshIn, RegisterIn, TokenOut, UserOut, WorkshopOut
from app.services.auth_service import (
    AuthError,
    ConflictError,
    ValidationError,
    auth_service,
    create_access_token,
    create_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer()


def _build_token_out(user, workshop) -> TokenOut:
    return TokenOut(
        access_token=create_access_token(user),
        refresh_token=create_refresh_token(user),
        user=UserOut.model_validate(user),
        workshop=WorkshopOut.model_validate(workshop),
    )


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterIn, db: AsyncSession = Depends(get_session)):
    try:
        user, workshop = await auth_service.register(
            db, body.workshop_name, body.name, body.email, body.password
        )
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return _build_token_out(user, workshop)


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_session)):
    try:
        user, workshop = await auth_service.login(db, body.email, body.password)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return _build_token_out(user, workshop)


@router.post("/refresh", response_model=TokenOut)
async def refresh(body: RefreshIn, db: AsyncSession = Depends(get_session)):
    try:
        user, workshop = await auth_service.refresh(db, body.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return _build_token_out(user, workshop)


@router.get("/me", response_model=UserOut)
async def me(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_session),
):
    try:
        user = await auth_service.get_current_user(db, credentials.credentials)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return UserOut.model_validate(user)
