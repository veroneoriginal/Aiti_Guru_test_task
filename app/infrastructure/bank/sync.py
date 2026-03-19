# app/infrastructure/bank/sync.py
# Этот модуль — связующее звено между банком и БД.
# Он не знает ни про HTTP, ни про бизнес-логику — просто координирует
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.bank.client import bank_client
from app.models.order import Order
from app.models.payment import Payment


async def sync_payment_with_bank(
        payment: Payment,
        session: AsyncSession,
) -> None:
    """
    Синхронизирует статус платежа с банком.

    Запрашивает актуальное состояние платежа у банка через acquiring_check
    и обновляет наши данные в соответствии с ответом.

    Аргументы:
        payment: объект платежа с заполненным bank_payment_id
        session: активная сессия БД

    Исключения:
        BankPaymentNotFoundError: платёж не найден в банке
        BankUnavailableError: банк недоступен
    """
    data = await bank_client.acquiring_check(payment.bank_payment_id)

    bank_status = data["status"]
    bank_paid_at = data.get("paid_at")

    payment.sync_from_bank(
        bank_status=bank_status,
        bank_paid_at=bank_paid_at,
    )

    if bank_status == "success":
        # Загрузка заказа со всеми платежами для корректного пересчёта
        result = await session.execute(
            select(Order)
            .where(Order.id == payment.order_id)
            .options(selectinload(Order.payments))
        )
        order = result.scalar_one()
        payment.order = order
        payment.mark_completed()

    elif bank_status == "failed":
        payment.mark_failed()

    session.add(payment)
    await session.commit()
