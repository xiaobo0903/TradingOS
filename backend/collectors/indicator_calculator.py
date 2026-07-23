"""
技术指标计算模块
使用 pandas 计算 MACD、RSI、BOLL、KDJ 等技术指标
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """技术指标计算器"""

    def __init__(self):
        pass

    def calculate_ma(self, df: pd.DataFrame, periods: list = [5, 10, 20, 60, 120, 250]) -> pd.DataFrame:
        """
        计算移动平均线 MA

        Args:
            df: 包含 'close' 列的 DataFrame
            periods: MA 周期列表
        """
        result = df.copy()
        for period in periods:
            result[f"ma{period}"] = df["close"].rolling(window=period).mean()
        return result

    def calculate_ema(self, df: pd.DataFrame, periods: list = [12, 26]) -> pd.DataFrame:
        """
        计算指数移动平均线 EMA
        """
        result = df.copy()
        for period in periods:
            result[f"ema{period}"] = df["close"].ewm(span=period, adjust=False).mean()
        return result

    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> pd.DataFrame:
        """
        计算 MACD 指标

        Args:
            df: 包含 'close' 列的 DataFrame
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            添加 dif, dea, macd 列的 DataFrame
        """
        result = df.copy()

        # 计算 EMA
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()

        # DIF = EMA(fast) - EMA(slow)
        result["dif"] = ema_fast - ema_slow

        # DEA = Signal 线（DIF 的 EMA）
        result["dea"] = result["dif"].ewm(span=signal, adjust=False).mean()

        # MACD = (DIF - DEA) * 2
        result["macd"] = (result["dif"] - result["dea"]) * 2

        return result

    def calculate_rsi(self, df: pd.DataFrame, periods: list = [6, 12, 24]) -> pd.DataFrame:
        """
        计算 RSI 相对强弱指标

        Args:
            df: 包含 'close' 列的 DataFrame
            periods: RSI 周期列表
        """
        result = df.copy()

        for period in periods:
            # 计算价格变化
            delta = df["close"].diff()

            # 分离涨跌
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # 计算平均涨跌
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()

            # 计算 RS 和 RSI
            rs = avg_gain / avg_loss
            result[f"rsi{period}"] = 100 - (100 / (1 + rs))

        return result

    def calculate_boll(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
    ) -> pd.DataFrame:
        """
        计算布林带指标

        Args:
            df: 包含 'close' 列的 DataFrame
            period: 中轨周期
            std_dev: 标准差倍数
        """
        result = df.copy()

        # 中轨 = MA
        result["boll_mid"] = df["close"].rolling(window=period).mean()

        # 标准差
        std = df["close"].rolling(window=period).std()

        # 上轨和下轨
        result["boll_upper"] = result["boll_mid"] + std_dev * std
        result["boll_lower"] = result["boll_mid"] - std_dev * std

        return result

    def calculate_kdj(
        self,
        df: pd.DataFrame,
        n: int = 9,
        m1: int = 3,
        m2: int = 3,
    ) -> pd.DataFrame:
        """
        计算 KDJ 随机指标

        Args:
            df: 包含 'high', 'low', 'close' 列的 DataFrame
            n: RSV 周期
            m1: K 值平滑因子
            m2: D 值平滑因子
        """
        result = df.copy()

        # 计算 RSV
        low_n = df["low"].rolling(window=n).min()
        high_n = df["high"].rolling(window=n).max()

        rsv = (df["close"] - low_n) / (high_n - low_n) * 100

        # 计算 K、D、J 值
        result["kdj_k"] = rsv.ewm(com=m1 - 1, adjust=False).mean()
        result["kdj_d"] = result["kdj_k"].ewm(com=m2 - 1, adjust=False).mean()
        result["kdj_j"] = 3 * result["kdj_k"] - 2 * result["kdj_d"]

        return result

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标

        Args:
            df: 包含 'open', 'high', 'low', 'close', 'volume' 列的 DataFrame
        """
        logger.info("正在计算所有技术指标...")

        # 确保列名正确
        df = df.rename(
            columns={
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
            }
        )

        # 计算各项指标
        df = self.calculate_ma(df)
        df = self.calculate_ema(df)
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df)
        df = self.calculate_boll(df)
        df = self.calculate_kdj(df)

        logger.info("技术指标计算完成")
        return df

    def get_latest_indicators(self, df: pd.DataFrame) -> Optional[dict]:
        """
        获取最新一行的技术指标值

        Args:
            df: 计算完指标的数据
        """
        if df.empty or len(df) < 60:
            logger.warning("数据不足，无法计算指标（需要至少60个交易日数据）")
            return None

        row = df.iloc[-1]

        return {
            "ma5": round(row.get("ma5", 0) or 0, 2),
            "ma10": round(row.get("ma10", 0) or 0, 2),
            "ma20": round(row.get("ma20", 0) or 0, 2),
            "ma60": round(row.get("ma60", 0) or 0, 2),
            "ma120": round(row.get("ma120", 0) or 0, 2),
            "ma250": round(row.get("ma250", 0) or 0, 2),
            "ema12": round(row.get("ema12", 0) or 0, 2),
            "ema26": round(row.get("ema26", 0) or 0, 2),
            "dif": round(row.get("dif", 0) or 0, 4),
            "dea": round(row.get("dea", 0) or 0, 4),
            "macd": round(row.get("macd", 0) or 0, 4),
            "rsi6": round(row.get("rsi6", 0) or 0, 2),
            "rsi12": round(row.get("rsi12", 0) or 0, 2),
            "rsi24": round(row.get("rsi24", 0) or 0, 2),
            "boll_upper": round(row.get("boll_upper", 0) or 0, 2),
            "boll_mid": round(row.get("boll_mid", 0) or 0, 2),
            "boll_lower": round(row.get("boll_lower", 0) or 0, 2),
            "kdj_k": round(row.get("kdj_k", 0) or 0, 2),
            "kdj_d": round(row.get("kdj_d", 0) or 0, 2),
            "kdj_j": round(row.get("kdj_j", 0) or 0, 2),
        }

    def format_indicator_for_db(self, indicator: dict, symbol: str, trade_date: str) -> dict:
        """
        将指标格式化为数据库写入格式
        """
        return {
            "symbol": symbol,
            "trade_date": trade_date,
            **{k: v for k, v in indicator.items()},
            "created_at": datetime.now(),
        }


if __name__ == "__main__":
    from collectors.kline_collector import KlineCollector

    calculator = IndicatorCalculator()
    kline_collector = KlineCollector()

    # 获取日K数据
    print("=== 获取日K数据 ===")
    df = kline_collector.get_daily_kline("600519", start_date="20240101")

    if not df.empty:
        # 计算指标
        df_with_indicator = calculator.calculate_all(df)

        # 获取最新指标
        latest = calculator.get_latest_indicators(df_with_indicator)
        print("\n=== 贵州茅台最新技术指标 ===")
        for k, v in latest.items():
            print(f"  {k}: {v}")
