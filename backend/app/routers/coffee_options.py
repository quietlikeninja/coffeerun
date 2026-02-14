import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, require_admin
from app.models.coffee_option import CoffeeOption
from app.routers.colleagues import _coffee_option_to_response
from app.schemas.colleague import CoffeeOptionResponse, CoffeeOptionUpdate

router = APIRouter(prefix="/coffee-options", tags=["coffee-options"])


@router.put("/{option_id}", response_model=CoffeeOptionResponse)
async def update_coffee_option(
    option_id: uuid.UUID,
    data: CoffeeOptionUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(CoffeeOption).where(CoffeeOption.id == option_id))
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=404, detail="Coffee option not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(option, field, value)

    await db.flush()
    await db.refresh(option)
    return _coffee_option_to_response(option)


@router.delete("/{option_id}")
async def delete_coffee_option(
    option_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(CoffeeOption).where(CoffeeOption.id == option_id))
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=404, detail="Coffee option not found")

    await db.delete(option)
    await db.flush()
    return {"message": "Coffee option deleted"}


@router.put("/{option_id}/set-default", response_model=CoffeeOptionResponse)
async def set_default_coffee_option(
    option_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(CoffeeOption).where(CoffeeOption.id == option_id))
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=404, detail="Coffee option not found")

    # Unset all defaults for this colleague
    sibling_result = await db.execute(
        select(CoffeeOption).where(CoffeeOption.colleague_id == option.colleague_id)
    )
    for sibling in sibling_result.scalars().all():
        sibling.is_default = False

    option.is_default = True
    await db.flush()
    await db.refresh(option)
    return _coffee_option_to_response(option)
