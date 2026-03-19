# app/services/sync_scheduler.py
import asyncio
import logging

from sqlalchemy import select

from app.core.exceptions import BankPaymentNotFoundError, BankUnavailableError
from app.infrastructure.bank.sync import sync_payment_with_bank
from app.infrastructure.db.session import AsyncSessionFactory
from app.models.base import PaymentStatus, PaymentType
from app.models.payment import Payment

logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 60  # частота опроса банка


async def sync_pending_payments() -> None:
    """
    Находит все pending-эквайринговые платежи и синхронизирует с банком.
    """
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(Payment).where(
                Payment.type == PaymentType.ACQUIRING,
                Payment.status == PaymentStatus.PENDING,
                Payment.bank_payment_id.is_not(None),
                )
        )
        payments = result.scalars().all()

        for payment in payments:
            try:
                await sync_payment_with_bank(payment, session)
                logger.info("Синхронизирован платёж %s", payment.id)
            except Exception as e:
                logger.error("Ошибка синхронизации платежа %s: %s", payment.id, e)


async def run_sync_loop() -> None:
    """
    Бесконечный цикл синхронизации. Запускается при старте приложения.
    """
    while True:
        try:
            await sync_pending_payments()
        except Exception as e:
            logger.error("Ошибка в цикле синхронизации: %s", e)
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)
