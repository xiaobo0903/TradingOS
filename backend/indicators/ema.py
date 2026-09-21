import pandas as pd
from typing import List, Dict
from indicators.base import BaseIndicator


class EMAIndicator(BaseIndicator):
    """指数移动平均 (Exponential Moving Average)"""

    name = "ema"

    def __init__(self, periods: List[int] = None):
        self.periods = periods or [12, 26]

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算EMA"""
        result = df.copy()

        for period in self.periods:
            if len(df) >= period:
                result[f'ema{period}'] = df['close'].ewm(span=period, adjust=False).mean()
            else:
                result[f'ema{period}'] = None

        return result

    def get_params(self) -> Dict:
        return {"periods": self.periods}
