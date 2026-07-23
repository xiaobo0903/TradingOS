from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class IndexData(BaseModel):
    code: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    amount: float


class StockInfo(BaseModel):
    code: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    amount: float
    turnover: float
    volume_ratio: float
    pe: float
    pb: float
    high_52w: float
    low_52w: float


class KLineData(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None


class IndicatorData(BaseModel):
    ma5: float
    ma10: float
    ma20: float
    ma60: float
    dif: float
    dea: float
    macd: float
    rsi6: float
    rsi12: float
    rsi24: float
    boll_upper: float
    boll_mid: float
    boll_lower: float
    kdj_k: float
    kdj_d: float
    kdj_j: float


class CapitalData(BaseModel):
    main_inflow: float
    main_outflow: float
    super_large_in: float
    super_large_out: float
    large_in: float
    large_out: float
    medium_in: float
    medium_out: float
    small_in: float
    small_out: float


class AIAnalysis(BaseModel):
    trend: str
    confidence: int
    signals: List[str]
    risks: List[str]
    suggestion: str


class HotStock(BaseModel):
    code: str
    name: str
    change: float
    turnover: float
    volume_ratio: float
    ai_score: int


class MarketOverview(BaseModel):
    indices: List[IndexData]
    up_count: int
    down_count: int
    limit_up_count: int
    limit_down_count: int
    hot_stocks: List[HotStock]
    main_inflow: float
    north_money: float
    industry_money: float
    ai_analysis: dict
