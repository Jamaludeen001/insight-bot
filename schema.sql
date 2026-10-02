-- schema.sql
-- Run once: psql -U postgres -d insightbot -f schema.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Products tracking ────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    order_id        VARCHAR(50)  PRIMARY KEY,
    product_id      VARCHAR(50)  NOT NULL,
    product_name    VARCHAR(255) NOT NULL,
    customer_name   VARCHAR(255),
    purchase_date   DATE,
    warranty_status VARCHAR(20)  DEFAULT 'active',
    is_crt          BOOLEAN      DEFAULT FALSE,
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ── Damage reports ───────────────────────────────────
CREATE TABLE IF NOT EXISTS damage_reports (
    tracking_id       UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id          VARCHAR(50)  NOT NULL REFERENCES products(order_id),
    feedback          TEXT,
    sentiment         VARCHAR(20),
    sentiment_score   NUMERIC(4,3),
    damage_severity   NUMERIC(4,3),
    damage_details    JSONB,
    warranty_claim_id VARCHAR(50),
    status            VARCHAR(20)  DEFAULT 'open',
    created_at        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_order   ON damage_reports(order_id);
CREATE INDEX IF NOT EXISTS idx_products_crt    ON products(is_crt);

-- ── Seed data (for testing) ──────────────────────────
INSERT INTO products (order_id, product_id, product_name, customer_name, purchase_date, is_crt)
VALUES
    ('ORD-1001', 'SHOE-X1', 'Running Shoe X1',  'Alice',  '2026-01-15', TRUE),
    ('ORD-1002', 'SHIRT-M2','Cotton Shirt M2',  'Bob',    '2026-02-01', FALSE),
    ('ORD-1003', 'BAG-CRT9','CRT Travel Bag',   'Carol',  '2025-12-10', TRUE)
ON CONFLICT (order_id) DO NOTHING;