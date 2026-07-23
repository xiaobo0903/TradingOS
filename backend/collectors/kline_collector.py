"""
K线数据采集模块
使用 AKShare 获取日K、分钟K线数据
"""

import akshare as ak
import pandas as pd
from typing import Literal, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KlineCollector:
    """K线数据采集器"""

    def __init__(self):
        self.period_map = {
            "daily": "日K",
            "weekly": "周K",
            "monthly": "月K",
            "1": "1分钟",
            "5": "5分钟",
            "15": "15分钟",
            "30": "30分钟",
            "60": "60分钟",
        }

    def get_daily_kline(
        self,
        symbol: str,
        start_date: str = "20200101",
        end_date: str = None,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """
        获取日K线数据

        Args:
            symbol: 股票代码，如 "600519"
            start_date: 开始日期，格式 YYYYMMDD
            end_date: 结束日期，格式 YYYYMMDD，None 表示今天
            adjust: 复权类型，"qfq"前复权，"hfq"后复权，"None"不复权
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        logger.info(f"正在获取 {symbol} 日K线数据...")
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
            )
            logger.info(f"获取到 {len(df)} 条日K数据")
            return df
        except Exception as e:
            logger.error(f"获取日K线失败: {e}")
            return pd.DataFrame()

    def get_minute_kline(
        self,
        symbol: str,
        period: Literal["1", "5", "15", "30", "60"] = "5",
        start_date: str = None,
        end_date: str = None,
    ) -> pd.DataFrame:
        """
        获取分钟K线数据

        Args:
            symbol: 股票代码，如 "600519"
            period: 分钟周期，"1", "5", "15", "30", "60"
            start_date: 开始日期，格式 YYYYMMDD HH:MM:SS
            end_date: 结束日期，格式 YYYYMMDD HH:MM:SS
        """
        logger.info(f"正在获取 {symbol} {period}分钟K线数据...")
        try:
            # AKShare 的分钟数据接口
            df = ak.stock_zh_a_minute(
                symbol=self._format_symbol_for_api(symbol),
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )
            logger.info(f"获取到 {len(df)} 条分钟K数据")
            return df
        except Exception as e:
            logger.error(f"获取分钟K线失败: {e}")
            return pd.DataFrame()

    def get_realtime_kline(self, symbol: str, period: str = "1") -> pd.DataFrame:
        """
        获取实时K线数据（当日分时数据）

        Args:
            symbol: 股票代码
            period: "1" 或 "5"
        """
        logger.info(f"正在获取 {symbol} 实时K线...")
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=datetime.now().strftime("%Y%m%d"),
                end_date=datetime.now().strftime("%Y%m%d"),
                adjust="qfq",
            )
            return df
        except Exception as e:
            logger.error(f"获取实时K线失败: {e}")
            return pd.DataFrame()

    def _format_symbol_for_api(self, symbol: str) -> str:
        """将股票代码格式化为 AKShare 需要的格式"""
        if symbol.startswith("6"):
            return f"sh{symbol}"
        elif symbol.startswith(("0", "3")):
            return f"sz{symbol}"
        return symbol

    def format_daily_for_db(self, df: pd.DataFrame, symbol: str) -> list:
        """
        将日K数据格式化为数据库写入格式
        对应 market.stock_daily_k 表
        """
        records = []
        if df.empty:
            return records

        for _, row in df.iterrows():
            try:
                # AKShare 返回的列名: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
                record = {
                    "symbol": symbol,
                    "trade_date": row.get("日期"),
                    "open": float(row.get("开盘", 0) or 0),
                    "high": float(row.get("最高", 0) or 0),
                    "low": float(row.get("最低", 0) or 0),
                    "close": float(row.get("收盘", 0) or 0),
                    "volume": int(row.get("成交量", 0) or 0),
                    "amount": float(row.get("成交额", 0) or 0),
                    "turnover": float(row.get("换手率", 0) or 0),
                    "change_percent": float(row.get("涨跌幅", 0) or 0),
                }
                records.append(record)
            except Exception as e:
                logger.warning(f"格式化K线数据失败: {e}")
                continue
        return records

    def format_minute_for_db(self, df: pd.DataFrame, symbol: str, period: str) -> list:
        """
        将分钟K数据格式化为数据库写入格式
        对应 market.stock_minute_k 表
        """
        records = []
        if df.empty:
            return records

        for _, row in df.iterrows():
            try:
                record = {
                    "symbol": symbol,
                    "timestamp": row.get("时间") or row.get("Datetime"),
                    "period": f"{period}min",
                    "open": float(row.get("开盘", 0) or 0),
                    "high": float(row.get("最高", 0) or 0),
                    "low": float(row.get("最低", 0) or 0),
                    "close": float(row.get("收盘", 0) or 0),
                    "volume": int(row.get("成交量", 0) or 0),
                    "amount": float(row.get("成交额", 0) or 0),
                }
                records.append(record)
            except Exception as e:
                logger.warning(f"格式化分钟K线失败: {e}")
                continue
        return records


if __name__ == "__main__":
    collector = KlineCollector()

    # 测试获取日K线
    print("=== 测试获取日K线 (贵州茅台 600519) ===")
    df = collector.get_daily_kline("600519", start_date="20240601")
    if not df.empty:
        print(f"获取 {len(df)} 条数据")
        print("列名:", df.columns.tolist())
        print(df.tail(5))

    # 格式化数据
    print("\n=== 格式化后的数据 ===")
    records = collector.format_daily_for_db(df, "600519")
    if records:
        print(records[-1])
