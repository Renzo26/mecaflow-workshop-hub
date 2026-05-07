import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr


class RegisterIn(BaseModel):
    workshop_name: str
    name: str
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class WorkshopOut(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    workshop_id: uuid.UUID

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut
    workshop: WorkshopOut
