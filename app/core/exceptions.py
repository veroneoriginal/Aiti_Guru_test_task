# app/core/exceptions.py

import uuid
from decimal import Decimal


class AppError(Exception):
    """
    Базовое исключение приложения.
    """
    pass


# ------------------------------------------------------------------
# Заказы
# ------------------------------------------------------------------

class OrderNotFoundError(AppError):
    """
    Ошибка: заказ не найден.
    """

    def __init__(self, order_id: uuid.UUID):
        self.order_id = order_id
        super().__init__(f"Заказ {order_id} не найден.")


class OrderAlreadyPaidError(AppError):
    """
    Заказ уже полностью оплачен — новый платёж невозможен.

    Атрибуты:
        order_id: ID заказа, который уже в статусе paid
    """

    def __init__(self, order_id: uuid.UUID):
        self.order_id = order_id
        super().__init__(f"Заказ {order_id} уже оплачен.")


# ------------------------------------------------------------------
# Платежи
# ------------------------------------------------------------------

class PaymentNotFoundError(AppError):
    """
    Ошибка: платеж не найден.
    """

    def __init__(self, payment_id: uuid.UUID):
        self.payment_id = payment_id
        super().__init__(f"Платеж {payment_id} не найден.")


class OverpaymentError(AppError):
    """
    Сумма платежа превышает доступный остаток по заказу.

    Атрибуты:
        available: сколько ещё можно оплатить по заказу
        requested: какую сумму запросил пользователь
    """

    def __init__(self, available: Decimal, requested: Decimal):
        self.available = available
        self.requested = requested
        super().__init__(
            f"Сумма платежа {requested} превышает доступный остаток {available}."
        )


class RefundExceedsDepositError(AppError):
    """
    Сумма возврата превышает оплаченную сумму по заказу.

    Атрибуты:
        available: сколько можно вернуть (фактически оплачено)
        requested: какую сумму возврата запросил пользователь
    """
    def __init__(self, available: Decimal, requested: Decimal):
        self.available = available
        self.requested = requested
        super().__init__(
            f"Сумма возврата {requested} превышает оплаченную сумму {available}."
        )


class PaymentAlreadyCompletedError(AppError):
    """
    Платёж уже был завершён ранее — повторное завершение невозможно.

    Атрибуты:
        payment_id: ID платежа, который уже в статусе completed
    """
    def __init__(self, payment_id: uuid.UUID):
        self.payment_id = payment_id
        super().__init__(f"Платеж {payment_id} уже выполнен.")


# ------------------------------------------------------------------
# Банк
# ------------------------------------------------------------------

class BankError(AppError):
    """
    Базовое исключение для ошибок банка.
    """

    def __init__(self, message: str):
        super().__init__(f"Ошибка банка: {message}")


class BankPaymentNotFoundError(BankError):
    """
    Платёж не найден на стороне банка.

    Атрибуты:
        bank_payment_id: ID платежа в системе банка
    """

    def __init__(self, bank_payment_id: str):
        self.bank_payment_id = bank_payment_id
        super().__init__(f"Банковский платеж {bank_payment_id} не найден.")


class BankUnavailableError(BankError):
    """
    Банк недоступен — сетевая ошибка или таймаут при обращении к API банка.
    """

    def __init__(self):
        super().__init__("API банка недоступен.")
