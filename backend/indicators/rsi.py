import pandas as pd
import numpy as np
from typing import List, Dict
from indicators.base import BaseIndicator


class RSIIndicator(BaseIndicator):
    """
    RSI (Relative Strength Index)

    默认参数:
    - periods: [6, 12, 24]

    计算公式:
    RSI = 100 - (100 / (1 + RS))
    RS = 平均涨幅 / 平均跌幅
    """

    name = "rsi"

    def __init__(self, periods: List[int] = None):
        self.periods = periods or [6, 12, 24]

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算RSI"""
        result = df.copy()
        close = df['close']

        for period in self.periods:
            if len(df) < period + 1:
                result[f'rsi{period}'] = None
                continue

            delta = close.diff()

            # 分离涨跌
            gain = delta.where(delta > 0, 0.0)
            loss = (-delta).where(delta < 0, 0.0)

            # 计算平均涨跌幅（使用指数移动平均）
            avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
            avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

            # 计算RS和RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            result[f'rsi{period}'] = rsi

        return result

    def get_params(self) -> Dict:
        return {"periods": self.periods}

    def analyze(self, row: pd.Series) -> Dict:
        """分析RSI状态"""
        rsi6 = row.get('rsi6')
        rsi12 = row.get('rsi12')
        rsi24 = row.get('rsi24')

        analysis = {}

        # RSI超买超卖
        def get_level(rsi):
            if pd.isna(rsi):
                return "unknown"
            if rsi >= 80:
                return "overbought"  # 超买
            elif rsi <= 20:
                return "oversold"  # 超卖
            elif rsi >= 70:
                return "overbought_warn"  # 接近超买
            elif rsi <= 30:
                return "oversold_warn"  # 接近超卖
            else:
                return "normal"

        analysis['rsi6_level'] = get_level(rsi6)
        analysis['rsi12_level'] = get_level(rsi12)
        analysis['rsi24_level'] = get_level(rsi24)

        # 多周期RSI是否都偏强/偏弱
        valid_levels = [l for l in [analysis['rsi6_level'], analysis['rsi12_level'], analysis['rsi24_level']] if l != "unknown"]

        if all(l in ["overbought", "overbought_warn"] for l in valid_levels):
            analysis['overall'] = "overbought"
        elif all(l in ["oversold", "oversold_warn"] for l in valid_levels):
            analysis['overall'] = "oversold"
        else:
            analysis['overall'] = "normal"

        return analysis
