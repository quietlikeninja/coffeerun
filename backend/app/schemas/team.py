import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class TeamCreate(BaseModel):
    name: str


class TeamUpdate(BaseModel):
    name: str | None = None


class TeamResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_by: uuid.UUID
    is_active: bool
    member_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email: str
    display_name: str | None = None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamMemberUpdate(BaseModel):
    role: str


class InviteCreate(BaseModel):
    email: EmailStr
    role: str
    colleague_id: uuid.UUID | None = None


class InviteResponse(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    email: str
    role: str
    colleague_id: uuid.UUID | None = None
    invited_by: uuid.UUID
    expires_at: datetime
    accepted: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteAccept(BaseModel):
    token: str
