import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import TeamMember, get_team_member
from app.models.coffee_option import CoffeeOption
from app.models.colleague import Colleague
from app.models.team import TeamRole
from app.routers.colleagues import _coffee_option_to_response
from app.schemas.colleague import CoffeeOptionResponse, CoffeeOptionUpdate

router = APIRouter(prefix="/coffee-options", tags=["coffee-options"])


async def _get_option_with_permission(
    option_id: uuid.UUID,
    team_member: TeamMember,
    db: AsyncSession,
) -> CoffeeOption:
    """Load a coffee option, verify it belongs to the team, and check permissions."""
    result = await db.execute(
        select(CoffeeOption)
        .join(Colleague)
        .where(
            CoffeeOption.id == option_id,
            Colleague.team_id == team_member.team_id,
        )
    )
    option = result.scalar_one_or_none()
    if not option:
        raise HTTPException(status_code=404, detail="Coffee option not found")

    # Owner/manager can edit any; member only their own linked colleague
    if team_member.role not in (TeamRole.owner, TeamRole.manager):
        colleague = (
            await db.execute(select(Colleague).where(Colleague.id == option.colleague_id))
        ).scalar_one()
        if colleague.user_id != team_member.id:
            raise HTTPException(status_code=403, detail="Cannot modify this coffee option")

    return option


@router.put("/{option_id}", response_model=CoffeeOptionResponse)
async def update_coffee_option(
    option_id: uuid.UUID,
    data: CoffeeOptionUpdate,
    db: AsyncSession = Depends(get_db),
    team_member: TeamMember = Depends(get_team_member),
):
    option = await _get_option_with_permission(option_id, team_member, db)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(option, field, value)

    await db.flush()
    await db.refresh(option)
    return _coffee_option_to_response(option)


@router.delete("/{option_id}")
async def delete_coffee_option(
    option_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    team_member: TeamMember = Depends(get_team_member),
):
    option = await _get_option_with_permission(option_id, team_member, db)

    await db.delete(option)
    await db.flush()
    return {"message": "Coffee option deleted"}


@router.put("/{option_id}/set-default", response_model=CoffeeOptionResponse)
async def set_default_coffee_option(
    option_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    team_member: TeamMember = Depends(get_team_member),
):
    option = await _get_option_with_permission(option_id, team_member, db)

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
