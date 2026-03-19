# Тестовое задание
FastAPI - потому, что задание само подталкивает к нему своими требованиями. 
Async - потому, что есть внешний банк, и блокировать воркер на ожидании его ответа расточительно.


# Payment Service

Сервис работы с платежами по заказу. Позволяет оплачивать заказы одним или несколькими платежами (наличные / эквайринг), делать возвраты и синхронизировать статус платежей с банком.

## Стек

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL
- httpx (HTTP-клиент для API банка)
- Pydantic v2
- pytest + pytest-asyncio (тесты)

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone <url>
cd tech_task
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Настроить переменные окружения

Создать файл `.env` в корне проекта:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/payments_db
BANK_API_URL=http://localhost:8080
BANK_API_TIMEOUT=10
```

### 4. Создать таблицы

```bash
psql -U user -d payments_db -f schema.sql
```

### 5. Запустить сервис

```bash
uvicorn main:app --reload
```

Swagger-документация доступна по адресу: `http://localhost:8000/docs`

## Запуск тестов

Тесты используют in-memory SQLite — PostgreSQL не нужен.

```bash
pip install pytest pytest-asyncio aiosqlite
pytest tests/ -v
```

## Структура проекта

```
├── main.py                          # Точка входа FastAPI
├── schema.sql                       # DDL-схема базы данных
├── .env                             # Переменные окружения (не в git)
├── app/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── orders.py            # GET /orders/{id}
│   │   │   └── payments.py          # POST /payments, POST /payments/{id}/refund
│   │   ├── schemas/
│   │   │   ├── order.py             # Pydantic-схемы заказа
│   │   │   └── payment.py           # Pydantic-схемы платежа
│   │   └── exceptions/
│   │       └── handlers.py          # Маппинг исключений → HTTP-ответы
│   ├── core/
│   │   ├── config.py                # Настройки (из .env)
│   │   └── exceptions.py            # Бизнес-исключения
│   ├── models/
│   │   ├── base.py                  # Base, enum-ы статусов
│   │   ├── order.py                 # Модель Order
│   │   └── payment.py              # Модель Payment
│   ├── services/
│   │   ├── order_service.py         # Получение заказа
│   │   └── payment_service.py       # Депозит, возврат
│   └── infrastructure/
│       ├── bank/
│       │   ├── client.py            # HTTP-клиент к API банка
│       │   └── sync.py              # Синхронизация статуса с банком
│       └── db/
│           └── session.py           # Движок и сессия SQLAlchemy
│           └── schema.sql           # Схема БД
└── tests/
    ├── conftest.py                  # Фикстуры (in-memory SQLite)
    └── test_payment_service.py      # Тесты платёжного сервиса
```

## API

### `GET /orders/{order_id}`

Возвращает заказ со всеми платежами.

### `POST /payments`

Создаёт платёж (депозит) по заказу.

Тело запроса:
```json
{
  "order_id": "uuid",
  "amount": 500.00,
  "type": "cash"
}
```

`type` — `"cash"` или `"acquiring"`.

### `POST /payments/{payment_id}/refund`

Создаёт возврат по существующему платежу.

Тело запроса:
```json
{
  "amount": 200.00
}
```

### `GET /health`

Проверка работоспособности. Возвращает `{"status": "ok"}`.

## Архитектурные решения

- **Слоёная архитектура**: `api → services → models → infrastructure`. Роутеры не содержат бизнес-логики, сервисы не знают про HTTP.
- **Single Table для платежей**: наличные и эквайринг хранятся в одной таблице. Поля `bank_*` заполняются только для эквайринга. Это позволяет работать с платежами единообразно, не задумываясь о типе.
- **Сервисные функции принимают session**: это позволяет вызывать `deposit()` и `refund()` не только из REST-ручек, но и из фоновых задач, скриптов, тестов.
- **Синхронизация с банком** (`bank/sync.py`): отдельный модуль, который запрашивает актуальный статус у банка и обновляет локальные данные. Учитывает, что банк может изменить статус в любой момент.
