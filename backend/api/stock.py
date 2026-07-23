from fastapi import APIRouter, Path
from models.schemas import StockInfo, KLineData, IndicatorData, CapitalData, AIAnalysis
import random
from datetime import datetime, timedelta

router = APIRouter()


def generate_mock_stock(code: str):
    names = {
        "600519": "贵州茅台",
        "000858": "五粮液",
        "002594": "比亚迪",
        "600036": "招商银行",
        "601318": "中国平安",
        "300750": "宁德时代",
    }
    name = names.get(code, "未知股票")
    base_price = random.uniform(30, 1800)
    return StockInfo(
        code=code,
        name=name,
        price=base_price,
        change=base_price * random.uniform(0.01, 0.05),
        change_percent=random.uniform(1, 5),
        volume=random.randint(1000000, 10000000),
        amount=random.randint(1000000000, 10000000000),
        turnover=random.uniform(1, 8),
        volume_ratio=random.uniform(0.8, 3),
        pe=random.uniform(15, 50),
        pb=random.uniform(2, 8),
        high_52w=base_price * 1.3,
        low_52w=base_price * 0.7
    )


def generate_mock_kline(code: str, days: int = 60):
    data = []
    base_price = random.uniform(100, 500)
    today = datetime.now()

    for i in range(days, 0, -1):
        date = today - timedelta(days=i)
        open_price = base_price + random.uniform(-20, 20)
        close_price = open_price + random.uniform(-15, 15)
        high_price = max(open_price, close_price) + random.uniform(0, 10)
        low_price = min(open_price, close_price) - random.uniform(0, 10)

        data.append(KLineData(
            date=date.strftime("%m/%d"),
            open=round(open_price, 2),
            high=round(high_price, 2),
            low=round(low_price, 2),
            close=round(close_price, 2),
            volume=random.randint(5000000, 20000000),
            ma5=round(close_price * random.uniform(0.98, 1.02), 2),
            ma10=round(close_price * random.uniform(0.96, 1.04), 2),
            ma20=round(close_price * random.uniform(0.94, 1.06), 2)
        ))
        base_price = close_price

    return data


def generate_mock_indicator():
    return IndicatorData(
        ma5=1652.35,
        ma10=1648.72,
        ma20=1645.18,
        ma60=1638.45,
        dif=12.35,
        dea=8.67,
        macd=7.36,
        rsi6=68.5,
        rsi12=65.3,
        rsi24=62.8,
        boll_upper=1685.25,
        boll_mid=1650.0,
        boll_lower=1614.75,
        kdj_k=72.5,
        kdj_d=68.3,
        kdj_j=81.2
    )


def generate_mock_capital():
    return CapitalData(
        main_inflow=125000000,
        main_outflow=98000000,
        super_large_in=85000000,
        super_large_out=62000000,
        large_in=68000000,
        large_out=55000000,
        medium_in=32000000,
        medium_out=45000000,
        small_in=18000000,
        small_out=35000000
    )


def generate_mock_ai_analysis():
    return AIAnalysis(
        trend="上涨趋势",
        confidence=78,
        signals=["MACD金叉", "BOLL突破上轨", "放量上涨", "主力资金流入"],
        risks=["RSI接近超买区域", "短线涨幅较大"],
        suggestion="等待回踩20日均线后关注"
    )


@router.get("/{code}", response_model=StockInfo)
async def get_stock(code: str = Path(description="股票代码")):
    return generate_mock_stock(code)


@router.get("/{code}/kline", response_model=list[KLineData])
async def get_kline(code: str = Path(description="股票代码"), days: int = 60):
    return generate_mock_kline(code, days)


@router.get("/{code}/indicator", response_model=IndicatorData)
async def get_indicator(code: str = Path(description="股票代码")):
    return generate_mock_indicator()


@router.get("/{code}/capital", response_model=CapitalData)
async def get_capital(code: str = Path(description="股票代码")):
    return generate_mock_capital()


@router.get("/{code}/ai", response_model=AIAnalysis)
async def get_ai_analysis(code: str = Path(description="股票代码")):
    return generate_mock_ai_analysis()
