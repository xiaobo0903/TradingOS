import pandas as pd
import numpy as np
from typing import Dict
from indicators.base import BaseIndicator


class BOLLIndicator(BaseIndicator):
    """
    BOLL (Bollinger Bands) 布林带

    默认参数:
    - period: 20
    - std_dev: 2

    计算公式:
    - MB = MA20 (中轨)
    - UB = MB + K × σ (上轨)
    - LB = MB - K × σ (下轨)
    - σ = 标准差
    """

    name = "boll"

    def __init__(self, period: int = 20, std_dev: float = 2):
        self.period = period
        self.std_dev = std_dev

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算BOLL"""
        result = df.copy()
        close = df['close']

        if len(df) < self.period:
            result['boll_mb'] = None
            result['boll_ub'] = None
            result['boll_lb'] = None
            result['boll_width'] = None
            return result

        # 中轨 = MA20
        mb = close.rolling(window=self.period).mean()

        # 标准差
        std = close.rolling(window=self.period).std()

        # 上轨和下轨
        ub = mb + self.std_dev * std
        lb = mb - self.std_dev * std

        # 带宽 = (UB - LB) / MB * 100
        width = (ub - lb) / mb * 100

        result['boll_mb'] = mb
        result['boll_ub'] = ub
        result['boll_lb'] = lb
        result['boll_width'] = width

        return result

    def get_params(self) -> Dict:
        return {"period": self.period, "std_dev": self.std_dev}

    def analyze(self, row: pd.Series, current_price: float) -> Dict:
        """分析BOLL状态"""
        mb = row.get('boll_mb')
        ub = row.get('boll_ub')
        lb = row.get('boll_lb')

        analysis = {}

        if pd.isna(mb) or pd.isna(ub) or pd.isna(lb):
            return {"signal": "unknown"}

        # 价格位置
        if current_price > ub:
            analysis['position'] = "above_upper"  # 突破上轨
            analysis['signal'] = "突破上轨"
        elif current_price < lb:
            analysis['position'] = "below_lower"  # 跌破下轨
            analysis['signal'] = "跌破下轨"
        elif current_price > mb:
            analysis['position'] = "above_middle"  # 在中轨之上
            analysis['signal'] = "偏强"
        else:
            analysis['position'] = "below_middle"  # 在中轨之下
            analysis['signal'] = "偏弱"

        # 带宽收窄/扩张（用于判断波动率）
        analysis['is_shrink'] = True if row.get('boll_width') and row.get('boll_width') < 10 else False

        return analysis
