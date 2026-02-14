from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.models.order import Order, OrderItem
from app.schemas.order import ColleagueStat, DrinkStat, StatsOverview

router = APIRouter(prefix="/stats", tags=["stats"])


def _get_date_filter(days: int | None):
    if days is None:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


@router.get("/overview", response_model=StatsOverview)
async def stats_overview(
    days: int | None = Query(None, description="Filter to last N days"),
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    date_from = _get_date_filter(days)
    base_query = select(Order)
    if date_from:
        base_query = base_query.where(Order.created_at >= date_from)

    # Total orders
    result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total_orders = result.scalar() or 0

    # Total coffees
    items_query = select(func.count(OrderItem.id))
    if date_from:
        items_query = items_query.join(Order).where(Order.created_at >= date_from)
    result = await db.execute(items_query)
    total_coffees = result.scalar() or 0

    # Orders this week
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        select(func.count()).select_from(
            select(Order).where(Order.created_at >= week_ago).subquery()
        )
    )
    orders_this_week = result.scalar() or 0

    # Orders this month
    month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    result = await db.execute(
        select(func.count()).select_from(
            select(Order).where(Order.created_at >= month_ago).subquery()
        )
    )
    orders_this_month = result.scalar() or 0

    # Busiest day of week
    result = await db.execute(
        select(
            func.strftime("%w", Order.created_at).label("dow"),
            func.count().label("cnt"),
        )
        .group_by("dow")
        .order_by(func.count().desc())
        .limit(1)
    )
    row = result.first()
    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    busiest_day = day_names[int(row[0])] if row else None

    return StatsOverview(
        total_orders=total_orders,
        total_coffees=total_coffees,
        busiest_day=busiest_day,
        orders_this_week=orders_this_week,
        orders_this_month=orders_this_month,
    )


@router.get("/drinks", response_model=list[DrinkStat])
async def stats_drinks(
    days: int | None = Query(None),
    limit: int = Query(10),
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    query = select(
        OrderItem.drink_type_name,
        func.count().label("cnt"),
    )
    if days:
        date_from = _get_date_filter(days)
        query = query.join(Order).where(Order.created_at >= date_from)
    query = query.group_by(OrderItem.drink_type_name).order_by(
        func.count().desc()
    ).limit(limit)

    result = await db.execute(query)
    return [
        DrinkStat(drink_name=row[0], count=row[1]) for row in result.all()
    ]


@router.get("/colleagues", response_model=list[ColleagueStat])
async def stats_colleagues(
    days: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    from app.models.colleague import Colleague

    # Count orders per colleague
    query = select(
        Colleague.name,
        func.count(OrderItem.id).label("cnt"),
    ).join(Colleague, OrderItem.colleague_id == Colleague.id)

    if days:
        date_from = _get_date_filter(days)
        query = query.join(Order, OrderItem.order_id == Order.id).where(
            Order.created_at >= date_from
        )

    query = query.group_by(Colleague.name).order_by(func.count(OrderItem.id).desc())
    result = await db.execute(query)
    colleague_counts = result.all()

    stats = []
    for name, count in colleague_counts:
        # Get favourite drink for each colleague
        fav_query = (
            select(OrderItem.drink_type_name, func.count().label("cnt"))
            .join(Colleague, OrderItem.colleague_id == Colleague.id)
            .where(Colleague.name == name)
            .group_by(OrderItem.drink_type_name)
            .order_by(func.count().desc())
            .limit(1)
        )
        fav_result = await db.execute(fav_query)
        fav_row = fav_result.first()

        stats.append(
            ColleagueStat(
                colleague_name=name,
                order_count=count,
                favourite_drink=fav_row[0] if fav_row else None,
            )
        )

    return stats
