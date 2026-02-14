import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user, require_admin
from app.models.menu import DrinkType, MilkOption, Size
from app.schemas.menu import (
    DrinkTypeCreate,
    DrinkTypeResponse,
    DrinkTypeUpdate,
    MilkOptionCreate,
    MilkOptionResponse,
    MilkOptionUpdate,
    SizeCreate,
    SizeResponse,
    SizeUpdate,
)

router = APIRouter(prefix="/menu", tags=["menu"])


# --- Drink Types ---
@router.get("/drink-types", response_model=list[DrinkTypeResponse])
async def list_drink_types(
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(DrinkType)
        .where(DrinkType.is_active == True)  # noqa: E712
        .order_by(DrinkType.display_order, DrinkType.name)
    )
    return result.scalars().all()


@router.post("/drink-types", response_model=DrinkTypeResponse, status_code=201)
async def create_drink_type(
    data: DrinkTypeCreate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    item = DrinkType(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.put("/drink-types/{item_id}", response_model=DrinkTypeResponse)
async def update_drink_type(
    item_id: uuid.UUID,
    data: DrinkTypeUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(DrinkType).where(DrinkType.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Drink type not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/drink-types/{item_id}")
async def delete_drink_type(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(DrinkType).where(DrinkType.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Drink type not found")
    item.is_active = False
    await db.flush()
    return {"message": "Drink type deactivated"}


# --- Sizes ---
@router.get("/sizes", response_model=list[SizeResponse])
async def list_sizes(
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Size)
        .where(Size.is_active == True)  # noqa: E712
        .order_by(Size.display_order, Size.name)
    )
    return result.scalars().all()


@router.post("/sizes", response_model=SizeResponse, status_code=201)
async def create_size(
    data: SizeCreate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    item = Size(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.put("/sizes/{item_id}", response_model=SizeResponse)
async def update_size(
    item_id: uuid.UUID,
    data: SizeUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(Size).where(Size.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Size not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/sizes/{item_id}")
async def delete_size(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(Size).where(Size.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Size not found")
    item.is_active = False
    await db.flush()
    return {"message": "Size deactivated"}


# --- Milk Options ---
@router.get("/milk-options", response_model=list[MilkOptionResponse])
async def list_milk_options(
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(MilkOption)
        .where(MilkOption.is_active == True)  # noqa: E712
        .order_by(MilkOption.display_order, MilkOption.name)
    )
    return result.scalars().all()


@router.post("/milk-options", response_model=MilkOptionResponse, status_code=201)
async def create_milk_option(
    data: MilkOptionCreate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    item = MilkOption(**data.model_dump())
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.put("/milk-options/{item_id}", response_model=MilkOptionResponse)
async def update_milk_option(
    item_id: uuid.UUID,
    data: MilkOptionUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(MilkOption).where(MilkOption.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Milk option not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/milk-options/{item_id}")
async def delete_milk_option(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(MilkOption).where(MilkOption.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Milk option not found")
    item.is_active = False
    await db.flush()
    return {"message": "Milk option deactivated"}
