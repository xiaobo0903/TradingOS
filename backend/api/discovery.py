"""
股票发现 API 接口

核心逻辑：基于T-1日数据分析，找出可能上涨/买入机会的股票
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel

from services.discovery_service import get_discovery_service, DiscoveryResult
from utils.logging import app_logger


router = APIRouter(prefix="/api/discovery", tags=["股票发现"])


class DiscoveryItem(BaseModel):
    """发现结果项"""
    id: int
    stock_id: int
    code: str
    name: str
    industry: Optional[str] = None
    sectors: List[str] = []  # 所属板块列表
    score: float
    reason: str
    trade_date: str
    # 满足的条件列表
    conditions: List[str] = []
    # T-1日行情
    close: float = 0
    change_pct: float = 0
    volume: int = 0
    turnover_rate: float = 0
    high: float = 0
    low: float = 0
    # 技术指标
    indicators: dict = {}


class DiscoveryRunResponse(BaseModel):
    """运行发现任务响应"""
    success: bool
    total_scanned: int
    discoveries_found: int
    saved: int
    message: str


class DiscoveryListResponse(BaseModel):
    """发现列表响应"""
    total: int
    items: List[DiscoveryItem]


# 缺省阈值配置（可在运行时覆盖）
DEFAULT_THRESHOLDS = {
    'vol_ratio_min': 1.5,        # 最小量比
    'turnover_rate_min': 3.0,     # 最小换手率(%)
    'change_pct_min': 2.0,       # 最小涨幅(%)
    'change_pct_max': 8.0,       # 最大涨幅(%)
    'rsi_max': 70,              # RSI最大值
    'rsi_min': 30,              # RSI最小值
}


@router.post("/run", response_model=DiscoveryRunResponse)
def run_discovery(
    period: str = Query("short", description="分析周期 (暂未使用)"),
    limit: int = Query(50, description="返回结果数量", ge=1, le=200),
    min_score: float = Query(60.0, description="最低评分", ge=0, le=100),
    save: bool = Query(True, description="是否保存到数据库"),
):
    """
    运行股票发现任务

    基于T-1日数据分析，找出可能上涨的股票
    """
    app_logger.info(f"API调用: 执行股票发现 最低分={min_score}, 限制={limit}", category="API")

    service = get_discovery_service()

    # 执行发现
    discoveries = service.discover(
        period=period,
        limit=limit,
        min_score=min_score,
    )

    saved = 0
    if save and discoveries:
        saved = service.save_discoveries(discoveries, discovery_type='buy_signal')
        app_logger.info(f"API调用: 股票发现完成，发现 {len(discoveries)} 只，保存 {saved} 条", category="API")

    return DiscoveryRunResponse(
        success=True,
        total_scanned=0,
        discoveries_found=len(discoveries),
        saved=saved,
        message=f"发现 {len(discoveries)} 只候选股票，已保存 {saved} 条记录"
    )


@router.get("/list", response_model=DiscoveryListResponse)
def get_discovery_list(
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    offset: int = Query(0, description="偏移量", ge=0),
):
    """
    获取已保存的发现记录

    返回最近3天内的发现结果，按评分排序
    """
    service = get_discovery_service()

    items = service.get_discoveries(
        discovery_type='buy_signal',
        limit=limit,
        offset=offset,
    )

    result_items = []
    for item in items:
        yesterday = item.get('yesterday', {})
        result_items.append(DiscoveryItem(
            id=item['id'],
            stock_id=item['stock_id'],
            code=item['code'],
            name=item['name'],
            industry=item.get('industry'),
            sectors=item.get('sectors', []),
            score=item['score'],
            reason=item['reason'],
            conditions=item.get('conditions', []),
            trade_date=item['trade_date'],
            close=yesterday.get('close', 0),
            change_pct=yesterday.get('change_pct', 0),
            volume=int(yesterday.get('volume', 0)),
            turnover_rate=yesterday.get('turnover_rate', 0),
            high=yesterday.get('high', 0),
            low=yesterday.get('low', 0),
            indicators=item.get('indicators', {}),
        ))

    return DiscoveryListResponse(
        total=len(result_items),
        items=result_items,
    )


@router.get("/hot", response_model=DiscoveryListResponse)
def get_hot_discoveries(
    limit: int = Query(10, description="返回数量", ge=1, le=50),
):
    """
    获取热门发现（评分最高的发现记录）

    用于首页展示
    """
    service = get_discovery_service()

    items = service.get_discoveries(
        discovery_type='buy_signal',
        limit=limit,
    )

    result_items = []
    for item in items:
        yesterday = item.get('yesterday', {})
        result_items.append(DiscoveryItem(
            id=item['id'],
            stock_id=item['stock_id'],
            code=item['code'],
            name=item['name'],
            industry=item.get('industry'),
            sectors=item.get('sectors', []),
            score=item['score'],
            reason=item['reason'],
            conditions=item.get('conditions', []),
            trade_date=item['trade_date'],
            close=yesterday.get('close', 0),
            change_pct=yesterday.get('change_pct', 0),
            volume=int(yesterday.get('volume', 0)),
            turnover_rate=yesterday.get('turnover_rate', 0),
            high=yesterday.get('high', 0),
            low=yesterday.get('low', 0),
            indicators=item.get('indicators', {}),
        ))

    return DiscoveryListResponse(
        total=len(result_items),
        items=result_items,
    )


@router.get("/thresholds")
def get_thresholds():
    """获取当前使用的阈值配置"""
    return DEFAULT_THRESHOLDS