# app/api/routers/payments.py

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.payment import (
    PaymentCreateRequest,
    PaymentResponse,
    RefundCreateRequest,
)
from app.core.exceptions import PaymentNotFoundError
from app.infrastructure.bank.sync import sync_payment_with_bank
from app.infrastructure.db.session import get_db
from app.models.payment import Payment
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


@router.post("/{payment_id}/sync", response_model=PaymentResponse)
async def sync_payment_handler(
        payment_id: uuid.UUID,
        session: AsyncSession = Depends(get_db),
) -> PaymentResponse:
    """
    Синхронизирует статус эквайрингового платежа с банком.
    """
    result = await session.execute(
        select(Payment).where(Payment.id == payment_id)
    )
    payment = result.scalar_one_or_none()

    if payment is None:
        raise PaymentNotFoundError(payment_id)

    if not payment.bank_payment_id:
        raise HTTPException(
            status_code=400,
            detail="Платёж не является эквайринговым.",
        )

    await sync_payment_with_bank(payment, session)
    await session.refresh(payment)
    return PaymentResponse.model_validate(payment)
