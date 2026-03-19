# app/models/order.py

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    OrderStatus,
    PaymentOperation,
    PaymentStatus,
    TimestampMixin,
)

# спасает от циклической зависимости между взаимосвязанными моделями.
if TYPE_CHECKING:
    from app.models.payment import Payment


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Итоговая сумма заказа",
    )
    status: Mapped[OrderStatus] = mapped_column(
        String(20),
        nullable=False,
        default=OrderStatus.UNPAID,
        comment="Статус оплаты: не оплачен / частично оплачен / оплачен",
    )

    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        lazy="selectin",
    )

    # ------------------------------------------------------------------
    # Бизнес-логика пересчёта статуса
    # Вызывается после каждого deposit / refund
    # ------------------------------------------------------------------
    def recalculate_status(self) -> None:
        """
        Пересчитывает статус на основе завершённых платежей.
        """
        paid_total = self.paid_total()

        if paid_total <= 0:
            self.status = OrderStatus.UNPAID
        elif paid_total >= self.amount:
            self.status = OrderStatus.PAID
        else:
            self.status = OrderStatus.PARTIAL

    def paid_total(self) -> Decimal:
        """
        Сумма всех завершённых депозитов минус возвраты.
        """

        total = Decimal("0")
        for p in self.payments:
            if p.status != PaymentStatus.COMPLETED:
                continue
            if p.operation == PaymentOperation.DEPOSIT:
                total += p.amount
            elif p.operation == PaymentOperation.REFUND:
                total -= p.amount
        return total

    def available_to_pay(self) -> Decimal:
        """
        Сколько ещё можно заплатить по заказу.
        """
        return self.amount - self.paid_total()
