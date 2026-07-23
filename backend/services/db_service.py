"""
数据库服务模块
负责与 PostgreSQL 数据库的交互
"""

import os
from typing import Optional, List
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库服务"""

    def __init__(self):
        self.db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://tradingos:tradingos_password@192.168.31.132:5432/tradingos",
        )
        self.engine = None
        self._connect()

    def _connect(self):
        """建立数据库连接"""
        try:
            self.engine = create_engine(
                self.db_url,
                poolclass=NullPool,
                isolation_level="AUTOCOMMIT",
            )
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def _convert_params(self, params: dict) -> dict:
        """将 numpy 类型转换为 Python 原生类型"""
        if not params:
            return params
        result = {}
        for k, v in params.items():
            if hasattr(v, 'item'):  # numpy type
                result[k] = v.item()
            elif isinstance(v, (list, tuple)):
                result[k] = [x.item() if hasattr(x, 'item') else x for x in v]
            else:
                result[k] = v
        return result

    def execute(self, sql: str, params: dict = None) -> None:
        """执行 SQL 语句"""
        with self.engine.connect() as conn:
            if params:
                conn.execute(text(sql), self._convert_params(params))
            else:
                conn.execute(text(sql))

    def fetch_one(self, sql: str, params: dict = None) -> Optional[dict]:
        """查询单条记录"""
        with self.engine.connect() as conn:
            if params:
                result = conn.execute(text(sql), params)
            else:
                result = conn.execute(text(sql))
            row = result.fetchone()
            if row:
                return dict(row._mapping)
            return None

    def fetch_all(self, sql: str, params: dict = None) -> List[dict]:
        """查询多条记录"""
        with self.engine.connect() as conn:
            if params:
                result = conn.execute(text(sql), params)
            else:
                result = conn.execute(text(sql))
            return [dict(row._mapping) for row in result]

    def to_df(self, sql: str, params: dict = None) -> pd.DataFrame:
        """查询并返回 DataFrame"""
        with self.engine.connect() as conn:
            if params:
                df = pd.read_sql(text(sql), conn, params=params)
            else:
                df = pd.read_sql(text(sql), conn)
            return df

    # ==================== 股票基础信息 ====================

    def get_stock(self, code: str) -> Optional[dict]:
        """获取股票信息"""
        sql = "SELECT * FROM base.stock_info WHERE symbol = :code"
        return self.fetch_one(sql, {"code": code})

    def upsert_stock(self, data: dict) -> None:
        """插入或更新股票信息"""
        sql = """
        INSERT INTO base.stock_info (
            symbol, name, exchange, industry, sector,
            market_cap, float_cap, listing_date, status, updated_at
        ) VALUES (
            :symbol, :name, :exchange, :industry, :sector,
            :market_cap, :float_cap, :listing_date, :status, NOW()
        )
        ON CONFLICT (symbol) DO UPDATE SET
            name = EXCLUDED.name,
            price = EXCLUDED.price,
            updated_at = NOW()
        """

    def get_all_stocks(self) -> List[dict]:
        """获取所有股票"""
        sql = "SELECT * FROM base.stock_info ORDER BY symbol"
        return self.fetch_all(sql)

    # ==================== K线数据 ====================

    def get_daily_kline(self, code: str, days: int = 60) -> List[dict]:
        """获取日K线数据"""
        sql = """
        SELECT * FROM market.stock_daily_k
        WHERE symbol = :code
        ORDER BY trade_date DESC
        LIMIT :days
        """
        return self.fetch_all(sql, {"code": code, "days": days})

    def insert_daily_kline(self, records: List[dict]) -> None:
        """批量插入日K线数据"""
        if not records:
            return

        for record in records:
            sql = """
            INSERT INTO market.stock_daily_k (
                symbol, trade_date, open, high, low, close,
                volume, amount, turnover, change_percent
            ) VALUES (
                :symbol, :trade_date, :open, :high, :low, :close,
                :volume, :amount, :turnover, :change_percent
            )
            ON CONFLICT (symbol, trade_date) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                amount = EXCLUDED.amount,
                turnover = EXCLUDED.turnover,
                change_percent = EXCLUDED.change_percent
            """
            self.execute(sql, record)

    def get_minute_kline(
        self, code: str, period: str = "5min", limit: int = 100
    ) -> List[dict]:
        """获取分钟K线数据"""
        sql = """
        SELECT * FROM market.stock_minute_k
        WHERE symbol = :code AND period = :period
        ORDER BY timestamp DESC
        LIMIT :limit
        """
        return self.fetch_all(sql, {"code": code, "period": period, "limit": limit})

    def insert_minute_kline(self, records: List[dict]) -> None:
        """批量插入分钟K线数据"""
        if not records:
            return

        for record in records:
            sql = """
            INSERT INTO market.stock_minute_k (
                symbol, timestamp, period, open, high, low, close, volume, amount
            ) VALUES (
                :symbol, :timestamp, :period, :open, :high, :low, :close, :volume, :amount
            )
            ON CONFLICT (symbol, timestamp, period) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume,
                amount = EXCLUDED.amount
            """
            self.execute(sql, record)

    # ==================== 技术指标 ====================

    def get_latest_indicator(self, code: str) -> Optional[dict]:
        """获取最新技术指标"""
        sql = """
        SELECT * FROM indicator.technical_indicator
        WHERE symbol = :code
        ORDER BY trade_date DESC
        LIMIT 1
        """
        return self.fetch_one(sql, {"code": code})

    def insert_indicator(self, record: dict) -> None:
        """插入技术指标"""
        sql = """
        INSERT INTO indicator.technical_indicator (
            symbol, trade_date, ma5, ma10, ma20, ma60, ma120, ma250,
            ema12, ema26, dif, dea, macd,
            rsi6, rsi12, rsi24,
            boll_upper, boll_mid, boll_lower,
            kdj_k, kdj_d, kdj_j
        ) VALUES (
            :symbol, :trade_date, :ma5, :ma10, :ma20, :ma60, :ma120, :ma250,
            :ema12, :ema26, :dif, :dea, :macd,
            :rsi6, :rsi12, :rsi24,
            :boll_upper, :boll_mid, :boll_lower,
            :kdj_k, :kdj_d, :kdj_j
        )
        ON CONFLICT (symbol, trade_date) DO UPDATE SET
            ma5 = EXCLUDED.ma5, ma10 = EXCLUDED.ma10, ma20 = EXCLUDED.ma20,
            ma60 = EXCLUDED.ma60, ma120 = EXCLUDED.ma120, ma250 = EXCLUDED.ma250,
            ema12 = EXCLUDED.ema12, ema26 = EXCLUDED.ema26,
            dif = EXCLUDED.dif, dea = EXCLUDED.dea, macd = EXCLUDED.macd,
            rsi6 = EXCLUDED.rsi6, rsi12 = EXCLUDED.rsi12, rsi24 = EXCLUDED.rsi24,
            boll_upper = EXCLUDED.boll_upper, boll_mid = EXCLUDED.boll_mid, boll_lower = EXCLUDED.boll_lower,
            kdj_k = EXCLUDED.kdj_k, kdj_d = EXCLUDED.kdj_d, kdj_j = EXCLUDED.kdj_j
        """
        self.execute(sql, record)

    # ==================== 资金数据 ====================

    def get_money_flow(self, code: str, days: int = 30) -> List[dict]:
        """获取资金流数据"""
        sql = """
        SELECT * FROM fund.stock_money_flow
        WHERE symbol = :code
        ORDER BY trade_date DESC
        LIMIT :days
        """
        return self.fetch_all(sql, {"code": code, "days": days})

    def insert_money_flow(self, record: dict) -> None:
        """插入资金流数据"""
        sql = """
        INSERT INTO fund.stock_money_flow (
            symbol, trade_date,
            main_inflow, main_outflow,
            super_large_in, super_large_out,
            large_in, large_out,
            medium_in, medium_out,
            small_in, small_out
        ) VALUES (
            :symbol, :trade_date,
            :main_inflow, :main_outflow,
            :super_large_in, :super_large_out,
            :large_in, :large_out,
            :medium_in, :medium_out,
            :small_in, :small_out
        )
        ON CONFLICT (symbol, trade_date) DO UPDATE SET
            main_inflow = EXCLUDED.main_inflow,
            main_outflow = EXCLUDED.main_outflow,
            super_large_in = EXCLUDED.super_large_in,
            super_large_out = EXCLUDED.super_large_out,
            large_in = EXCLUDED.large_in,
            large_out = EXCLUDED.large_out,
            medium_in = EXCLUDED.medium_in,
            medium_out = EXCLUDED.medium_out,
            small_in = EXCLUDED.small_in,
            small_out = EXCLUDED.small_out
        """
        self.execute(sql, record)

    def get_north_money(self, days: int = 30) -> List[dict]:
        """获取北向资金数据"""
        sql = """
        SELECT * FROM fund.north_money
        ORDER BY trade_date DESC
        LIMIT :days
        """
        return self.fetch_all(sql, {"days": days})

    def insert_north_money(self, record: dict) -> None:
        """插入北向资金数据"""
        sql = """
        INSERT INTO fund.north_money (trade_date, sh_connect, sz_connect, total)
        VALUES (:trade_date, :sh_connect, :sz_connect, :total)
        ON CONFLICT (trade_date) DO UPDATE SET
            sh_connect = EXCLUDED.sh_connect,
            sz_connect = EXCLUDED.sz_connect,
            total = EXCLUDED.total
        """
        self.execute(sql, record)

    # ==================== 统计查询 ====================

    def get_stock_count(self) -> int:
        """获取股票总数"""
        sql = "SELECT COUNT(*) as count FROM base.stock_info"
        result = self.fetch_one(sql)
        return result["count"] if result else 0

    def get_kline_count(self, code: str = None) -> int:
        """获取K线数据条数"""
        if code:
            sql = "SELECT COUNT(*) as count FROM market.stock_daily_k WHERE symbol = :code"
            result = self.fetch_one(sql, {"code": code})
        else:
            sql = "SELECT COUNT(*) as count FROM market.stock_daily_k"
            result = self.fetch_one(sql)
        return result["count"] if result else 0


# 全局实例
db_service = DatabaseService()


if __name__ == "__main__":
    # 测试数据库连接
    print("=== 测试数据库连接 ===")
    count = db_service.get_stock_count()
    print(f"当前股票总数: {count}")

    kline_count = db_service.get_kline_count()
    print(f"K线数据总条数: {kline_count}")
