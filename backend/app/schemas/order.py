import uuid
from datetime import datetime

from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    colleague_id: uuid.UUID
    coffee_option_id: uuid.UUID


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    colleague_id: uuid.UUID
    colleague_name: str | None = None
    coffee_option_id: uuid.UUID
    drink_type_name: str
    size_name: str
    size_abbreviation: str
    milk_option_name: str | None
    sugar: int
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConsolidatedItem(BaseModel):
    count: int
    drink_type_name: str
    size_name: str
    size_abbreviation: str
    milk_option_name: str | None
    sugar: int
    notes: str | None
    display_text: str


class OrderResponse(BaseModel):
    id: uuid.UUID
    share_token: str
    created_by: uuid.UUID
    created_at: datetime
    items: list[OrderItemResponse] = []
    consolidated: list[ConsolidatedItem] = []

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    id: uuid.UUID
    share_token: str
    created_at: datetime
    item_count: int

    model_config = {"from_attributes": True}


class OrderUpdateRequest(BaseModel):
    items: list[OrderItemCreate]


class StatsOverview(BaseModel):
    total_orders: int
    total_coffees: int
    busiest_day: str | None
    orders_this_week: int
    orders_this_month: int


class DrinkStat(BaseModel):
    drink_name: str
    count: int


class ColleagueStat(BaseModel):
    colleague_name: str
    order_count: int
    favourite_drink: str | None
