# tests/test_payment_service.py

"""
Тесты для сервиса платежей.

Покрывают основные сценарии:
- депозит наличными (полная и частичная оплата)
- возврат
- ошибки: переплата, повторная оплата, возврат больше оплаченного
- пересчёт статуса заказа
"""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    OrderAlreadyPaidError,
    OrderNotFoundError,
    OverpaymentError,
    PaymentNotFoundError,
    RefundExceedsDepositError,
)
from app.models.base import OrderStatus, PaymentOperation, PaymentStatus, PaymentType
from app.models.order import Order
from app.services.payment_service import deposit, refund

# ======================================================================
# Депозит наличными
# ======================================================================

class TestDepositCash:
    """Тесты создания платежа наличными."""

    @pytest.mark.asyncio
    async def test_full_payment(self, session: AsyncSession, order: Order):
        """Полная оплата заказа — статус становится paid."""
        payment = await deposit(
            order_id=order.id,
            amount=Decimal("1000.00"),
            payment_type=PaymentType.CASH,
            session=session,
        )

        assert payment.amount == Decimal("1000.00")
        assert payment.type == PaymentType.CASH
        assert payment.operation == PaymentOperation.DEPOSIT
        assert payment.status == PaymentStatus.COMPLETED

        # Проверяем что статус заказа пересчитался
        await session.refresh(order)
        assert order.status == OrderStatus.PAID

    @pytest.mark.asyncio
    async def test_partial_payment(self, session: AsyncSession, order: Order):
        """Частичная оплата — статус становится partial."""
        await deposit(
            order_id=order.id,
            amount=Decimal("300.00"),
            payment_type=PaymentType.CASH,
            session=session,
        )

        await session.refresh(order)
        assert order.status == OrderStatus.PARTIAL

    @pytest.mark.asyncio
    async def test_two_partial_payments_make_paid(self, session: AsyncSession, order: Order):
        """Два частичных платежа в сумме = полная оплата."""
        await deposit(
            order_id=order.id,
            amount=Decimal("600.00"),
            payment_type=PaymentType.CASH,
            session=session,
        )
        await deposit(
            order_id=order.id,
            amount=Decimal("400.00"),
            payment_type=PaymentType.CASH,
            session=session,
        )

        await session.refresh(order)
        assert order.status == OrderStatus.PAID


# ======================================================================
# Депозит эквайринг
# ======================================================================

class TestDepositAcquiring:
    """Тесты создания платежа через эквайринг."""

    @pytest.mark.asyncio
    async def test_acquiring_creates_pending_payment(self, session: AsyncSession, order: Order):
        """Эквайринг-платёж создаётся в статусе pending с bank_payment_id."""
        fake_bank_id = "bank_123"

        with patch(
                "app.services.payment_service.bank_client.acquiring_start",
                new_callable=AsyncMock,
                return_value=fake_bank_id,
        ):
            payment = await deposit(
                order_id=order.id,
                amount=Decimal("500.00"),
                payment_type=PaymentType.ACQUIRING,
                session=session,
            )

        assert payment.status == PaymentStatus.PENDING
        assert payment.bank_payment_id == fake_bank_id
        assert payment.type == PaymentType.ACQUIRING


# ======================================================================
# Ошибки депозита
# ======================================================================

class TestDepositErrors:
    """Тесты ошибок при создании платежа."""

    @pytest.mark.asyncio
    async def test_order_not_found(self, session: AsyncSession):
        """Платёж по несуществующему заказу — OrderNotFoundError."""
        with pytest.raises(OrderNotFoundError):
            await deposit(
                order_id=uuid.uuid4(),
                amount=Decimal("100.00"),
                payment_type=PaymentType.CASH,
                session=session,
            )

    @pytest.mark.asyncio
    async def test_overpayment(self, session: AsyncSession, order: Order):
        """Сумма больше остатка — OverpaymentError."""
        with pytest.raises(OverpaymentError):
            await deposit(
                order_id=order.id,
                amount=Decimal("1500.00"),
                payment_type=PaymentType.CASH,
                session=session,
            )

    @pytest.mark.asyncio
    async def test_already_paid(self, session: AsyncSession, order: Order):
        """Платёж по уже оплаченному заказу — OrderAlreadyPaidError."""
        # Сначала оплачиваем полностью
        await deposit(
            order_id=order.id,
            amount=Decimal("1000.00"),
            payment_type=PaymentType.CASH,
            session=session,
        )
        # Пытаемся заплатить ещё
        with pytest.raises(OrderAlreadyPaidError):
            await deposit(
                order_id=order.id,
                amount=Decimal("1.00"),
                payment_type=PaymentType.CASH,
                session=session,
            )


# ======================================================================
# Возврат
# ======================================================================

class TestRefund:
    """Тесты возврата."""

    @pytest.mark.asyncio
    async def test_partial_refund(self, session: AsyncSession, order: Order):
        """Частичный возврат — статус возвращается в partial."""
        payment = await deposit(
            order_id=order.id,
            amount=Decimal("1000.00"),
            payment_type=PaymentType.CASH,
            session=session,
        )

        refund_payment = await refund(
            payment_id=payment.id,
            amount=Decimal("300.00"),
            session=session,
        )

        assert refund_payment.operation == PaymentOperation.REFUND
        assert refund_payment.amount == Decimal("300.00")
        assert refund_payment.status == PaymentStatus.COMPLETED

        await session.refresh(order)
        assert order.status == OrderStatus.PARTIAL

    @pytest.mark.asyncio
    async def test_full_refund(self, session: AsyncSession, order: Order):
        """Полный возврат — статус становится unpaid."""
        payment = await deposit(
            order_id=order.id,
            amount=Decimal("1000.00"),
            payment_type=PaymentType.CASH,
            session=session,
        )

        await refund(
            payment_id=payment.id,
            amount=Decimal("1000.00"),
            session=session,
        )

        await session.refresh(order)
        assert order.status == OrderStatus.UNPAID


# ======================================================================
# Ошибки возврата
# ======================================================================

class TestRefundErrors:
    """Тесты ошибок при возврате."""

    @pytest.mark.asyncio
    async def test_payment_not_found(self, session: AsyncSession):
        """Возврат по несуществующему платежу — PaymentNotFoundError."""
        with pytest.raises(PaymentNotFoundError):
            await refund(
                payment_id=uuid.uuid4(),
                amount=Decimal("100.00"),
                session=session,
            )

    @pytest.mark.asyncio
    async def test_refund_exceeds_paid(self, session: AsyncSession, order: Order):
        """Возврат больше оплаченного — RefundExceedsDepositError."""
        payment = await deposit(
            order_id=order.id,
            amount=Decimal("500.00"),
            payment_type=PaymentType.CASH,
            session=session,
        )

        with pytest.raises(RefundExceedsDepositError):
            await refund(
                payment_id=payment.id,
                amount=Decimal("999.00"),
                session=session,
            )
