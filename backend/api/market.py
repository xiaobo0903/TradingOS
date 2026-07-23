from fastapi import APIRouter
from models.schemas import IndexData, MarketOverview, HotStock
import random

router = APIRouter()


def generate_mock_indices():
    return [
        IndexData(
            code="000001",
            name="上证指数",
            price=2965.23 + random.uniform(-10, 10),
            change=45.32 + random.uniform(-5, 5),
            change_percent=1.55 + random.uniform(-0.3, 0.3),
            volume=325600000,
            amount=398000000000
        ),
        IndexData(
            code="399001",
            name="深证成指",
            price=10748.56 + random.uniform(-20, 20),
            change=156.78 + random.uniform(-10, 10),
            change_percent=1.48 + random.uniform(-0.3, 0.3),
            volume=456700000,
            amount=512000000000
        ),
        IndexData(
            code="399006",
            name="创业板",
            price=2234.12 + random.uniform(-15, 15),
            change=35.67 + random.uniform(-5, 5),
            change_percent=1.62 + random.uniform(-0.3, 0.3),
            volume=189500000,
            amount=267000000000
        ),
        IndexData(
            code="000688",
            name="科创50",
            price=756.89 + random.uniform(-5, 5),
            change=12.34 + random.uniform(-2, 2),
            change_percent=1.66 + random.uniform(-0.3, 0.3),
            volume=98700000,
            amount=123000000000
        )
    ]


def generate_mock_hot_stocks():
    stocks = [
        {"code": "600519", "name": "贵州茅台", "change": 2.35, "turnover": 3.5, "volume_ratio": 1.8, "ai_score": 88},
        {"code": "000858", "name": "五粮液", "change": 3.21, "turnover": 4.2, "volume_ratio": 2.1, "ai_score": 85},
        {"code": "002594", "name": "比亚迪", "change": 4.56, "turnover": 5.8, "volume_ratio": 2.5, "ai_score": 90},
        {"code": "600036", "name": "招商银行", "change": 1.89, "turnover": 2.1, "volume_ratio": 1.3, "ai_score": 78},
        {"code": "601318", "name": "中国平安", "change": 2.12, "turnover": 2.8, "volume_ratio": 1.6, "ai_score": 82},
        {"code": "000001", "name": "平安银行", "change": 1.45, "turnover": 1.9, "volume_ratio": 1.2, "ai_score": 75},
        {"code": "600900", "name": "长江电力", "change": 0.89, "turnover": 1.2, "volume_ratio": 0.9, "ai_score": 72},
        {"code": "300750", "name": "宁德时代", "change": 3.78, "turnover": 4.5, "volume_ratio": 2.2, "ai_score": 87},
        {"code": "601012", "name": "隆基绿能", "change": 2.34, "turnover": 3.2, "volume_ratio": 1.7, "ai_score": 80},
        {"code": "002415", "name": "海康威视", "change": 1.98, "turnover": 2.6, "volume_ratio": 1.4, "ai_score": 76},
    ]
    return [HotStock(**s) for s in stocks]


@router.get("/index", response_model=MarketOverview)
async def get_market_overview():
    return MarketOverview(
        indices=generate_mock_indices(),
        up_count=2856,
        down_count=1892,
        limit_up_count=85,
        limit_down_count=12,
        hot_stocks=generate_mock_hot_stocks(),
        main_inflow=125000000000,
        north_money=28500000000,
        industry_money=45600000000,
        ai_analysis={
            "trend": "上涨趋势",
            "score": 78,
            "risk": "中等",
            "sentiment": "资金活跃"
        }
    )


@router.get("/hot", response_model=list[HotStock])
async def get_hot_stocks():
    return generate_mock_hot_stocks()
