import uuid
from datetime import datetime

from pydantic import BaseModel


class CoffeeOptionCreate(BaseModel):
    drink_type_id: uuid.UUID
    size_id: uuid.UUID
    milk_option_id: uuid.UUID | None = None
    sugar: int = 0
    notes: str | None = None
    is_default: bool = False
    display_order: int = 0


class CoffeeOptionUpdate(BaseModel):
    drink_type_id: uuid.UUID | None = None
    size_id: uuid.UUID | None = None
    milk_option_id: uuid.UUID | None = None
    sugar: int | None = None
    notes: str | None = None
    is_default: bool | None = None
    display_order: int | None = None


class CoffeeOptionResponse(BaseModel):
    id: uuid.UUID
    colleague_id: uuid.UUID
    drink_type_id: uuid.UUID
    drink_type_name: str | None = None
    size_id: uuid.UUID
    size_name: str | None = None
    size_abbreviation: str | None = None
    milk_option_id: uuid.UUID | None = None
    milk_option_name: str | None = None
    sugar: int
    notes: str | None
    is_default: bool
    display_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ColleagueCreate(BaseModel):
    name: str
    usually_in: bool = True
    display_order: int = 0


class ColleagueUpdate(BaseModel):
    name: str | None = None
    usually_in: bool | None = None
    display_order: int | None = None


class ColleagueResponse(BaseModel):
    id: uuid.UUID
    name: str
    usually_in: bool
    display_order: int
    is_active: bool
    coffee_options: list[CoffeeOptionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
