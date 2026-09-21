"""
股票筛选 API 接口

支持：
1. 股票发现类型过滤（强势股、放量股、涨停股等）
2. 行情数据筛选（涨跌幅、换手率、成交量、价格等）
3. 技术指标筛选（MA、MACD、RSI、KDJ等）
4. 组合条件筛选
"""
from typing import List, Optional
from datetime import datetime, date
import json

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from models.database import get_db
from models.stock import Stock, StockDaily
from models.indicator import StockIndicator
from models.discovery import StockDiscovery
from utils.logging import app_logger


router = APIRouter(prefix="/api/screener", tags=["股票筛选"])


class ScreenerFilter(BaseModel):
    """筛选条件"""
    # 发现类型
    discovery_type: Optional[str] = None  # strong, volume_surge, breakout, etc.
    period: Optional[str] = "short"  # short, medium, long

    # 行情条件
    min_change_pct: Optional[float] = None  # 最小涨幅
    max_change_pct: Optional[float] = None  # 最大涨幅
    min_price: Optional[float] = None  # 最低价
    max_price: Optional[float] = None  # 最高价
    min_volume: Optional[int] = None  # 最小成交量
    max_volume: Optional[int] = None  # 最大成交量
    min_turnover_rate: Optional[float] = None  # 最小换手率
    max_turnover_rate: Optional[float] = None  # 最大换手率
    min_amount: Optional[float] = None  # 最小成交额
    max_amount: Optional[float] = None  # 最大成交额

    # 技术指标条件
    min_ma5: Optional[float] = None
    max_ma5: Optional[float] = None
    min_rsi6: Optional[float] = None
    max_rsi6: Optional[float] = None
    min_macd: Optional[float] = None
    max_macd: Optional[float] = None

    # 市场条件
    market: Optional[str] = None  # SH, SZ
    industry: Optional[str] = None

    # 排序
    sort_by: str = "score"  # score, change_pct, volume, turnover_rate, price
    sort_order: str = "desc"  # asc, desc

    # 分页
    limit: int = 50
    offset: int = 0


class StockItem(BaseModel):
    """股票结果项"""
    id: int
    stock_id: int
    code: str
    name: str
    industry: Optional[str] = None
    market: Optional[str] = None

    # 行情数据
    current_price: float = 0
    change_pct: float = 0
    volume: int = 0
    amount: float = 0
    turnover_rate: float = 0
    open: float = 0
    high: float = 0
    low: float = 0

    # 发现相关
    discovery_type: Optional[str] = None
    score: Optional[float] = None
    reason: Optional[str] = None
    behaviors: Optional[dict] = None
    trend: Optional[dict] = None

    class Config:
        from_attributes = True


class ScreenerResponse(BaseModel):
    total: int
    items: List[StockItem]


@router.get("/filters/options")
def get_filter_options():
    """获取筛选选项"""
    return {
        "discovery_types": [
            {"value": "strong", "label": "强势股", "desc": "涨幅 > 3%"},
            {"value": "volume_surge", "label": "放量股", "desc": "成交量异常放大"},
            {"value": "volume_shrink", "label": "缩量上涨", "desc": "缩量上涨"},
            {"value": "breakout", "label": "突破股", "desc": "突破近期高点"},
            {"value": "pullback", "label": "回调股", "desc": "从高点回调"},
            {"value": "limit_up", "label": "涨停股", "desc": "涨幅 >= 9.9%"},
            {"value": "new_high", "label": "新高股", "desc": "创出新高的股票"},
            {"value": "new_low", "label": "新低股", "desc": "创出新低的股票"},
            {"value": "sentiment", "label": "人气股", "desc": "涨幅+放量的热门股"},
            {"value": "large_order", "label": "异动股", "desc": "换手率异常的股票"},
            {"value": "capital_flow", "label": "资金异动", "desc": "主力资金净流入"},
            {"value": "oversold", "label": "超跌候选", "desc": "超跌反弹候选"},
            {"value": "tech_resonance", "label": "技术共振", "desc": "多指标共振"},
        ],
        "periods": [
            {"value": "short", "label": "短线"},
            {"value": "medium", "label": "中线"},
            {"value": "long", "label": "长线"},
        ],
        "sort_options": [
            {"value": "score", "label": "综合评分"},
            {"value": "change_pct", "label": "涨跌幅"},
            {"value": "volume", "label": "成交量"},
            {"value": "turnover_rate", "label": "换手率"},
            {"value": "price", "label": "价格"},
        ],
    }


@router.post("/query", response_model=ScreenerResponse)
def query_stocks(
    filter: ScreenerFilter,
    db: Session = Depends(get_db)
):
    """
    股票筛选查询

    支持发现类型 + 行情条件 + 技术指标组合筛选
    """
    app_logger.info(f"股票筛选查询: {filter.dict(exclude_none=True)}", category="API")

    # 获取最近交易日的发现记录
    today = date.today()
    discovery_map = {}

    if filter.discovery_type:
        discoveries = db.query(StockDiscovery).filter(
            StockDiscovery.trade_date >= today
        ).all()

        for d in discoveries:
            key = f"{d.stock_id}_{d.discovery_type}"
            discovery_map[key] = {
                'discovery_type': d.discovery_type,
                'score': float(d.score) if d.score else 0,
                'reason': d.reason,
                'behaviors': json.loads(d.data_snapshot).get('behaviors', {}) if d.data_snapshot else {},
                'trend': json.loads(d.data_snapshot).get('trend', {}) if d.data_snapshot else {},
            }

    # 获取最新日线的子查询
    from sqlalchemy.sql import func
    latest_daily_subq = db.query(
        StockDaily.stock_id,
        func.max(StockDaily.trade_date).label('max_date')
    ).group_by(StockDaily.stock_id).subquery()

    # 最新日线数据
    latest_daily = db.query(
        StockDaily.stock_id,
        StockDaily.close,
        StockDaily.change_pct,
        StockDaily.volume,
        StockDaily.amount,
        StockDaily.turnover_rate,
        StockDaily.open,
        StockDaily.high,
        StockDaily.low,
    ).join(
        latest_daily_subq,
        and_(
            StockDaily.stock_id == latest_daily_subq.c.stock_id,
            StockDaily.trade_date == latest_daily_subq.c.max_date
        )
    ).subquery()

    # 获取最新指标的子查询
    latest_indicator_subq = db.query(
        StockIndicator.stock_id,
        func.max(StockIndicator.trade_date).label('max_date')
    ).group_by(StockIndicator.stock_id).subquery()

    # 最新指标数据
    latest_indicator = db.query(
        StockIndicator.stock_id,
        StockIndicator.ma5,
        StockIndicator.rsi6,
        StockIndicator.dif,
        StockIndicator.macd,
    ).join(
        latest_indicator_subq,
        and_(
            StockIndicator.stock_id == latest_indicator_subq.c.stock_id,
            StockIndicator.trade_date == latest_indicator_subq.c.max_date
        )
    ).subquery()

    # 构建查询 - 使用 select 并明确列标签
    from sqlalchemy import select

    query = select(
        Stock.id.label('id'),
        Stock.code.label('code'),
        Stock.name.label('name'),
        Stock.industry.label('industry'),
        Stock.market.label('market'),
        latest_daily.c.close.label('close'),
        latest_daily.c.change_pct.label('change_pct'),
        latest_daily.c.volume.label('volume'),
        latest_daily.c.amount.label('amount'),
        latest_daily.c.turnover_rate.label('turnover_rate'),
        latest_daily.c.open.label('open'),
        latest_daily.c.high.label('high'),
        latest_daily.c.low.label('low'),
        latest_indicator.c.ma5.label('ma5'),
        latest_indicator.c.rsi6.label('rsi6'),
        latest_indicator.c.dif.label('dif'),
        latest_indicator.c.macd.label('macd'),
    ).select_from(Stock).join(
        latest_daily,
        latest_daily.c.stock_id == Stock.id
    ).outerjoin(
        latest_indicator,
        latest_indicator.c.stock_id == Stock.id
    ).where(Stock.status == 'active')

    # 应用行情条件
    if filter.min_change_pct is not None:
        query = query.where(latest_daily.c.change_pct >= filter.min_change_pct)
    if filter.max_change_pct is not None:
        query = query.where(latest_daily.c.change_pct <= filter.max_change_pct)
    if filter.min_price is not None:
        query = query.where(latest_daily.c.close >= filter.min_price)
    if filter.max_price is not None:
        query = query.where(latest_daily.c.close <= filter.max_price)
    if filter.min_volume is not None:
        query = query.where(latest_daily.c.volume >= filter.min_volume)
    if filter.max_volume is not None:
        query = query.where(latest_daily.c.volume <= filter.max_volume)
    if filter.min_turnover_rate is not None:
        query = query.where(latest_daily.c.turnover_rate >= filter.min_turnover_rate)
    if filter.max_turnover_rate is not None:
        query = query.where(latest_daily.c.turnover_rate <= filter.max_turnover_rate)
    if filter.min_amount is not None:
        query = query.where(latest_daily.c.amount >= filter.min_amount)
    if filter.max_amount is not None:
        query = query.where(latest_daily.c.amount <= filter.max_amount)

    # 应用技术指标条件
    if filter.min_ma5 is not None:
        query = query.where(latest_indicator.c.ma5 >= filter.min_ma5)
    if filter.max_ma5 is not None:
        query = query.where(latest_indicator.c.ma5 <= filter.max_ma5)
    if filter.min_rsi6 is not None:
        query = query.where(latest_indicator.c.rsi6 >= filter.min_rsi6)
    if filter.max_rsi6 is not None:
        query = query.where(latest_indicator.c.rsi6 <= filter.max_rsi6)
    if filter.min_macd is not None:
        query = query.where(latest_indicator.c.macd >= filter.min_macd)
    if filter.max_macd is not None:
        query = query.where(latest_indicator.c.macd <= filter.max_macd)

    # 应用市场条件
    if filter.market:
        query = query.where(Stock.market == filter.market)
    if filter.industry:
        query = query.where(Stock.industry == filter.industry)

    # 获取总数
    total = db.execute(select(func.count()).select_from(query.subquery())).scalar()

    # 排序
    sort_column = None
    if filter.sort_by == 'change_pct':
        sort_column = latest_daily.c.change_pct
    elif filter.sort_by == 'volume':
        sort_column = latest_daily.c.volume
    elif filter.sort_by == 'turnover_rate':
        sort_column = latest_daily.c.turnover_rate
    elif filter.sort_by == 'price':
        sort_column = latest_daily.c.close

    if sort_column:
        if filter.sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

    # 分页
    results = db.execute(query.offset(filter.offset).limit(filter.limit)).fetchall()

    # 构建返回结果
    items = []
    for r in results:
        stock_id = r.id

        # 查找发现记录
        discovery_key = f"{stock_id}_{filter.discovery_type}" if filter.discovery_type else None
        discovery_info = None
        if discovery_key and discovery_key in discovery_map:
            discovery_info = discovery_map[discovery_key]
        elif not filter.discovery_type:
            for key, val in discovery_map.items():
                if key.startswith(f"{stock_id}_"):
                    discovery_info = val
                    break

        item = StockItem(
            id=stock_id,
            stock_id=stock_id,
            code=r.code,
            name=r.name,
            industry=r.industry,
            market=r.market,
            current_price=float(r.close) if r.close else 0,
            change_pct=float(r.change_pct) if r.change_pct else 0,
            volume=r.volume or 0,
            amount=float(r.amount) if r.amount else 0,
            turnover_rate=float(r.turnover_rate) if r.turnover_rate else 0,
            open=float(r.open) if r.open else 0,
            high=float(r.high) if r.high else 0,
            low=float(r.low) if r.low else 0,
        )

        if discovery_info:
            item.discovery_type = discovery_info['discovery_type']
            item.score = discovery_info['score']
            item.reason = discovery_info['reason']
            item.behaviors = discovery_info['behaviors']
            item.trend = discovery_info['trend']

        items.append(item)

    # 如果指定了发现类型，需要过滤
    if filter.discovery_type:
        items = [i for i in items if i.discovery_type == filter.discovery_type]
        total = len(items)

    return ScreenerResponse(total=total, items=items)


@router.get("/industries")
def get_industries(db: Session = Depends(get_db)):
    """获取所有行业列表"""
    industries = db.query(Stock.industry).distinct().filter(
        Stock.industry.isnot(None),
        Stock.status == 'active'
    ).all()
    return [i[0] for i in industries if i[0]]
