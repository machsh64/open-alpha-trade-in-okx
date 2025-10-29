-- AI Trading Database Schema for PostgreSQL
-- Database: ai-trade
-- Connection: postgresql://user:pwd@ip:port/ai-trade

-- 1. Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    is_active VARCHAR(10) NOT NULL DEFAULT 'true',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);

-- 2. Accounts Table
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version VARCHAR(100) NOT NULL DEFAULT 'v1',
    name VARCHAR(100) NOT NULL,
    account_type VARCHAR(20) NOT NULL DEFAULT 'AI',
    is_active VARCHAR(10) NOT NULL DEFAULT 'true',
    
    -- AI Model Configuration
    model VARCHAR(100) DEFAULT 'gpt-4',
    base_url VARCHAR(500) DEFAULT 'https://api.openai.com/v1',
    api_key VARCHAR(500),
    
    -- OKX Trading Configuration
    okx_api_key VARCHAR(500),
    okx_secret VARCHAR(500),
    okx_passphrase VARCHAR(500),
    okx_sandbox VARCHAR(10) DEFAULT 'true',
    
    -- Account Balances
    initial_capital DECIMAL(18, 2) NOT NULL DEFAULT 10000.00,
    current_cash DECIMAL(18, 2) NOT NULL DEFAULT 10000.00,
    frozen_cash DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_accounts_is_active ON accounts(is_active);

-- 3. User Auth Sessions Table
CREATE TABLE user_auth_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_auth_sessions_token ON user_auth_sessions(session_token);
CREATE INDEX idx_user_auth_sessions_user_id ON user_auth_sessions(user_id);

-- 4. Positions Table
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(100) NOT NULL DEFAULT 'v1',
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL DEFAULT 0,
    available_quantity DECIMAL(18, 8) NOT NULL DEFAULT 0,
    avg_cost DECIMAL(18, 6) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_positions_account_id ON positions(account_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);

-- 5. Orders Table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    version VARCHAR(100) NOT NULL DEFAULT 'v1',
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    order_no VARCHAR(32) UNIQUE NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL DEFAULT 'CRYPTO',
    side VARCHAR(10) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    price DECIMAL(18, 6),
    quantity DECIMAL(18, 8) NOT NULL,
    filled_quantity DECIMAL(18, 8) NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_account_id ON orders(account_id);
CREATE INDEX idx_orders_order_no ON orders(order_no);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- 6. Trades Table
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(10) NOT NULL DEFAULT 'CRYPTO',
    side VARCHAR(10) NOT NULL,
    price DECIMAL(18, 6) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    commission DECIMAL(18, 6) NOT NULL DEFAULT 0,
    trade_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_account_id ON trades(account_id);
CREATE INDEX idx_trades_order_id ON trades(order_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_trade_time ON trades(trade_time);

-- 7. Trading Configs Table
CREATE TABLE trading_configs (
    id SERIAL PRIMARY KEY,
    version VARCHAR(100) NOT NULL DEFAULT 'v1',
    market VARCHAR(10) NOT NULL,
    min_commission FLOAT NOT NULL,
    commission_rate FLOAT NOT NULL,
    exchange_rate FLOAT NOT NULL DEFAULT 1.0,
    min_order_quantity INTEGER NOT NULL DEFAULT 1,
    lot_size INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(market, version)
);

-- 8. System Configs Table
CREATE TABLE system_configs (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value VARCHAR(5000),
    description VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_configs_key ON system_configs(key);

-- 9. Crypto Prices Table
CREATE TABLE crypto_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    market VARCHAR(10) NOT NULL DEFAULT 'CRYPTO',
    price DECIMAL(18, 6) NOT NULL,
    price_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, market, price_date)
);

CREATE INDEX idx_crypto_prices_symbol ON crypto_prices(symbol);
CREATE INDEX idx_crypto_prices_price_date ON crypto_prices(price_date);

-- 10. Crypto Klines Table
CREATE TABLE crypto_klines (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    market VARCHAR(10) NOT NULL DEFAULT 'CRYPTO',
    period VARCHAR(10) NOT NULL,
    timestamp BIGINT NOT NULL,
    datetime_str VARCHAR(50) NOT NULL,
    open_price DECIMAL(18, 6),
    high_price DECIMAL(18, 6),
    low_price DECIMAL(18, 6),
    close_price DECIMAL(18, 6),
    volume DECIMAL(18, 2),
    amount DECIMAL(18, 2),
    change DECIMAL(18, 6),
    percent DECIMAL(10, 4),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, market, period, timestamp)
);

CREATE INDEX idx_crypto_klines_symbol ON crypto_klines(symbol);
CREATE INDEX idx_crypto_klines_timestamp ON crypto_klines(timestamp);

-- 11. AI Decision Logs Table
CREATE TABLE ai_decision_logs (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    decision_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(1000) NOT NULL,
    prompt TEXT,
    operation VARCHAR(50) NOT NULL,
    symbol VARCHAR(20),
    prev_portion DECIMAL(10, 6) NOT NULL DEFAULT 0,
    target_portion DECIMAL(10, 6) NOT NULL,
    leverage INTEGER DEFAULT 1,
    total_balance DECIMAL(18, 2) NOT NULL,
    executed VARCHAR(10) NOT NULL DEFAULT 'false',
    order_id INTEGER REFERENCES orders(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_decision_logs_account_id ON ai_decision_logs(account_id);
CREATE INDEX idx_ai_decision_logs_decision_time ON ai_decision_logs(decision_time);

-- Insert default trading config for CRYPTO market
INSERT INTO trading_configs (market, min_commission, commission_rate, exchange_rate, min_order_quantity, lot_size)
VALUES ('CRYPTO', 0.1, 0.001, 1.0, 1, 1)
ON CONFLICT (market, version) DO NOTHING;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trading_configs_updated_at BEFORE UPDATE ON trading_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_configs_updated_at BEFORE UPDATE ON system_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_crypto_prices_updated_at BEFORE UPDATE ON crypto_prices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions to letta user (if needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO machsh;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO machsh;
