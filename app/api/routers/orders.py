# app/api/routers/orders.py

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.order import OrderResponse
from app.infrastructure.db.session import get_db
from app.services.order_service import get_order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_handler(
        order_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
) -> OrderResponse:
    """
    Возвращает заказ по ID со всеми платежами.
    """
    order = await get_order(order_id, session)
    return OrderResponse.model_validate(order)
