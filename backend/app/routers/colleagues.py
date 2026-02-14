import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user, require_admin
from app.models.colleague import Colleague
from app.models.coffee_option import CoffeeOption
from app.schemas.colleague import (
    CoffeeOptionCreate,
    CoffeeOptionResponse,
    CoffeeOptionUpdate,
    ColleagueCreate,
    ColleagueResponse,
    ColleagueUpdate,
)

router = APIRouter(prefix="/colleagues", tags=["colleagues"])


def _coffee_option_to_response(opt: CoffeeOption) -> CoffeeOptionResponse:
    return CoffeeOptionResponse(
        id=opt.id,
        colleague_id=opt.colleague_id,
        drink_type_id=opt.drink_type_id,
        drink_type_name=opt.drink_type.name if opt.drink_type else None,
        size_id=opt.size_id,
        size_name=opt.size.name if opt.size else None,
        size_abbreviation=opt.size.abbreviation if opt.size else None,
        milk_option_id=opt.milk_option_id,
        milk_option_name=opt.milk_option.name if opt.milk_option else None,
        sugar=opt.sugar,
        notes=opt.notes,
        is_default=opt.is_default,
        display_order=opt.display_order,
        created_at=opt.created_at,
    )


def _colleague_to_response(colleague: Colleague) -> ColleagueResponse:
    return ColleagueResponse(
        id=colleague.id,
        name=colleague.name,
        usually_in=colleague.usually_in,
        display_order=colleague.display_order,
        is_active=colleague.is_active,
        coffee_options=[_coffee_option_to_response(o) for o in colleague.coffee_options],
        created_at=colleague.created_at,
        updated_at=colleague.updated_at,
    )


@router.get("", response_model=list[ColleagueResponse])
async def list_colleagues(
    db: AsyncSession = Depends(get_db),
    _current_user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(Colleague)
        .where(Colleague.is_active == True)  # noqa: E712
        .order_by(Colleague.display_order, Colleague.name)
    )
    colleagues = result.scalars().all()
    return [_colleague_to_response(c) for c in colleagues]


@router.post("", response_model=ColleagueResponse, status_code=201)
async def create_colleague(
    data: ColleagueCreate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    colleague = Colleague(**data.model_dump())
    db.add(colleague)
    await db.flush()
    await db.refresh(colleague)
    return _colleague_to_response(colleague)


@router.put("/{colleague_id}", response_model=ColleagueResponse)
async def update_colleague(
    colleague_id: uuid.UUID,
    data: ColleagueUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(Colleague).where(Colleague.id == colleague_id))
    colleague = result.scalar_one_or_none()
    if not colleague:
        raise HTTPException(status_code=404, detail="Colleague not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(colleague, field, value)

    await db.flush()
    await db.refresh(colleague)
    return _colleague_to_response(colleague)


@router.delete("/{colleague_id}")
async def delete_colleague(
    colleague_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(Colleague).where(Colleague.id == colleague_id))
    colleague = result.scalar_one_or_none()
    if not colleague:
        raise HTTPException(status_code=404, detail="Colleague not found")

    colleague.is_active = False
    await db.flush()
    return {"message": "Colleague deactivated"}


# Coffee Options sub-routes
@router.post(
    "/{colleague_id}/coffee-options",
    response_model=CoffeeOptionResponse,
    status_code=201,
)
async def add_coffee_option(
    colleague_id: uuid.UUID,
    data: CoffeeOptionCreate,
    db: AsyncSession = Depends(get_db),
    _admin: CurrentUser = Depends(require_admin),
):
    result = await db.execute(select(Colleague).where(Colleague.id == colleague_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Colleague not found")

    # If this is the first option or marked as default, handle default logic
    if data.is_default:
        await db.execute(
            select(CoffeeOption)
            .where(CoffeeOption.colleague_id == colleague_id)
        )
        existing = (
            await db.execute(
                select(CoffeeOption).where(CoffeeOption.colleague_id == colleague_id)
            )
        ).scalars().all()
        for opt in existing:
            opt.is_default = False

    option = CoffeeOption(colleague_id=colleague_id, **data.model_dump())

    # If first option, make it default
    existing_count = (
        await db.execute(
            select(CoffeeOption).where(CoffeeOption.colleague_id == colleague_id)
        )
    ).scalars().all()
    if len(existing_count) == 0:
        option.is_default = True

    db.add(option)
    await db.flush()
    await db.refresh(option)
    return _coffee_option_to_response(option)
