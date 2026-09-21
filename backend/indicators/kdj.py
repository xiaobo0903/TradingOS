import pandas as pd
import numpy as np
from typing import Dict, Tuple
from indicators.base import BaseIndicator


class KDJIndicator(BaseIndicator):
    """
    KDJ 随机指标

    默认参数:
    - n: 9 (RSV计算周期)
    - m1: 3 (K平滑值)
    - m2: 3 (D平滑值)

    计算公式:
    - RSV = (C - LowN) / (HighN - LowN) × 100
    - K = 2/3 × K(-1) + 1/3 × RSV
    - D = 2/3 × D(-1) + 1/3 × K
    - J = 3K - 2D
    """

    name = "kdj"

    def __init__(self, n: int = 9, m1: int = 3, m2: int = 3):
        self.n = n
        self.m1 = m1
        self.m2 = m2

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算KDJ"""
        result = df.copy()

        if len(df) < self.n:
            result['kdj_k'] = None
            result['kdj_d'] = None
            result['kdj_j'] = None
            return result

        low_n = df['low'].rolling(window=self.n).min()
        high_n = df['high'].rolling(window=self.n).max()

        # RSV = (C - LowN) / (HighN - LowN) × 100
        rsv = (df['close'] - low_n) / (high_n - low_n) * 100
        rsv = rsv.fillna(50)  # 如果分母为0，用50代替

        # K, D, J计算
        k = np.zeros(len(rsv))
        d = np.zeros(len(rsv))

        # 初始值
        k[0] = 50
        d[0] = 50

        for i in range(1, len(rsv)):
            # K = 2/3 × K(-1) + 1/3 × RSV
            k[i] = (self.m1 - 1) / self.m1 * k[i - 1] + 1 / self.m1 * rsv.iloc[i]
            # D = 2/3 × D(-1) + 1/3 × K
            d[i] = (self.m2 - 1) / self.m2 * d[i - 1] + 1 / self.m2 * k[i]

        # J = 3K - 2D
        j = 3 * k - 2 * d

        result['kdj_k'] = k
        result['kdj_d'] = d
        result['kdj_j'] = j

        return result

    def get_params(self) -> Dict:
        return {"n": self.n, "m1": self.m1, "m2": self.m2}

    def analyze(self, row: pd.Series) -> Dict:
        """分析KDJ状态"""
        k = row.get('kdj_k')
        d = row.get('kdj_d')
        j = row.get('kdj_j')

        if pd.isna(k) or pd.isna(d):
            return {"signal": "unknown"}

        analysis = {}

        # 金叉/死叉
        # 这里需要前一个周期的值才能准确判断，但在单行分析中简化处理
        if j > k and d > k:
            analysis['cross'] = "neutral"  # 无法单周期判断
        elif k > d:
            analysis['cross'] = "golden"  # 可能金叉
        else:
            analysis['cross'] = "dead"  # 可能死叉

        # KDJ超买超卖
        if j >= 90 or k >= 90:
            analysis['level'] = "overbought"  # 超买
        elif j <= 10 or k <= 10:
            analysis['level'] = "oversold"  # 超卖
        else:
            analysis['level'] = "normal"

        # J值偏离度（用于判断背离）
        if not pd.isna(j):
            if j > 100:
                analysis['j_extreme'] = "overbought"
            elif j < 0:
                analysis['j_extreme'] = "oversold"
            else:
                analysis['j_extreme'] = "normal"

        return analysis
