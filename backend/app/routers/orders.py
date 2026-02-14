import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.models.colleague import Colleague
from app.models.coffee_option import CoffeeOption
from app.models.order import Order, OrderItem
from app.schemas.order import (
    OrderCreate,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderUpdateRequest,
)
from app.services.order import consolidate_order_items

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_query():
    """Base query for loading an order with all nested relationships."""
    return (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.colleague),
            selectinload(Order.creator),
        )
    )


async def _build_order_response(order: Order) -> OrderResponse:
    items_data = []
    item_responses = []
    for item in order.items:
        resp = OrderItemResponse(
            id=item.id,
            order_id=item.order_id,
            colleague_id=item.colleague_id,
            colleague_name=item.colleague.name if item.colleague else None,
            coffee_option_id=item.coffee_option_id,
            drink_type_name=item.drink_type_name,
            size_name=item.size_name,
            size_abbreviation=item.size_abbreviation,
            milk_option_name=item.milk_option_name,
            sugar=item.sugar,
            notes=item.notes,
            created_at=item.created_at,
        )
        item_responses.append(resp)
        items_data.append(
            {
                "drink_type_name": item.drink_type_name,
                "size_name": item.size_name,
                "size_abbreviation": item.size_abbreviation,
                "milk_option_name": item.milk_option_name,
                "sugar": item.sugar,
                "notes": item.notes,
            }
        )

    consolidated = consolidate_order_items(items_data)
    return OrderResponse(
        id=order.id,
        share_token=order.share_token,
        created_by=order.created_by,
        created_at=order.created_at,
        items=item_responses,
        consolidated=consolidated,
    )


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    order = Order(
        share_token=secrets.token_urlsafe(48),
        created_by=current_user.id,
    )
    db.add(order)
    await db.flush()

    for item_data in data.items:
        # Look up the coffee option to denormalize
        result = await db.execute(
            select(CoffeeOption).where(CoffeeOption.id == item_data.coffee_option_id)
        )
        coffee_opt = result.scalar_one_or_none()
        if not coffee_opt:
            raise HTTPException(
                status_code=400,
                detail=f"Coffee option {item_data.coffee_option_id} not found",
            )

        order_item = OrderItem(
            order_id=order.id,
            colleague_id=item_data.colleague_id,
            coffee_option_id=item_data.coffee_option_id,
            drink_type_name=coffee_opt.drink_type.name,
            size_name=coffee_opt.size.name,
            size_abbreviation=coffee_opt.size.abbreviation,
            milk_option_name=coffee_opt.milk_option.name if coffee_opt.milk_option else None,
            sugar=coffee_opt.sugar,
            notes=coffee_opt.notes,
        )
        db.add(order_item)

    await db.flush()

    # Re-query with eager loading to avoid lazy-load issues in async
    result = await db.execute(_order_query().where(Order.id == order.id))
    order = result.scalar_one()
    return await _build_order_response(order)


@router.get("", response_model=list[OrderListResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        _order_query().order_by(Order.created_at.desc()).offset(skip).limit(limit)
    )
    orders = result.scalars().all()
    responses = []
    for order in orders:
        responses.append(
            OrderListResponse(
                id=order.id,
                share_token=order.share_token,
                created_at=order.created_at,
                item_count=len(order.items),
            )
        )
    return responses


@router.get("/share/{share_token}", response_model=OrderResponse)
async def get_shared_order(share_token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        _order_query().where(Order.share_token == share_token)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return await _build_order_response(order)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(_order_query().where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return await _build_order_response(order)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: uuid.UUID,
    data: OrderUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Delete existing items
    for item in order.items:
        await db.delete(item)
    await db.flush()

    # Add new items
    for item_data in data.items:
        result = await db.execute(
            select(CoffeeOption).where(CoffeeOption.id == item_data.coffee_option_id)
        )
        coffee_opt = result.scalar_one_or_none()
        if not coffee_opt:
            raise HTTPException(
                status_code=400,
                detail=f"Coffee option {item_data.coffee_option_id} not found",
            )

        order_item = OrderItem(
            order_id=order.id,
            colleague_id=item_data.colleague_id,
            coffee_option_id=item_data.coffee_option_id,
            drink_type_name=coffee_opt.drink_type.name,
            size_name=coffee_opt.size.name,
            size_abbreviation=coffee_opt.size.abbreviation,
            milk_option_name=coffee_opt.milk_option.name if coffee_opt.milk_option else None,
            sugar=coffee_opt.sugar,
            notes=coffee_opt.notes,
        )
        db.add(order_item)

    await db.flush()

    result = await db.execute(_order_query().where(Order.id == order.id))
    order = result.scalar_one()
    return await _build_order_response(order)
