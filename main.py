# main.py
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.exceptions.handlers import register_exception_handlers
from app.api.routers.orders import router as orders_router
from app.api.routers.payments import router as payments_router
from app.services.sync_scheduler import run_sync_loop


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Запуск фоновой синхронизации при старте
    task = asyncio.create_task(run_sync_loop())
    yield
    # Остановка при завершении
    task.cancel()


app = FastAPI(
    title="Payment Service",
    description="Сервис работы с платежами по заказу",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Роутеры ---
app.include_router(orders_router)
app.include_router(payments_router)

# --- Обработчики исключений ---
register_exception_handlers(app)


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """
    Проверка работоспособности сервиса.
    """
    return {"status": "ok"}
