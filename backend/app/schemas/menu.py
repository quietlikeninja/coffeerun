import uuid

from pydantic import BaseModel


class DrinkTypeCreate(BaseModel):
    name: str
    display_order: int = 0


class DrinkTypeUpdate(BaseModel):
    name: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class DrinkTypeResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class SizeCreate(BaseModel):
    name: str
    abbreviation: str
    display_order: int = 0


class SizeUpdate(BaseModel):
    name: str | None = None
    abbreviation: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class SizeResponse(BaseModel):
    id: uuid.UUID
    name: str
    abbreviation: str
    display_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class MilkOptionCreate(BaseModel):
    name: str
    display_order: int = 0


class MilkOptionUpdate(BaseModel):
    name: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class MilkOptionResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_order: int
    is_active: bool

    model_config = {"from_attributes": True}
