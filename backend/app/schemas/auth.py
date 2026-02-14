import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr


class VerifyRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
