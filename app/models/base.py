# app/models/base.py

import enum

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class OrderStatus(str, enum.Enum):
    UNPAID = "unpaid"   # не оплачен
    PARTIAL = "partial" # частично оплачен
    PAID = "paid"       # оплачен


class PaymentType(str, enum.Enum):
    CASH = "cash"           # наличные
    ACQUIRING = "acquiring" # экваринг


class PaymentOperation(str, enum.Enum):
    DEPOSIT = "deposit" # депозит
    REFUND = "refund"   # возврат


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"      # создан, ожидаем подтверждения (актуально для эквайринга)
    COMPLETED = "completed"  # успешно завершён
    FAILED = "failed"        # ошибка
