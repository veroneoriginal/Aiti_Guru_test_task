# app/models/base.py

import enum
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """
    Миксин с полями created_at и updated_at.
    Подмешивается в любую модель, которой нужны временные метки.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OrderStatus(str, enum.Enum):
    UNPAID = "unpaid"  # не оплачен
    PARTIAL = "partial"  # частично оплачен
    PAID = "paid"  # оплачен


class PaymentType(str, enum.Enum):
    CASH = "cash"  # наличные
    ACQUIRING = "acquiring"  # экваринг


class PaymentOperation(str, enum.Enum):
    DEPOSIT = "deposit"  # депозит
    REFUND = "refund"  # возврат


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"  # создан, ожидаем подтверждения (актуально для эквайринга)
    COMPLETED = "completed"  # успешно завершён
    FAILED = "failed"  # ошибка
