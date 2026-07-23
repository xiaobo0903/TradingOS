"""
数据采集模块

提供股票数据、K线数据、资金流数据、技术指标的采集功能
使用 AKShare 作为数据源
"""

from collectors.stock_collector import StockCollector
from collectors.kline_collector import KlineCollector
from collectors.capital_collector import CapitalCollector
from collectors.indicator_calculator import IndicatorCalculator

__all__ = [
    "StockCollector",
    "KlineCollector",
    "CapitalCollector",
    "IndicatorCalculator",
]
