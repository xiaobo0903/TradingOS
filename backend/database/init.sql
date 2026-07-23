-- ================================================
-- TradingOS 数据库初始化脚本
-- 数据库选型: PostgreSQL + TimescaleDB + Redis + ChromaDB
-- ================================================

-- 1. 创建数据库
CREATE DATABASE tradingos;
\c tradingos;

-- ================================================
-- 2. 启用扩展
-- ================================================
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
-- CREATE EXTENSION IF NOT EXISTS vector;

-- ================================================
-- 3. Schema 创建
-- ================================================
CREATE SCHEMA base;        -- 基础数据
CREATE SCHEMA market;      -- 行情数据
CREATE SCHEMA indicator;    -- 技术指标
CREATE SCHEMA fund;         -- 资金数据
CREATE SCHEMA ai;           -- AI数据
CREATE SCHEMA user_schema;  -- 用户系统

-- ================================================
-- 4. 基础数据表 (base)
-- ================================================

-- 4.1 股票基本信息表
CREATE TABLE base.stock_info (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,      -- 股票代码
    name VARCHAR(50) NOT NULL,               -- 股票名称
    exchange VARCHAR(10) NOT NULL,           -- 交易所 (SH/SZ)
    industry VARCHAR(50),                    -- 行业
    sector VARCHAR(50),                     -- 板块
    market_cap DECIMAL(18,2),             -- 总市值
    float_cap DECIMAL(18,2),               -- 流通市值
    listing_date DATE,                     -- 上市日期
    status VARCHAR(10) DEFAULT 'ACTIVE',   -- 状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_symbol ON base.stock_info(symbol);
CREATE INDEX idx_stock_industry ON base.stock_info(industry);

-- 4.2 股票分类表 (热点、概念、行业)
CREATE TABLE base.stock_category (
    id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL,
    category_type VARCHAR(20) NOT NULL,      -- 'hot'/'concept'/'industry'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4.3 股票-分类关联表
CREATE TABLE base.stock_category_relation (
    stock_id INTEGER REFERENCES base.stock_info(id),
    category_id INTEGER REFERENCES base.stock_category(id),
    PRIMARY KEY (stock_id, category_id)
);

-- ================================================
-- 5. 行情数据表 (market) - TimescaleDB hypertable
-- ================================================

-- 5.1 日K数据表
CREATE TABLE market.stock_daily_k (
    id SERIAL,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open DECIMAL(10,2) NOT NULL,
    high DECIMAL(10,2) NOT NULL,
    low DECIMAL(10,2) NOT NULL,
    close DECIMAL(10,2) NOT NULL,
    volume BIGINT NOT NULL,
    amount DECIMAL(18,2),
    turnover DECIMAL(10,2),
    change_percent DECIMAL(10,2),
    PRIMARY KEY (symbol, trade_date)
);

SELECT create_hypertable('market.stock_daily_k', 'trade_date',
    chunk_time_interval => INTERVAL '1 month');

CREATE INDEX idx_daily_k_symbol ON market.stock_daily_k(symbol);
CREATE INDEX idx_daily_k_date ON market.stock_daily_k(trade_date DESC);

-- 5.2 分钟K数据表
CREATE TABLE market.stock_minute_k (
    id SERIAL,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    period VARCHAR(10) NOT NULL,            -- '1min'/'5min'/'15min'/'30min'/'60min'
    open DECIMAL(10,2) NOT NULL,
    high DECIMAL(10,2) NOT NULL,
    low DECIMAL(10,2) NOT NULL,
    close DECIMAL(10,2) NOT NULL,
    volume BIGINT NOT NULL,
    amount DECIMAL(18,2),
    PRIMARY KEY (symbol, timestamp, period)
);

SELECT create_hypertable('market.stock_minute_k', 'timestamp',
    chunk_time_interval => INTERVAL '1 day');

CREATE INDEX idx_minute_k_symbol_period ON market.stock_minute_k(symbol, period);
CREATE INDEX idx_minute_k_timestamp ON market.stock_minute_k(timestamp DESC);

-- 5.3 Tick成交数据
CREATE TABLE market.stock_tick (
    id BIGSERIAL,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    volume BIGINT NOT NULL,
    amount DECIMAL(18,2),
    direction VARCHAR(10),                  -- 'BUY'/'SELL'/'UNKNOWN'
    PRIMARY KEY (symbol, timestamp, id)
);

SELECT create_hypertable('market.stock_tick', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour');

CREATE INDEX idx_tick_symbol ON market.stock_tick(symbol);
CREATE INDEX idx_tick_timestamp ON market.stock_tick(timestamp DESC);

-- 5.4 五档盘口
CREATE TABLE market.stock_order_book (
    id SERIAL,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    bid_price1 DECIMAL(10,2), bid_volume1 BIGINT,
    bid_price2 DECIMAL(10,2), bid_volume2 BIGINT,
    bid_price3 DECIMAL(10,2), bid_volume3 BIGINT,
    bid_price4 DECIMAL(10,2), bid_volume4 BIGINT,
    bid_price5 DECIMAL(10,2), bid_volume5 BIGINT,
    ask_price1 DECIMAL(10,2), ask_volume1 BIGINT,
    ask_price2 DECIMAL(10,2), ask_volume2 BIGINT,
    ask_price3 DECIMAL(10,2), ask_volume3 BIGINT,
    ask_price4 DECIMAL(10,2), ask_volume4 BIGINT,
    ask_price5 DECIMAL(10,2), ask_volume5 BIGINT,
    PRIMARY KEY (symbol, timestamp)
);

SELECT create_hypertable('market.stock_order_book', 'timestamp',
    chunk_time_interval => INTERVAL '1 day');

CREATE INDEX idx_orderbook_symbol ON market.stock_order_book(symbol);

-- ================================================
-- 6. 技术指标表 (indicator)
-- ================================================

-- 6.1 技术指标表
CREATE TABLE indicator.technical_indicator (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    ma5 DECIMAL(10,2),
    ma10 DECIMAL(10,2),
    ma20 DECIMAL(10,2),
    ma60 DECIMAL(10,2),
    ma120 DECIMAL(10,2),
    ma250 DECIMAL(10,2),
    ema12 DECIMAL(10,2),
    ema26 DECIMAL(10,2),
    dif DECIMAL(10,4),
    dea DECIMAL(10,4),
    macd DECIMAL(10,4),
    rsi6 DECIMAL(10,2),
    rsi12 DECIMAL(10,2),
    rsi24 DECIMAL(10,2),
    boll_upper DECIMAL(10,2),
    boll_mid DECIMAL(10,2),
    boll_lower DECIMAL(10,2),
    kdj_k DECIMAL(10,2),
    kdj_d DECIMAL(10,2),
    kdj_j DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, trade_date)
);

CREATE INDEX idx_indicator_symbol ON indicator.technical_indicator(symbol);
CREATE INDEX idx_indicator_date ON indicator.technical_indicator(trade_date DESC);

-- 6.2 技术信号表
CREATE TABLE indicator.technical_signal (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    signal_date DATE NOT NULL,
    signal_type VARCHAR(50) NOT NULL,       -- 'MACD金叉'/'RSI超卖'/'BOLL突破'/'均线多头'
    confidence INTEGER,                     -- 可信度 0-100
    description TEXT,
    price DECIMAL(10,2),                   -- 信号发生时价格
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signal_symbol ON indicator.technical_signal(symbol);
CREATE INDEX idx_signal_type ON indicator.technical_signal(signal_type);

-- 6.3 K线形态表
CREATE TABLE indicator.candle_pattern (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    pattern_date DATE NOT NULL,
    pattern_name VARCHAR(50) NOT NULL,    -- '早晨之星'/'黄昏之星'/'乌云盖顶'
    position VARCHAR(20),                  -- '底部'/'顶部'
    score INTEGER,                          -- 可信度 0-100
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pattern_symbol ON indicator.candle_pattern(symbol);

-- ================================================
-- 7. 资金数据表 (fund)
-- ================================================

-- 7.1 股票资金流向
CREATE TABLE fund.stock_money_flow (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    main_inflow DECIMAL(18,2),           -- 主力净流入
    main_outflow DECIMAL(18,2),
    net_inflow DECIMAL(18,2),
    super_large_in DECIMAL(18,2),         -- 超大单
    super_large_out DECIMAL(18,2),
    large_in DECIMAL(18,2),                -- 大单
    large_out DECIMAL(18,2),
    medium_in DECIMAL(18,2),               -- 中单
    medium_out DECIMAL(18,2),
    small_in DECIMAL(18,2),                -- 散户
    small_out DECIMAL(18,2),
    UNIQUE (symbol, trade_date)
);

CREATE INDEX idx_flow_symbol ON fund.stock_money_flow(symbol);
CREATE INDEX idx_flow_date ON fund.stock_money_flow(trade_date DESC);

-- 7.2 北向资金
CREATE TABLE fund.north_money (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL UNIQUE,
    sh_connect DECIMAL(18,2),             -- 沪股通
    sz_connect DECIMAL(18,2),             -- 深股通
    total DECIMAL(18,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_north_date ON fund.north_money(trade_date DESC);

-- 7.3 龙虎榜
CREATE TABLE fund.dragon_tiger (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50),
    reason TEXT,                            -- 上榜原因
    buy_amount DECIMAL(18,2),             -- 买入金额
    sell_amount DECIMAL(18,2),            -- 卖出金额
    net_amount DECIMAL(18,2),             -- 净买入
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dragon_date ON fund.dragon_tiger(trade_date DESC);
CREATE INDEX idx_dragon_symbol ON fund.dragon_tiger(symbol);

-- ================================================
-- 8. AI分析数据表 (ai)
-- ================================================

-- 8.1 AI股票分析报告
CREATE TABLE ai.ai_stock_report (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    report_date DATE NOT NULL,
    trend VARCHAR(20),                     -- '上涨'/'下跌'/'震荡'
    score INTEGER,                          -- 综合评分 0-100
    confidence INTEGER,                     -- 可信度
    technical_analysis JSONB,              -- 技术分析
    fund_analysis JSONB,                  -- 资金分析
    risk TEXT[],                          -- 风险提示
    suggestion TEXT,                      -- 操作建议
    model VARCHAR(50),                    -- AI模型
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (symbol, report_date)
);

CREATE INDEX idx_ai_report_symbol ON ai.ai_stock_report(symbol);
CREATE INDEX idx_ai_report_date ON ai.ai_stock_report(report_date DESC);

-- 8.2 AI对话记录
CREATE TABLE ai.ai_chat (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    question TEXT NOT NULL,
    answer TEXT,
    context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8.3 RAG知识库文档
CREATE TABLE ai.knowledge_document (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,         -- '股票基础'/'技术分析'/'主力行为'
    content TEXT NOT NULL,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_knowledge_category ON ai.knowledge_document(category);

-- 8.4 知识库向量 (使用 ChromaDB，不在 PostgreSQL 中存储向量)
-- 注意：向量数据存储在 ChromaDB 中，PostgreSQL 只存储关联元数据

-- 8.5 主力行为分析
CREATE TABLE ai.main_force_behavior (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    behavior_date DATE NOT NULL,
    behavior VARCHAR(20) NOT NULL,         -- '吸筹'/'洗盘'/'拉升'/'出货'
    score INTEGER,                          -- 概率 0-100
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_force_symbol ON ai.main_force_behavior(symbol);
CREATE INDEX idx_force_behavior ON ai.main_force_behavior(behavior);

-- 8.6 涨停分析
CREATE TABLE ai.limit_up_analysis (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    limit_type VARCHAR(30),              -- '一字板'/'放量涨停'/'缩量涨停'/'开板回封'
    seal_amount DECIMAL(18,2),           -- 封单金额
    turnover_rate DECIMAL(10,2),          -- 换手率
    analysis TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- 9. 用户系统表 (user_schema)
-- ================================================

-- 9.1 用户表
CREATE TABLE user_schema.users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,       -- bcrypt hash
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'USER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9.2 自选股
CREATE TABLE user_schema.favorite_stock (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_schema.users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    group_name VARCHAR(50) DEFAULT '默认',
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, symbol)
);

CREATE INDEX idx_favorite_user ON user_schema.favorite_stock(user_id);

-- 9.3 交易记录
CREATE TABLE user_schema.trade_record (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_schema.users(id) ON DELETE CASCADE,
    symbol VARCHAR(10) NOT NULL,
    direction VARCHAR(10),               -- 'BUY'/'SELL'
    buy_price DECIMAL(10,2),
    sell_price DECIMAL(10,2),
    volume INTEGER,
    profit DECIMAL(18,2),
    reason TEXT,
    trade_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trade_user ON user_schema.trade_record(user_id);

-- 9.4 AI Prompt模板
CREATE TABLE user_schema.ai_prompt (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version INTEGER DEFAULT 1,
    prompt TEXT NOT NULL,
    model VARCHAR(50),
    temperature DECIMAL(3,2) DEFAULT 0.7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- 10. 系统配置表
-- ================================================

CREATE TABLE base.system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10.1 数据源配置
CREATE TABLE base.data_source (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    source_type VARCHAR(20),              -- 'api'/'crawler'/'file'
    url VARCHAR(500),
    api_key VARCHAR(255),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    last_update TIMESTAMP,
    data_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10.2 数据异常记录
CREATE TABLE base.data_error (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES base.data_source(id),
    error_type VARCHAR(50),
    error_message TEXT,
    error_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'PENDING',  -- 'PENDING'/'FIXED'/'IGNORED'
    resolved_at TIMESTAMP,
    resolved_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- 11. 股票评分表
-- ================================================

CREATE TABLE base.stock_score (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    score_date DATE NOT NULL,
    technical_score INTEGER,
    fund_score INTEGER,
    emotion_score INTEGER,
    hot_score INTEGER,
    total_score INTEGER,
    rank INTEGER,
    UNIQUE (symbol, score_date)
);

CREATE INDEX idx_score_date ON base.stock_score(score_date DESC);
CREATE INDEX idx_score_rank ON base.stock_score(total_score DESC);

-- ================================================
-- 12. 热点数据表
-- ================================================

CREATE TABLE base.market_hotspot (
    id SERIAL PRIMARY KEY,
    trade_date DATE NOT NULL,
    sector VARCHAR(50),
    rise_percent DECIMAL(10,2),
    money_inflow DECIMAL(18,2),
    stock_count INTEGER,
    top_stocks JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_hotspot_date ON base.market_hotspot(trade_date DESC);

-- ================================================
-- 13. 新闻数据表
-- ================================================

CREATE TABLE base.news (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source VARCHAR(50),
    publish_time TIMESTAMP,
    url VARCHAR(500),
    sentiment VARCHAR(20),               -- '利好'/'利空'/'中性'
    related_stocks JSONB,               -- 相关股票代码列表
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_news_publish ON base.news(publish_time DESC);
CREATE INDEX idx_news_sentiment ON base.news(sentiment);

-- ================================================
-- 14. 策略表
-- ================================================

CREATE TABLE base.trading_strategy (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    conditions JSONB NOT NULL,           -- 策略条件
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================
-- 15. 初始化配置数据
-- ================================================

INSERT INTO base.system_config (config_key, config_value, description) VALUES
('AI_MODEL', 'Qwen3-14B', '当前使用的AI模型'),
('DATA_REFRESH_INTERVAL', '5', '行情数据刷新间隔(秒)'),
('THEME', 'dark', '系统主题');

-- ================================================
-- 16. 创建只读用户(可选)
-- ================================================
-- CREATE USER tradingos_read WITH PASSWORD 'readonly_password';
-- GRANT SELECT ON ALL TABLES IN SCHEMA base TO tradingos_read;
-- GRANT SELECT ON ALL TABLES IN SCHEMA market TO tradingos_read;
-- GRANT SELECT ON ALL TABLES IN SCHEMA indicator TO tradingos_read;
-- GRANT SELECT ON ALL TABLES IN SCHEMA fund TO tradingos_read;
-- GRANT SELECT ON ALL TABLES IN SCHEMA ai TO tradingos_read;

COMMENT ON DATABASE tradingos IS 'TradingOS - 智能股票分析系统数据库';
