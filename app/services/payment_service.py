# app/services/payment_service.py

import uuid  # для типизации order_id и payment_id
from decimal import Decimal  # для типизации суммы платежа

from sqlalchemy import select  # построение SELECT-запроса
from sqlalchemy.ext.asyncio import AsyncSession  # тип сессии БД

from app.core.exceptions import (
    OrderAlreadyPaidError,
    OverpaymentError,
    PaymentNotFoundError,
    RefundExceedsDepositError,
    RefundOnIncompletePaymentError,
    RefundOnNonDepositError,
)
from app.infrastructure.bank.client import bank_client
from app.models.base import OrderStatus, PaymentOperation, PaymentStatus, PaymentType
from app.models.payment import Payment
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
    session.add(order)
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
    """
    # 1. Поиск оригинального платежа
    result = await session.execute(select(Payment).where(Payment.id == payment_id))

    # scalar_one_or_none() достаёт из обёртки сам платёж (или None)
    original_payment = result.scalar_one_or_none()

    if original_payment is None:
        raise PaymentNotFoundError(payment_id)

    # 2. Возврат только по депозиту
    if original_payment.operation != PaymentOperation.DEPOSIT:
        raise RefundOnNonDepositError(payment_id)

    # 3. Возврат только по завершённому платежу
    if original_payment.status != PaymentStatus.COMPLETED:
        raise RefundOnIncompletePaymentError(payment_id)

    # 4. Считаем сколько уже вернули по ЭТОМУ депозиту
    refunded_result = await session.execute(
        select(Payment).where(
            Payment.parent_payment_id == payment_id,
            Payment.operation == PaymentOperation.REFUND,
            Payment.status == PaymentStatus.COMPLETED,
            )
    )
    refunded_payments = refunded_result.scalars().all() # [Payment(200₽), Payment(50₽)] / [].
    already_refunded = sum(p.amount for p in refunded_payments) \
        if refunded_payments else Decimal("0")

    # 5. Не возвращаем больше, чем оплачено по этому платежу
    available_for_refund = original_payment.amount - already_refunded
    if amount > available_for_refund:
        raise RefundExceedsDepositError(available=available_for_refund, requested=amount)

    # 6. Создаём возврат с привязкой к депозиту
    refund_payment = Payment(
        order_id=original_payment.order_id,
        type=original_payment.type,
        operation=PaymentOperation.REFUND,
        amount=amount,
        status=PaymentStatus.PENDING,
        parent_payment_id=original_payment.id,  # связь с депозитом
    )
    session.add(refund_payment)
    await session.flush()

    # 7. Логика по типу платежа
    if original_payment.type == PaymentType.CASH:
        refund_payment.mark_completed()
    elif original_payment.type == PaymentType.ACQUIRING:
        bank_payment_id = await bank_client.acquiring_start(
            order_id=str(original_payment.order_id),
            amount=str(amount),
        )
        refund_payment.bank_payment_id = bank_payment_id

    session.add(refund_payment)
    order = await get_order(original_payment.order_id, session)
    session.add(order)
    await session.commit()
    await session.refresh(refund_payment)
    return refund_payment
