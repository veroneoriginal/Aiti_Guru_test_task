-- schema.sql
-- Схема базы данных сервиса платежей
-- PostgreSQL 15+

CREATE
EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Таблица заказов
-- =====================================================
CREATE TABLE orders
(
    id         UUID PRIMARY KEY        DEFAULT uuid_generate_v4(),
    amount     NUMERIC(12, 2) NOT NULL,
    status     VARCHAR(20)    NOT NULL DEFAULT 'unpaid'
        CHECK (status IN ('unpaid', 'partial', 'paid')),
    created_at TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ    NOT NULL DEFAULT now()
);

COMMENT
ON COLUMN orders.amount IS 'Итоговая сумма заказа';
COMMENT
ON COLUMN orders.status IS 'Статус оплаты: unpaid / partial / paid';

-- =====================================================
-- Таблица платежей
-- =====================================================
CREATE TABLE payments
(
    id              UUID PRIMARY KEY        DEFAULT uuid_generate_v4(),
    order_id        UUID           NOT NULL
        REFERENCES orders (id) ON DELETE RESTRICT,
    type            VARCHAR(20)    NOT NULL
        CHECK (type IN ('cash', 'acquiring')),
    operation       VARCHAR(20)    NOT NULL
        CHECK (operation IN ('deposit', 'refund')),
    amount          NUMERIC(12, 2) NOT NULL
        CONSTRAINT ck_payment_amount_positive CHECK (amount > 0),
    status          VARCHAR(20)    NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'completed', 'failed')),
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ    NOT NULL DEFAULT now(),

    -- Поля эквайринга (NULL для наличных)
    bank_payment_id VARCHAR(255) UNIQUE,
    bank_status     VARCHAR(50),
    bank_paid_at    TIMESTAMPTZ
);

CREATE INDEX ix_payments_order_id ON payments (order_id);

COMMENT
ON COLUMN payments.type            IS 'Тип: cash / acquiring';
COMMENT
ON COLUMN payments.operation       IS 'Операция: deposit / refund';
COMMENT
ON COLUMN payments.amount          IS 'Сумма (всегда > 0)';
COMMENT
ON COLUMN payments.status          IS 'Статус: pending / completed / failed';
COMMENT
ON COLUMN payments.bank_payment_id IS 'ID платежа на стороне банка';
COMMENT
ON COLUMN payments.bank_status     IS 'Статус по данным банка';
COMMENT
ON COLUMN payments.bank_paid_at    IS 'Дата/время оплаты по данным банка';
