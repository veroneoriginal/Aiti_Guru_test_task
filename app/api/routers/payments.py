# app/api/routers/payments.py

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.payment import (
    PaymentCreateRequest,
    PaymentResponse,
    RefundCreateRequest,
)
from app.infrastructure.db.session import get_db
from app.services.payment_service import deposit, refund

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=201)
async def create_payment_handler(
        body: PaymentCreateRequest,
        session: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    """
    Создаёт платёж-депозит по заказу.
    """
    payment = await deposit(
        order_id=body.order_id,
        amount=body.amount,
        payment_type=body.type,
        session=session,
    )
    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/refund", response_model=PaymentResponse, status_code=201)
async def create_refund_handler(
        payment_id: uuid.UUID,
        body: RefundCreateRequest,
        session: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    """
    Создаёт возврат по существующему платежу.
    """
    payment = await refund(
        payment_id=payment_id,
        amount=body.amount,
        session=session,
    )
    return PaymentResponse.model_validate(payment)
