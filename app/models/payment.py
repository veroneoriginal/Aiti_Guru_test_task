# app/models/payment.py
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    PaymentOperation,
    PaymentStatus,
    PaymentType,
    TimestampMixin,
)


class Payment(TimestampMixin, Base):
    """
    Единая таблица для платежей всех типов (Single Table).

    Поля bank_* заполняются только для type=acquiring.
    Для type=cash они всегда NULL.
    """

    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
    )

    # ------------------------------------------------------------------
    # Общие поля (для всех типов)
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    type: Mapped[PaymentType] = mapped_column(
        String(20),
        nullable=False,
        comment="Тип платежа: наличные / эквайринг",
    )
    operation: Mapped[PaymentOperation] = mapped_column(
        String(20),
        nullable=False,
        comment="Операция: депозит / возврат",
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        comment="Сумма платежа",
    )
    status: Mapped[PaymentStatus] = mapped_column(
        String(20),
        nullable=False,
        default=PaymentStatus.PENDING,
        comment="Статус: создан / завершен / ошибка",
    )
    parent_payment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="RESTRICT"),
        nullable=True,
        comment="ID исходного депозита (заполняется только для возвратов)",
    )

    # ------------------------------------------------------------------
    # Поля эквайринга (nullable — заполняются только для type=acquiring)
    # ------------------------------------------------------------------
    bank_payment_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        comment="ID платежа на стороне банка",
    )
    bank_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Статус платежа по данным банка",
    )
    bank_paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата и время оплаты по данным банка",
    )

    # ------------------------------------------------------------------
    # Связи
    # ------------------------------------------------------------------
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="payments",
    )

    # ------------------------------------------------------------------
    # Хелперы
    # ------------------------------------------------------------------
    @property
    def is_acquiring(self) -> bool:
        return self.type == PaymentType.ACQUIRING

    @property
    def is_completed(self) -> bool:
        return self.status == PaymentStatus.COMPLETED

    def mark_completed(self) -> None:
        """
        Помечает платёж как завершённый и пересчитывает статус заказа.
        """
        self.status = PaymentStatus.COMPLETED
        self.order.recalculate_status()

    def mark_failed(self) -> None:
        self.status = PaymentStatus.FAILED

    def sync_from_bank(
            self,
            bank_status: str,
            bank_paid_at: Optional[datetime] = None,
    ) -> None:
        """
        Обновляет поля банка. Не меняет статус платежа — это делает сервис.
        """
        self.bank_status = bank_status
        if bank_paid_at:
            self.bank_paid_at = bank_paid_at

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} type={self.type} "
            f"op={self.operation} amount={self.amount} status={self.status}>"
        )
