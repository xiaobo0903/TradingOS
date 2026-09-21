"""
指标计算 API
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db
from models.stock import Stock, StockDaily
from indicators.calculator import get_calculator


router = APIRouter(prefix="/api/indicators", tags=["指标"])


class IndicatorCalculateRequest(BaseModel):
    stock_code: str
    indicators: Optional[List[str]] = None  # 要计算的指标，如 ['ma', 'macd', 'rsi']


@router.post("/calculate")
def calculate_indicators(request: IndicatorCalculateRequest):
    """
    计算技术指标

    直接从原始K线数据计算指标，不依赖数据库中的指标数据
    """
    import pandas as pd

    calculator = get_calculator()

    # 获取日线数据
    from providers.akshare_provider import AKShareProvider
    provider = AKShareProvider()

    # 获取最近365天数据
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now().replace(day=1) - pd.Timedelta(days=365)).strftime('%Y%m%d')

    daily_data = provider.get_daily(request.stock_code, start_date, end_date)

    if not daily_data:
        return {"error": "No data available"}

    # 转换为DataFrame
    df = pd.DataFrame(daily_data)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date')

    # 计算指标
    result_df = calculator.calculate(df, include=request.indicators)

    # 返回最新数据
    latest = result_df.iloc[-1].to_dict()

    return {
        "stock_code": request.stock_code,
        "trade_date": str(latest.get('trade_date', '')),
        "indicators": {k: v for k, v in latest.items() if k not in ['trade_date', 'open', 'high', 'low', 'close', 'volume', 'amount']}
    }


@router.get("/analyze/{code}")
def analyze_stock(
    code: str,
    current_price: Optional[float] = Query(None, description="当前价格（用于BOLL分析）")
):
    """
    综合技术分析

    对股票进行全面的技术分析，返回各指标的状态和信号
    """
    import pandas as pd

    calculator = get_calculator()

    # 获取日线数据
    from providers.akshare_provider import AKShareProvider
    provider = AKShareProvider()

    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - pd.Timedelta(days=365)).strftime('%Y%m%d')

    daily_data = provider.get_daily(code, start_date, end_date)

    if not daily_data:
        return {"error": "No data available"}

    # 转换为DataFrame
    df = pd.DataFrame(daily_data)
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    df = df.sort_values('trade_date')

    # 如果没有提供当前价格，使用最新收盘价
    if current_price is None:
        current_price = float(df.iloc[-1]['close'])

    # 进行技术分析
    analysis = calculator.analyze_technicals(df, current_price)

    return {
        "stock_code": code,
        "current_price": current_price,
        "analysis": analysis,
    }
