# app/api/exceptions/handlers.py
# pylint: skip-file
# app/api/exceptions/handlers.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    BankPaymentNotFoundError,
    BankUnavailableError,
    OrderAlreadyPaidError,
    OrderNotFoundError,
    OverpaymentError,
    PaymentNotFoundError,
    RefundExceedsDepositError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Регистрирует обработчики исключений в приложении FastAPI.
    Вызывается один раз при старте в main.py.
    """

    @app.exception_handler(OrderNotFoundError)
    async def order_not_found_handler(
            request: Request,
            exc: OrderNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )

    @app.exception_handler(OrderAlreadyPaidError)
    async def order_already_paid_handler(
            request: Request,
            exc: OrderAlreadyPaidError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(OverpaymentError)
    async def overpayment_handler(
            request: Request,
            exc: OverpaymentError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "available": str(exc.available),
                "requested": str(exc.requested),
            },
        )

    @app.exception_handler(RefundExceedsDepositError)
    async def refund_exceeds_deposit_handler(
            request: Request,
            exc: RefundExceedsDepositError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "available": str(exc.available),
                "requested": str(exc.requested),
            },
        )

    @app.exception_handler(PaymentNotFoundError)
    async def payment_not_found_handler(
            request: Request,
            exc: PaymentNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )

    @app.exception_handler(BankUnavailableError)
    async def bank_unavailable_handler(
            request: Request,
            exc: BankUnavailableError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"detail": str(exc)},
        )

    @app.exception_handler(BankPaymentNotFoundError)
    async def bank_payment_not_found_handler(
            request: Request,
            exc: BankPaymentNotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc)},
        )
