from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order
from app.routers.orders import _build_order_response, _order_query
from app.schemas.order import OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/share/{share_token}", response_model=OrderResponse)
async def get_shared_order(share_token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(_order_query().where(Order.share_token == share_token))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return await _build_order_response(order)
