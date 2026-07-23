from fastapi import APIRouter, Path, HTTPException
from models.schemas import StockInfo, KLineData, IndicatorData, CapitalData, AIAnalysis
from collectors.stock_collector import StockCollector
from collectors.kline_collector import KlineCollector
from collectors.capital_collector import CapitalCollector
from collectors.indicator_calculator import IndicatorCalculator
from services.db_service import db_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 初始化采集器
stock_collector = StockCollector()
kline_collector = KlineCollector()
capital_collector = CapitalCollector()
indicator_calculator = IndicatorCalculator()


def get_stock_info_from_db(code: str) -> StockInfo:
    """从数据库获取股票信息"""
    stock = db_service.get_stock(code)
    if stock:
        return StockInfo(
            code=stock["symbol"],
            name=stock["name"],
            price=stock.get("price", 0) or 0,
            change=stock.get("change", 0) or 0,
            change_percent=stock.get("change_percent", 0) or 0,
            volume=stock.get("volume", 0) or 0,
            amount=stock.get("amount", 0) or 0,
            turnover=stock.get("turnover", 0) or 0,
            volume_ratio=stock.get("volume_ratio", 0) or 0,
            pe=stock.get("pe", 0) or 0,
            pb=stock.get("pb", 0) or 0,
            high_52w=stock.get("high_52w", 0) or 0,
            low_52w=stock.get("low_52w", 0) or 0,
        )
    return None


def get_stock_info_from_api(code: str) -> StockInfo:
    """从AKShare获取实时股票信息"""
    info = stock_collector.get_stock_info(code)
    if info:
        return StockInfo(**info)
    return None


def get_kline_from_db(code: str, days: int = 60) -> list[KLineData]:
    """从数据库获取K线数据"""
    klines = db_service.get_daily_kline(code, days)
    return [
        KLineData(
            date=k["trade_date"].strftime("%m/%d") if hasattr(k["trade_date"], "strftime") else str(k["trade_date"]),
            open=float(k["open"]),
            high=float(k["high"]),
            low=float(k["low"]),
            close=float(k["close"]),
            volume=int(k["volume"]),
            ma5=None,
            ma10=None,
            ma20=None,
        )
        for k in reversed(klines)
    ]


def get_kline_from_api(code: str, days: int = 60) -> list[KLineData]:
    """从AKShare获取K线数据"""
    df = kline_collector.get_daily_kline(code, start_date="20200101")
    if df.empty:
        return []

    # 计算技术指标
    df = indicator_calculator.calculate_all(df)

    records = []
    for _, row in df.iterrows():
        records.append(KLineData(
            date=row.get("日期", ""),
            open=float(row.get("开盘", 0) or 0),
            high=float(row.get("最高", 0) or 0),
            low=float(row.get("最低", 0) or 0),
            close=float(row.get("收盘", 0) or 0),
            volume=int(row.get("成交量", 0) or 0),
            ma5=float(row.get("ma5", 0) or 0) or None,
            ma10=float(row.get("ma10", 0) or 0) or None,
            ma20=float(row.get("ma20", 0) or 0) or None,
        ))

    # 返回最近 days 条
    return records[-days:] if len(records) > days else records


def get_indicator_from_db(code: str) -> IndicatorData:
    """从数据库获取技术指标"""
    indicator = db_service.get_latest_indicator(code)
    if indicator:
        return IndicatorData(
            ma5=float(indicator.get("ma5", 0) or 0),
            ma10=float(indicator.get("ma10", 0) or 0),
            ma20=float(indicator.get("ma20", 0) or 0),
            ma60=float(indicator.get("ma60", 0) or 0),
            dif=float(indicator.get("dif", 0) or 0),
            dea=float(indicator.get("dea", 0) or 0),
            macd=float(indicator.get("macd", 0) or 0),
            rsi6=float(indicator.get("rsi6", 0) or 0),
            rsi12=float(indicator.get("rsi12", 0) or 0),
            rsi24=float(indicator.get("rsi24", 0) or 0),
            boll_upper=float(indicator.get("boll_upper", 0) or 0),
            boll_mid=float(indicator.get("boll_mid", 0) or 0),
            boll_lower=float(indicator.get("boll_lower", 0) or 0),
            kdj_k=float(indicator.get("kdj_k", 0) or 0),
            kdj_d=float(indicator.get("kdj_d", 0) or 0),
            kdj_j=float(indicator.get("kdj_j", 0) or 0),
        )
    return None


def get_indicator_from_api(code: str) -> IndicatorData:
    """从AKShare获取并计算技术指标"""
    df = kline_collector.get_daily_kline(code, start_date="20200101")
    if df.empty:
        raise HTTPException(status_code=404, detail="无法获取K线数据")

    df = indicator_calculator.calculate_all(df)
    latest = indicator_calculator.get_latest_indicators(df)
    if latest is None:
        raise HTTPException(status_code=404, detail="数据不足无法计算指标")

    return IndicatorData(**latest)


def get_capital_from_db(code: str) -> CapitalData:
    """从数据库获取资金数据"""
    flows = db_service.get_money_flow(code, days=1)
    if flows:
        f = flows[0]
        return CapitalData(
            main_inflow=float(f.get("main_inflow", 0) or 0),
            main_outflow=float(f.get("main_outflow", 0) or 0),
            super_large_in=float(f.get("super_large_in", 0) or 0),
            super_large_out=float(f.get("super_large_out", 0) or 0),
            large_in=float(f.get("large_in", 0) or 0),
            large_out=float(f.get("large_out", 0) or 0),
            medium_in=float(f.get("medium_in", 0) or 0),
            medium_out=float(f.get("medium_out", 0) or 0),
            small_in=float(f.get("small_in", 0) or 0),
            small_out=float(f.get("small_out", 0) or 0),
        )
    return None


def get_capital_from_api(code: str) -> CapitalData:
    """从AKShare获取资金数据"""
    df = capital_collector.get_stock_money_flow(code)
    if df.empty:
        # 返回默认数据
        return CapitalData(
            main_inflow=0,
            main_outflow=0,
            super_large_in=0,
            super_large_out=0,
            large_in=0,
            large_out=0,
            medium_in=0,
            medium_out=0,
            small_in=0,
            small_out=0,
        )

    # 取最新一条数据
    row = df.iloc[-1]
    return CapitalData(
        main_inflow=float(row.get("主力净流入", 0) or 0),
        main_outflow=float(row.get("主力净流出", 0) or 0),
        super_large_in=float(row.get("超大单净流入", 0) or 0),
        super_large_out=float(row.get("超大单净流出", 0) or 0),
        large_in=float(row.get("大单净流入", 0) or 0),
        large_out=float(row.get("大单净流出", 0) or 0),
        medium_in=float(row.get("中单净流入", 0) or 0),
        medium_out=float(row.get("中单净流出", 0) or 0),
        small_in=float(row.get("小单净流入", 0) or 0),
        small_out=float(row.get("小单净流出", 0) or 0),
    )


# ==================== API 端点 ====================

@router.get("/{code}", response_model=StockInfo)
async def get_stock(code: str = Path(description="股票代码")):
    """
    获取股票基本信息

    优先从数据库读取，数据库没有则从AKShare实时获取
    """
    # 先尝试从数据库获取
    stock = get_stock_info_from_db(code)
    if stock and stock.price > 0:
        return stock

    # 数据库没有或价格为空，从API获取
    stock = get_stock_info_from_api(code)
    if stock:
        return stock

    raise HTTPException(status_code=404, detail=f"股票 {code} 不存在")


@router.get("/{code}/kline", response_model=list[KLineData])
async def get_kline(code: str = Path(description="股票代码"), days: int = 60):
    """
    获取股票K线数据

    优先从数据库读取，数据库没有则从AKShare实时获取
    """
    # 先尝试从数据库获取
    klines = get_kline_from_db(code, days)
    if klines:
        return klines

    # 数据库没有，从API获取
    try:
        klines = get_kline_from_api(code, days)
        if klines:
            return klines
    except Exception as e:
        logger.error(f"获取K线失败: {e}")

    raise HTTPException(status_code=404, detail=f"无法获取股票 {code} 的K线数据")


@router.get("/{code}/indicator", response_model=IndicatorData)
async def get_indicator(code: str = Path(description="股票代码")):
    """
    获取技术指标

    优先从数据库读取，数据库没有则从AKShare实时获取并计算
    """
    # 先尝试从数据库获取
    indicator = get_indicator_from_db(code)
    if indicator:
        return indicator

    # 数据库没有，从API获取并计算
    try:
        indicator = get_indicator_from_api(code)
        return indicator
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"计算指标失败: {str(e)}")


@router.get("/{code}/capital", response_model=CapitalData)
async def get_capital(code: str = Path(description="股票代码")):
    """
    获取资金流向数据

    优先从数据库读取，数据库没有则从AKShare实时获取
    """
    # 先尝试从数据库获取
    capital = get_capital_from_db(code)
    if capital and (capital.main_inflow != 0 or capital.main_outflow != 0):
        return capital

    # 数据库没有，从API获取
    try:
        capital = get_capital_from_api(code)
        return capital
    except Exception as e:
        logger.error(f"获取资金数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取资金数据失败: {str(e)}")


@router.get("/{code}/ai", response_model=AIAnalysis)
async def get_ai_analysis(code: str = Path(description="股票代码")):
    """
    获取AI分析结果

    基于技术指标和资金数据生成简单的AI分析
    """
    try:
        # 获取指标和资金数据
        indicator = get_indicator_from_api(code)
        capital = get_capital_from_api(code)

        # 简单的AI分析逻辑
        signals = []
        risks = []
        trend = "震荡"
        confidence = 50

        # MACD分析
        if indicator.dif > indicator.dea:
            signals.append("MACD金叉")
        elif indicator.dif < indicator.dea:
            signals.append("MACD死叉")

        # RSI分析
        if indicator.rsi6 > 70:
            risks.append("RSI超买")
        elif indicator.rsi6 < 30:
            signals.append("RSI超卖")

        # BOLL分析
        if indicator.boll_upper > 0:
            signals.append("BOLL通道正常")

        # 资金分析
        if capital.main_inflow > 0:
            signals.append("主力资金净流入")
        elif capital.main_inflow < 0:
            risks.append("主力资金净流出")

        # 判断趋势
        up_count = sum(1 for s in signals if s not in ["MACD死叉", "RSI超买", "主力资金净流出"])
        down_count = len(risks)

        if up_count > down_count + 1:
            trend = "上涨趋势"
            confidence = min(90, 60 + up_count * 5)
        elif down_count > up_count + 1:
            trend = "下跌趋势"
            confidence = min(90, 60 + down_count * 5)

        suggestion = "建议观望"
        if trend == "上涨趋势" and "RSI超买" not in risks:
            suggestion = "建议关注回调买点"
        elif trend == "下跌趋势":
            suggestion = "建议谨慎，控制风险"

        return AIAnalysis(
            trend=trend,
            confidence=confidence,
            signals=signals[:5] if signals else ["暂无明显信号"],
            risks=risks[:5] if risks else ["无明显风险"],
            suggestion=suggestion,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI分析失败: {e}")
        # 返回默认分析
        return AIAnalysis(
            trend="未知",
            confidence=0,
            signals=["获取数据失败"],
            risks=["无法获取数据"],
            suggestion="请稍后重试",
        )
