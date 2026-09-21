"""
股票相关 API 接口
"""
from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import get_db
from models.stock import Stock, StockDaily, StockPrice
from models.indicator import StockIndicator


router = APIRouter(prefix="/api/stocks", tags=["股票"])


# Pydantic Schemas
class StockBase(BaseModel):
    code: str
    name: str
    market: Optional[str] = None
    industry: Optional[str] = None


class StockResponse(StockBase):
    id: int
    status: str

    class Config:
        from_attributes = True


class StockDetailResponse(StockBase):
    id: int
    status: str
    current_price: float = 0
    change_pct: float = 0
    volume: int = 0
    amount: float = 0
    turnover_rate: float = 0

    class Config:
        from_attributes = True


class DailyDataResponse(BaseModel):
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    turnover_rate: float
    change_pct: float
    amplitude: float

    class Config:
        from_attributes = True


class MinuteDataResponse(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float

    class Config:
        from_attributes = True


# API Endpoints
@router.get("/", response_model=List[StockResponse])
def list_stocks(
    market: Optional[str] = Query(None, description="市场：SH/SZ"),
    industry: Optional[str] = Query(None, description="行业"),
    status: str = Query("active", description="状态"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取股票列表"""
    query = db.query(Stock)

    if market:
        query = query.filter(Stock.market == market)
    if industry:
        query = query.filter(Stock.industry == industry)

    stocks = query.offset((page - 1) * page_size).limit(page_size).all()
    return stocks


@router.get("/{code}", response_model=StockDetailResponse)
def get_stock(code: str, db: Session = Depends(get_db)):
    """获取股票详情"""
    stock = db.query(Stock).filter(Stock.code == code).first()
    if not stock:
        return {"error": "Stock not found"}

    # 获取最新日线数据
    latest_daily = db.query(StockDaily).filter(
        StockDaily.stock_id == stock.id
    ).order_by(StockDaily.trade_date.desc()).first()

    return {
        "id": stock.id,
        "code": stock.code,
        "name": stock.name,
        "market": stock.market,
        "industry": stock.industry,
        "status": stock.status.value if stock.status else "unknown",
        "current_price": float(latest_daily.close) if latest_daily else 0,
        "change_pct": float(latest_daily.change_pct) if latest_daily else 0,
        "volume": latest_daily.volume if latest_daily else 0,
        "amount": float(latest_daily.amount) if latest_daily else 0,
        "turnover_rate": float(latest_daily.turnover_rate) if latest_daily else 0,
    }


@router.get("/{code}/daily", response_model=List[DailyDataResponse])
def get_daily(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
    adjust: str = Query("qfq", description="复权类型 qfq/hfq/None"),
    db: Session = Depends(get_db)
):
    """获取股票日线数据"""
    stock = db.query(Stock).filter(Stock.code == code).first()
    if not stock:
        return []

    query = db.query(StockDaily).filter(StockDaily.stock_id == stock.id)

    if start_date:
        start = datetime.strptime(start_date, '%Y%m%d').date()
        query = query.filter(StockDaily.trade_date >= start)
    if end_date:
        end = datetime.strptime(end_date, '%Y%m%d').date()
        query = query.filter(StockDaily.trade_date <= end)

    daily_data = query.order_by(StockDaily.trade_date).all()
    return daily_data


@router.get("/{code}/minute", response_model=List[MinuteDataResponse])
def get_minute(
    code: str,
    period: str = Query("1", description="周期 1/5/15/30/60"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """获取股票分钟数据"""
    stock = db.query(Stock).filter(Stock.code == code).first()
    if not stock:
        return []

    minute_data = db.query(StockPrice).filter(
        StockPrice.stock_id == stock.id
    ).order_by(StockPrice.timestamp.desc()).limit(limit).all()

    # 反转顺序，按时间正序返回
    return list(reversed(minute_data))


@router.get("/{code}/realtime")
def get_realtime(code: str):
    """获取实时行情（直接从数据源）"""
    from providers.akshare_provider import AKShareProvider
    provider = AKShareProvider()

    data = provider.get_realtime_price(code)
    return data[0] if data else {"error": "No data"}


@router.get("/{code}/indicators")
def get_indicators(
    code: str,
    trade_date: Optional[str] = Query(None, description="交易日期 YYYYMMDD"),
    db: Session = Depends(get_db)
):
    """获取技术指标"""
    stock = db.query(Stock).filter(Stock.code == code).first()
    if not stock:
        return {"error": "Stock not found"}

    query = db.query(StockIndicator).filter(StockIndicator.stock_id == stock.id)

    if trade_date:
        date_obj = datetime.strptime(trade_date, '%Y%m%d').date()
        query = query.filter(StockIndicator.trade_date == date_obj)
    else:
        # 返回最新
        query = query.order_by(StockIndicator.trade_date.desc())

    indicator = query.first()
    if not indicator:
        return {"error": "No indicator data"}

    return {
        "trade_date": indicator.trade_date,
        "ma": {
            "ma5": float(indicator.ma5) if indicator.ma5 else None,
            "ma10": float(indicator.ma10) if indicator.ma10 else None,
            "ma20": float(indicator.ma20) if indicator.ma20 else None,
            "ma30": float(indicator.ma30) if indicator.ma30 else None,
            "ma60": float(indicator.ma60) if indicator.ma60 else None,
            "ma120": float(indicator.ma120) if indicator.ma120 else None,
            "ma250": float(indicator.ma250) if indicator.ma250 else None,
        },
        "ema": {
            "ema12": float(indicator.ema12) if indicator.ema12 else None,
            "ema26": float(indicator.ema26) if indicator.ema26 else None,
        },
        "macd": {
            "dif": float(indicator.dif) if indicator.dif else None,
            "dea": float(indicator.dea) if indicator.dea else None,
            "macd": float(indicator.macd) if indicator.macd else None,
        },
        "rsi": {
            "rsi6": float(indicator.rsi6) if indicator.rsi6 else None,
            "rsi12": float(indicator.rsi12) if indicator.rsi12 else None,
            "rsi24": float(indicator.rsi24) if indicator.rsi24 else None,
        },
        "boll": {
            "mb": float(indicator.boll_mb) if indicator.boll_mb else None,
            "ub": float(indicator.boll_ub) if indicator.boll_ub else None,
            "lb": float(indicator.boll_lb) if indicator.boll_lb else None,
            "width": float(indicator.boll_width) if indicator.boll_width else None,
        },
        "kdj": {
            "k": float(indicator.kdj_k) if indicator.kdj_k else None,
            "d": float(indicator.kdj_d) if indicator.kdj_d else None,
            "j": float(indicator.kdj_j) if indicator.kdj_j else None,
        },
    }
