import pandas as pd
from typing import List, Dict
from indicators.base import BaseIndicator


class MAIndicator(BaseIndicator):
    """移动平均线 (Moving Average)"""

    name = "ma"

    def __init__(self, periods: List[int] = None):
        self.periods = periods or [5, 10, 20, 30, 60, 120, 250]

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算MA"""
        result = df.copy()

        for period in self.periods:
            if len(df) >= period:
                result[f'ma{period}'] = df['close'].rolling(window=period).mean()
            else:
                result[f'ma{period}'] = None

        return result

    def get_params(self) -> Dict:
        return {"periods": self.periods}
