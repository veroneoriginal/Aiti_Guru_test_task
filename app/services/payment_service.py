# app/services/payment_service.py

import uuid  # для типизации order_id и payment_id
from decimal import Decimal  # для типизации суммы платежа

from sqlalchemy import select  # построение SELECT-запроса
from sqlalchemy.ext.asyncio import AsyncSession  # тип сессии БД

from app.core.exceptions import (
    OrderAlreadyPaidError,
    OverpaymentError,
    RefundExceedsDepositError,
    PaymentNotFoundError,
)
from app.infrastructure.bank.client import bank_client
from app.models.payment import Payment
from app.models.base import (
    PaymentType,
    PaymentOperation,
    PaymentStatus,
    OrderStatus,
)
from app.services.order_service import get_order


async def deposit(
        order_id: uuid.UUID,
        amount: Decimal,
        payment_type: PaymentType,
        session: AsyncSession,
) -> Payment:
    """
    Создаёт платёж-депозит по заказу.

    Для наличных — сразу помечает платёж завершённым.
    Для эквайринга — создаёт платёж в банке, статус остаётся pending.

    Аргументы:
        order_id: ID заказа, по которому создаём платёж
        amount: сумма платежа
        payment_type: тип платежа (наличные / эквайринг)
        session: активная сессия БД, пробрасывается из роутера

    Возвращает:
        созданный объект Payment

    Исключения:
        OrderNotFoundError: заказ не найден
        OrderAlreadyPaidError: заказ уже оплачен
        OverpaymentError: сумма превышает остаток по заказу
    """
    # Загрузка заказа из БД, OrderNotFoundError если нет
    order = await get_order(order_id, session)

    # Проверка — если заказ уже полностью оплачен - платёж невозможен
    if order.status == OrderStatus.PAID:
        raise OrderAlreadyPaidError(order_id)

    # Поссчет сколько ещё можно заплатить
    available = order.available_to_pay()
    # если запрошенная сумма больше остатка
    if amount > available:
        raise OverpaymentError(available=available, requested=amount)  # отклоняется операция

    # Создание объекта платежа в памяти
    payment = Payment(
        order_id=order_id,  # привязка к заказу
        type=payment_type,  # наличные или эквайринг
        operation=PaymentOperation.DEPOSIT,  # депозит
        amount=amount,  # сумма
        status=PaymentStatus.PENDING,  # начальный статус — ожидание
    )
    # Регистрация объекта в сессии
    session.add(payment)
    # Отправка INSERT в БД — получение payment.id, но без фиксации
    await session.flush()  # запись в рамках транзакции

    # Тип оплаты наличные
    if payment_type == PaymentType.CASH:
        # Завершение — подтверждение не нужно, внутри пересчитывается статус заказа
        payment.mark_completed()

    # Тип оплаты эквайринг
    elif payment_type == PaymentType.ACQUIRING:
        # Переход в банк для создания платежа
        bank_payment_id = await bank_client.acquiring_start(
            order_id=str(order_id),
            amount=str(amount),
        )
        payment.bank_payment_id = bank_payment_id  # сохраняение ID банка на объекте

    # Отметить объект как изменённый
    session.add(payment)
    # Фиксация транзакции в БД
    await session.commit()
    # Обновляем объект в БД
    await session.refresh(payment)
    # Возврат готового платёжа
    return payment


async def refund(
        payment_id: uuid.UUID,
        amount: Decimal,
        session: AsyncSession,
) -> Payment:
    """
    Создаёт платёж-возврат по существующему депозиту.

    Аргументы:
        payment_id: ID исходного платежа (депозита), по которому осуществляется возврат
        amount: сумма возврата
        session: активная сессия БД

    Возвращает:
        созданный объект Payment с операцией refund

    Исключения:
        PaymentNotFoundError: исходный платёж не найден
        RefundExceedsDepositError: сумма возврата превышает оплаченную сумму
    """
    # Поиск платежа по ID
    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    # Получение объекта или None если не найден
    original_payment = result.scalar_one_or_none()

    if original_payment is None:
        raise PaymentNotFoundError(payment_id)

    # Загрузка заказа со всеми платежами для проверки суммы возврата
    order = await get_order(original_payment.order_id, session)

    # Подсчет суммы фактических оплат по заказу
    paid_total = order.paid_total()

    # Если сумма возврата больше, чем оплачено
    if amount > paid_total:
        raise RefundExceedsDepositError(available=paid_total, requested=amount)

    # Cоздание объекта платежа-возврата
    refund_payment = Payment(
        order_id=original_payment.order_id,
        type=original_payment.type,
        operation=PaymentOperation.REFUND,
        amount=amount,
        status=PaymentStatus.PENDING,
    )
    session.add(refund_payment)
    await session.flush()

    # Завершение — возврат не требует подтверждения
    refund_payment.mark_completed()

    session.add(refund_payment)
    await session.commit()
    await session.refresh(refund_payment)

    # Возврат готового платёжа-возврата
    return refund_payment
