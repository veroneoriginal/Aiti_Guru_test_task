Тестовое задание


✅ Что уже сделано
Модели (полностью готовы):

base.py — все enum'ы
order.py — модель + бизнес-логика (recalculate_status, available_to_pay)
payment.py — модель + хелперы (mark_completed, sync_from_bank)


🔧 Что нужно реализовать (по порядку)
1. Инфраструктура (фундамент)

core/config.py — настройки (DATABASE_URL, BANK_API_URL и т.д.)
core/exceptions.py — кастомные исключения (OrderNotFound, PaymentError, OverpaymentError...)
infrastructure/db/session.py — AsyncSession, get_db()
infrastructure/bank/client.py — BankClient с методами acquiring_start() и acquiring_check()
infrastructure/bank/sync.py — sync_payment_with_bank()

2. Сервисы

services/order_service.py — get_order()
services/payment_service.py — deposit() и refund() — это ключевая бизнес-логика

3. API слой

api/schemas/order.py — OrderResponse
api/schemas/payment.py — PaymentCreateRequest, PaymentResponse
api/routers/orders.py — GET /orders/{id}
api/routers/payments.py — POST /payments, POST /payments/{id}/refund
api/exceptions/handlers.py — обработчики ошибок
main.py — сборка приложения FastAPI

4. Тесты

Тесты на deposit() и refund() — минимум
Тесты на recalculate_status()

5. Документация

README.md со схемой БД
