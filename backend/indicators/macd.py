import pandas as pd
import numpy as np
from typing import Dict
from indicators.base import BaseIndicator


class MACDIndicator(BaseIndicator):
    """
    MACD (Moving Average Convergence Divergence)

    默认参数:
    - fast: 12
    - slow: 26
    - signal: 9

    计算公式:
    - DIF = EMA12 - EMA26
    - DEA = DIF的EMA9
    - MACD柱 = 2 × (DIF - DEA)
    """

    name = "macd"

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算MACD"""
        result = df.copy()
        close = df['close']

        # 计算快线和慢线EMA
        ema_fast = close.ewm(span=self.fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow, adjust=False).mean()

        # DIF = EMA12 - EMA26
        result['dif'] = ema_fast - ema_slow

        # DEA = DIF的EMA9
        result['dea'] = result['dif'].ewm(span=self.signal, adjust=False).mean()

        # MACD柱 = 2 × (DIF - DEA)
        result['macd'] = 2 * (result['dif'] - result['dea'])

        # 保留EMA12和EMA26
        result['ema12'] = ema_fast
        result['ema26'] = ema_slow

        return result

    def get_params(self) -> Dict:
        return {"fast": self.fast, "slow": self.slow, "signal": self.signal}

    def analyze(self, row: pd.Series) -> Dict:
        """分析MACD状态"""
        dif = row.get('dif')
        dea = row.get('dea')
        macd = row.get('macd')

        if pd.isna(dif) or pd.isna(dea):
            return {"signal": "unknown"}

        signal = []
        analysis = {}

        # 金叉/死叉
        if dif > dea:
            signal.append("金叉")
            analysis['cross'] = "golden"  # 金叉
        elif dif < dea:
            signal.append("死叉")
            analysis['cross'] = "dead"  # 死叉
        else:
            analysis['cross'] = "neutral"

        # DIF位置
        if dif > 0:
            signal.append("DIF>0")
            analysis['dif_position'] = "above_zero"
        else:
            signal.append("DIF<0")
            analysis['dif_position'] = "below_zero"

        # MACD柱
        if not pd.isna(macd):
            if macd > 0:
                signal.append("红柱")
                analysis['bar'] = "red"
            else:
                signal.append("绿柱")
                analysis['bar'] = "green"

        analysis['signal'] = "/".join(signal) if signal else "无信号"
        return analysis
