from fastapi import APIRouter, Path
from models.schemas import IndicatorData

router = APIRouter()


@router.get("/{code}", response_model=IndicatorData)
async def get_indicator(code: str = Path(description="股票代码")):
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


@router.get("/{code}/macd")
async def get_macd_analysis(code: str = Path(description="股票代码")):
    return {
        "dif": 12.35,
        "dea": 8.67,
        "macd": 7.36,
        "signal": "金叉" if 12.35 > 8.67 else "死叉",
        "position": "0轴上方" if 12.35 > 0 else "0轴下方",
        "trend": "多头增强" if 12.35 > 8.67 and 12.35 > 0 else "空头趋势"
    }


@router.get("/{code}/rsi")
async def get_rsi_analysis(code: str = Path(description="股票代码")):
    rsi = 68.5
    return {
        "rsi6": rsi,
        "rsi12": 65.3,
        "rsi24": 62.8,
        "status": "超买" if rsi > 80 else ("超卖" if rsi < 20 else "正常"),
        "interpretation": "RSI指标处于强势区域但接近超买边界，建议谨慎追高"
    }


@router.get("/{code}/boll")
async def get_boll_analysis(code: str = Path(description="股票代码")):
    return {
        "upper": 1685.25,
        "mid": 1650.0,
        "lower": 1614.75,
        "position": "突破上轨" if True else "中轨附近",
        "status": "强势上涨",
        "interpretation": "股价突破布林带上轨，强势特征明显"
    }


@router.get("/{code}/kdj")
async def get_kdj_analysis(code: str = Path(description="股票代码")):
    return {
        "k": 72.5,
        "d": 68.3,
        "j": 81.2,
        "signal": "金叉" if 72.5 > 68.3 else "死叉",
        "status": "偏强",
        "interpretation": "KDJ指标金叉向上，J值较高显示短期强势"
    }
