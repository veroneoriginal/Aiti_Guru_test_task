# app/infrastructure/bank/client.py

import httpx

from app.core.config import settings
from app.core.exceptions import BankPaymentNotFoundError, BankUnavailableError


class BankClient:
    """
    HTTP-клиент для работы с API банка.

    Инкапсулирует все обращения к внешнему сервису банка.
    Не содержит бизнес-логики — только запросы и обработка ошибок сети.
    """

    def __init__(self) -> None:
        self._base_url = settings.BANK_API_URL
        self._timeout = settings.BANK_API_TIMEOUT

    async def acquiring_start(
            self,
            order_id: str,
            amount: str,
    ) -> str:
        """
        Создаёт платёж в банке.

        Аргументы:
            order_id: ID заказа в нашей системе
            amount: сумма платежа в виде строки (например "100.00")

        Возвращает:
            bank_payment_id: уникальный ID платежа в системе банка

        Исключения:
            BankUnavailableError: банк недоступен или вернул неожиданный ответ
        """
        payload = {
            "order_id": order_id,
            "amount": amount,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/acquiring_start",
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise BankUnavailableError() from exc
        except httpx.RequestError as exc:
            raise BankUnavailableError() from exc

        if response.status_code != 200:
            raise BankUnavailableError()

        data = response.json()

        if "error" in data:
            raise BankUnavailableError()

        return data["bank_payment_id"]

    async def acquiring_check(
            self,
            bank_payment_id: str,
    ) -> dict:
        """
        Проверяет статус платежа в банке.

        Аргументы:
            bank_payment_id: ID платежа в системе банка

        Возвращает:
            словарь с полями: bank_payment_id, amount, status, paid_at

        Исключения:
            BankPaymentNotFoundError: платёж не найден в банке
            BankUnavailableError: банк недоступен или вернул неожиданный ответ
        """
        payload = {
            "bank_payment_id": bank_payment_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/acquiring_check",
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise BankUnavailableError() from exc
        except httpx.RequestError as exc:
            raise BankUnavailableError() from exc

        if response.status_code == 404:
            raise BankPaymentNotFoundError(bank_payment_id)

        if response.status_code != 200:
            raise BankUnavailableError()

        data = response.json()

        if data.get("error") == "Платеж не найден.":
            raise BankPaymentNotFoundError(bank_payment_id)

        return data


bank_client = BankClient()
