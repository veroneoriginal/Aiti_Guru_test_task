# app/services/order_service.py

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import OrderNotFoundError
from app.models.order import Order


async def get_order(
        order_id: uuid.UUID,
        session: AsyncSession,
) -> Order:
    """
    Возвращает заказ по ID.

    Аргументы:
        order_id: ID заказа
        session: активная сессия БД

    Возвращает:
        объект Order с загруженными платежами

    Исключения:
        OrderNotFoundError: заказ не найден
    """
    result = await session.execute(
        select(Order).where(Order.id == order_id)
    )
    order = result.scalar_one_or_none() # возвращает объект или None, не падает если не нашёл

    if order is None:
        raise OrderNotFoundError(order_id)

    return order
