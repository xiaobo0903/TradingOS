"""
技术指标计算编排器
"""
from typing import List, Dict, Optional
import pandas as pd

from indicators.ma import MAIndicator
from indicators.ema import EMAIndicator
from indicators.macd import MACDIndicator
from indicators.rsi import RSIIndicator
from indicators.boll import BOLLIndicator
from indicators.kdj import KDJIndicator


class IndicatorCalculator:
    """
    技术指标计算编排器

    统一调度所有指标的计算，提供便捷的批量计算接口
    """

    def __init__(self):
        self.indicators = {
            'ma': MAIndicator(),
            'ema': EMAIndicator(),
            'macd': MACDIndicator(),
            'rsi': RSIIndicator(),
            'boll': BOLLIndicator(),
            'kdj': KDJIndicator(),
        }

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有指标

        Args:
            df: 包含 OHLCV 数据的 DataFrame
                 必须包含列: open, high, low, close, volume

        Returns:
            添加了所有指标计算结果的 DataFrame
        """
        result = df.copy()

        for name, indicator in self.indicators.items():
            result = indicator.calculate(result)

        return result

    def calculate(self, df: pd.DataFrame, include: List[str] = None) -> pd.DataFrame:
        """
        计算指定指标

        Args:
            df: OHLCV 数据
            include: 要计算的指标名称列表，如 ['ma', 'macd', 'rsi']
                    如果为 None，则计算所有指标

        Returns:
            添加了指定指标计算结果的 DataFrame
        """
        result = df.copy()
        indicators_to_calc = include or list(self.indicators.keys())

        for name in indicators_to_calc:
            if name in self.indicators:
                result = self.indicators[name].calculate(result)

        return result

    def get_indicator_names(self) -> List[str]:
        """获取所有可用指标名称"""
        return list(self.indicators.keys())

    def get_latest_indicators(self, df: pd.DataFrame, include: List[str] = None) -> Dict:
        """
        计算并返回最新一根K线的指标值

        Args:
            df: OHLCV 数据
            include: 要计算的指标名称列表

        Returns:
            最新指标值的字典
        """
        result = self.calculate(df, include)

        if result.empty:
            return {}

        latest = result.iloc[-1]

        # 转换为普通字典，过滤掉NaN值
        return {k: v for k, v in latest.to_dict().items() if pd.notna(v)}

    def analyze_technicals(self, df: pd.DataFrame, current_price: float = None) -> Dict:
        """
        对最新数据进行全面技术分析

        Args:
            df: OHLCV 数据
            current_price: 当前价格（用于BOLL分析）

        Returns:
            技术分析结果字典
        """
        result = self.calculate_all(df)

        if result.empty:
            return {}

        latest = result.iloc[-1]
        analysis = {}

        # MACD 分析
        macd = MACDIndicator()
        analysis['macd'] = macd.analyze(latest)

        # RSI 分析
        rsi = RSIIndicator()
        analysis['rsi'] = rsi.analyze(latest)

        # BOLL 分析
        boll = BOLLIndicator()
        analysis['boll'] = boll.analyze(latest, current_price or float(latest['close']))

        # KDJ 分析
        kdj = KDJIndicator()
        analysis['kdj'] = kdj.analyze(latest)

        # 均线系统
        ma_periods = [5, 10, 20, 30, 60]
        ma_signals = []
        for p in ma_periods:
            ma_col = f'ma{p}'
            if ma_col in latest and pd.notna(latest[ma_col]):
                if current_price and current_price > float(latest[ma_col]):
                    ma_signals.append(f"价格>MA{p}")
                else:
                    ma_signals.append(f"价格<MA{p}")

        analysis['ma'] = {
            'signals': ma_signals,
            'latest': {f'ma{p}': float(latest[f'ma{p}']) for p in ma_periods if f'ma{p}' in latest and pd.notna(latest[f'ma{p}'])}
        }

        # 多周期均线排列
        ma5 = latest.get('ma5')
        ma10 = latest.get('ma10')
        ma20 = latest.get('ma20')
        ma60 = latest.get('ma60')

        if all(pd.notna(x) for x in [ma5, ma10, ma20]):
            if ma5 > ma10 > ma20:
                analysis['ma_arrangement'] = "多头排列"
            elif ma5 < ma10 < ma20:
                analysis['ma_arrangement'] = "空头排列"
            else:
                analysis['ma_arrangement'] = "混乱"

        return analysis


# 全局单例
_calculator_instance: Optional[IndicatorCalculator] = None


def get_calculator() -> IndicatorCalculator:
    """获取指标计算器单例"""
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = IndicatorCalculator()
    return _calculator_instance
