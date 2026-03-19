# app/api/schemas/payment.py

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, Field

from app.models.base import PaymentOperation, PaymentStatus, PaymentType

AmountField = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2)]


class PaymentCreateRequest(BaseModel):
    """
    Схема запроса для создания платежа (депозита).
    Принимается в POST /payments.
    """

    order_id: uuid.UUID
    amount: AmountField
    type: PaymentType


class RefundCreateRequest(BaseModel):
    """
    Схема запроса для создания возврата.
    Принимается в POST /payments/{id}/refund.
    """

    amount: AmountField


class PaymentResponse(BaseModel):
    """
    Схема ответа для платежа.
    Используется внутри OrderResponse и как ответ на создание платежа.
    """

    id: uuid.UUID
    order_id: uuid.UUID
    parent_payment_id: Optional[uuid.UUID]
    type: PaymentType
    operation: PaymentOperation
    amount: Decimal
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    bank_payment_id: Optional[str]
    bank_status: Optional[str]
    bank_paid_at: Optional[datetime]

    model_config = {"from_attributes": True}
