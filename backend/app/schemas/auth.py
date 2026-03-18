import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr


class VerifyRequest(BaseModel):
    token: str


class UserTeamMembership(BaseModel):
    team_id: uuid.UUID
    team_name: str
    role: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None = None
    teams: list[UserTeamMembership] = []
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    message: str
