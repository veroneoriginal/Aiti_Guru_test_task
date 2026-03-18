# app/api/schemas/order.py

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.api.schemas.payment import PaymentResponse
from app.models.base import OrderStatus


class OrderResponse(BaseModel):
    """
    Схема ответа для заказа.
    Возвращается в GET /orders/{id}.
    """

    id: uuid.UUID
    amount: Decimal
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    payments: list[PaymentResponse]

    model_config = {"from_attributes": True}
