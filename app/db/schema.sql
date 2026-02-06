CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    entry_time TIMESTAMPTZ NOT NULL,
    exit_time TIMESTAMPTZ,
    total_time_spent DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS movements (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    x_coordinate DOUBLE PRECISION NOT NULL,
    y_coordinate DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_movements_customer_time ON movements(customer_id, timestamp);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(80) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    camera_id VARCHAR(80) NOT NULL,
    severity VARCHAR(20) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_type_time ON alerts(alert_type, timestamp DESC);

CREATE TABLE IF NOT EXISTS product_interactions (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    product_class VARCHAR(120) NOT NULL,
    dwell_time DOUBLE PRECISION NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_product_interactions_customer ON product_interactions(customer_id);
