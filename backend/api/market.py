"""
市场概览 API 接口
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from providers.akshare_provider import AKShareProvider
from models.database import get_db_context
from models.stock import Stock, StockDaily


router = APIRouter(prefix="/api/market", tags=["市场"])


class IndexSpotResponse(BaseModel):
    """指数实时行情"""
    code: str
    name: str
    current_price: float
    change_pct: float
    volume: int
    amount: float
    source: Optional[str] = None


class MarketOverviewResponse(BaseModel):
    """市场概览"""
    indices: List[IndexSpotResponse]
    update_time: str


def get_realtime_indices():
    """从腾讯财经获取实时指数"""
    import requests

    indices_map = {
        'sh000001': '上证指数',
        'sz399001': '深证成指',
        'sz399006': '创业板指',
        'sh000300': '沪深300',
        'sz399905': '中小板指',
    }

    results = []
    session = requests.Session()
    session.trust_env = False

    for code, name in indices_map.items():
        try:
            url = f'https://sqt.gtimg.cn/q={code}'
            resp = session.get(url, timeout=10, proxies={'http': None, 'https': None})
            # 格式: v_sh000001="1~上证指数~000001~当前价~昨收~今开~成交量~..."
            text = resp.text.strip()
            parts = text.split('~')
            if len(parts) > 5:
                current = float(parts[3])
                yesterday = float(parts[4])
                change_pct = ((current - yesterday) / yesterday) * 100 if yesterday else 0
                change_amount = current - yesterday
                results.append({
                    "code": code[2:],  # 去掉 sh/sz 前缀
                    "name": name,
                    "current_price": current,
                    "change_pct": round(change_pct, 2),
                    "change_amount": round(change_amount, 2),
                    "volume": int(parts[6]) if parts[6].isdigit() else 0,
                    "amount": 0,
                    "source": "腾讯财经",
                })
        except Exception as e:
            print(f"获取 {name} 失败: {e}")
            continue

    return results


def get_test_indices():
    """获取测试指数数据（基于数据库中的股票）- 备用方案"""
    with get_db_context() as db:
        stocks = db.query(Stock).all()
        if not stocks:
            return []

        indices = []
        for stock in stocks[:10]:
            latest = db.query(StockDaily).filter(
                StockDaily.stock_id == stock.id
            ).order_by(StockDaily.trade_date.desc()).first()

            if latest:
                indices.append({
                    "code": stock.code,
                    "name": stock.name,
                    "current_price": float(latest.close),
                    "change_pct": float(latest.change_pct) if latest.change_pct else 0,
                    "volume": latest.volume or 0,
                    "amount": float(latest.amount) if latest.amount else 0,
                })
        return indices


def get_test_statistics():
    """获取测试统计数据（基于数据库中的股票）"""
    with get_db_context() as db:
        stocks = db.query(Stock).all()

        rising = 0
        falling = 0
        limit_up = 0
        limit_down = 0
        total_amount = 0

        for stock in stocks:
            latest = db.query(StockDaily).filter(
                StockDaily.stock_id == stock.id
            ).order_by(StockDaily.trade_date.desc()).first()

            if latest and latest.change_pct is not None:
                change_pct = float(latest.change_pct)
                if change_pct > 0:
                    rising += 1
                elif change_pct < 0:
                    falling += 1

                if change_pct >= 9.9:
                    limit_up += 1
                elif change_pct <= -9.9:
                    limit_down += 1

                total_amount += float(latest.amount) if latest.amount else 0

        return {
            "rising": rising,
            "falling": falling,
            "limit_up": limit_up,
            "limit_down": limit_down,
            "total_amount": total_amount,
        }


def get_realtime_statistics():
    """从 Tushare 获取市场统计数据（全市场精准统计）"""
    from datetime import datetime, timedelta

    try:
        import tushare as ts
        pro = ts.pro_api('2dd290408413995cd8d95d15145173a1e1aac6bcec65e5c57c830088')

        # 获取最近交易日的日期
        today = datetime.now().date()
        # 尝试获取今天或昨天的数据
        trade_date = today.strftime('%Y%m%d')

        df = pro.daily(trade_date=trade_date)

        # 如果今天没有数据，尝试昨天
        if len(df) == 0:
            yesterday = (today - timedelta(days=1)).strftime('%Y%m%d')
            df = pro.daily(trade_date=yesterday)

        if len(df) == 0:
            print(f"Tushare daily 返回 0 条记录，日期: {trade_date}")
            return None

        # 计算市场统计
        rising = len(df[df['pct_chg'] > 0])
        falling = len(df[df['pct_chg'] < 0])
        limit_up = len(df[df['pct_chg'] >= 9.9])
        limit_down = len(df[df['pct_chg'] <= -9.9])
        # amount 单位是千元，转换为元
        total_amount = df['amount'].sum() * 1000

        return {
            "rising": rising,
            "falling": falling,
            "limit_up": limit_up,
            "limit_down": limit_down,
            "total_amount": total_amount,
            "source": "Tushare",
        }
    except Exception as e:
        print(f"获取 Tushare 市场统计失败: {e}")
        return None


def get_realtime_hot_sectors(limit: int = 10):
    """从新浪财经获取热门板块"""
    import requests
    import re
    import json

    session = requests.Session()
    session.trust_env = False

    url = 'https://vip.stock.finance.sina.com.cn/q/view/newFLJK.php?param=class'
    try:
        resp = session.get(url, timeout=10, proxies={'http': None, 'https': None},
                          headers={'Referer': 'https://finance.sina.com.cn/'})

        text = resp.text.strip()
        match = re.search(r'= (\{.*\})', text, re.DOTALL)
        if not match:
            return []

        data = json.loads(match.group(1))

        items = []
        for code, info in data.items():
            parts = info.split(',')
            if len(parts) >= 5:
                try:
                    change_pct = float(parts[4]) if parts[4] else 0
                except (ValueError, TypeError):
                    change_pct = 0
                items.append({
                    '板块名称': parts[1],
                    '涨跌幅': change_pct,
                    '代码': code,
                })

        items.sort(key=lambda x: x['涨跌幅'], reverse=True)
        return items[:limit]
    except Exception as e:
        print(f"获取新浪财经板块失败: {e}")
        return []


def get_test_hot_sectors():
    """获取测试热门板块数据"""
    with get_db_context() as db:
        stocks = db.query(Stock).all()

        # 按行业分组统计
        industry_data = {}
        for stock in stocks:
            industry = stock.industry or "未知"
            latest = db.query(StockDaily).filter(
                StockDaily.stock_id == stock.id
            ).order_by(StockDaily.trade_date.desc()).first()

            if latest and latest.change_pct is not None:
                if industry not in industry_data:
                    industry_data[industry] = {"count": 0, "total_change": 0}
                industry_data[industry]["count"] += 1
                industry_data[industry]["total_change"] += float(latest.change_pct)

        # 计算平均涨跌幅并排序
        sectors = []
        for name, data in industry_data.items():
            avg_change = data["total_change"] / data["count"] if data["count"] > 0 else 0
            sectors.append({
                "板块名称": name,
                "涨跌幅": round(avg_change, 2),
                "股票数量": data["count"],
            })

        sectors.sort(key=lambda x: x["涨跌幅"], reverse=True)
        return sectors[:6]


@router.get("/indices", response_model=List[IndexSpotResponse])
def get_index_spot():
    """获取主要指数实时行情（上证、深证、创业板等）"""
    # 优先使用腾讯财经实时数据
    realtime_indices = get_realtime_indices()
    if realtime_indices:
        return realtime_indices

    # 如果腾讯财经失败，尝试 AKShare
    try:
        provider = AKShareProvider()
        data = provider.get_market_index()

        main_indices = []
        for item in data:
            code = item.get('代码', '')
            name = item.get('名称', '')

            if any(keyword in name for keyword in ['上证', '深证', '创业板', '科创', '沪深', '上证50', '沪深300']):
                main_indices.append({
                    "code": code,
                    "name": name,
                    "current_price": float(item.get('最新价', 0)),
                    "change_pct": float(item.get('涨跌幅', 0)),
                    "volume": int(item.get('成交量', 0)),
                    "amount": float(item.get('成交额', 0)),
                    "source": "东方财富",
                })

        if main_indices:
            return main_indices
    except Exception as e:
        print(f"AKShare获取指数失败，使用测试数据: {e}")

    # 最后使用数据库中的测试数据
    indices = get_test_indices()
    for idx in indices:
        idx["source"] = "测试数据"
    return indices


@router.get("/overview")
def get_market_overview():
    """获取市场整体概览"""
    # 优先使用腾讯财经实时数据
    realtime_stats = get_realtime_statistics()
    if realtime_stats:
        realtime_indices = get_realtime_indices()
        return {
            "indices": realtime_indices,
            "statistics": realtime_stats,
            "update_time": "腾讯财经",
        }

    # 尝试 AKShare
    try:
        provider = AKShareProvider()
        indices = provider.get_market_index()

        rising = 0
        falling = 0
        limit_up = 0
        limit_down = 0
        total_amount = 0

        stocks = provider.get_realtime_price()

        for stock in stocks:
            change_pct = float(stock.get('涨跌幅', 0))
            amount = float(stock.get('成交额', 0))

            if change_pct > 0:
                rising += 1
            elif change_pct < 0:
                falling += 1

            if change_pct >= 9.9:
                limit_up += 1
            elif change_pct <= -9.9:
                limit_down += 1

            total_amount += amount

        return {
            "indices": indices[:10],
            "statistics": {
                "rising": rising,
                "falling": falling,
                "limit_up": limit_up,
                "limit_down": limit_down,
                "total_amount": total_amount,
                "source": "东方财富",
            },
            "update_time": indices[0].get('时间', '') if indices else '',
        }
    except Exception as e:
        print(f"AKShare获取市场概览失败，使用测试数据: {e}")

    # 返回测试数据
    indices = get_test_indices()
    statistics = get_test_statistics()
    return {
        "indices": indices,
        "statistics": statistics,
        "update_time": "测试数据",
    }


@router.get("/hot-sectors")
def get_hot_sectors(limit: int = 10):
    """获取热门板块"""
    # 优先使用新浪财经实时数据
    realtime_sectors = get_realtime_hot_sectors(limit)
    if realtime_sectors:
        return {
            "source": "新浪财经",
            "data": realtime_sectors
        }

    # 尝试 AKShare
    try:
        import akshare as ak
        df = ak.stock_board_industry_name_em()
        df = df.sort_values('涨跌幅', ascending=False).head(limit)
        records = df.to_dict('records')
        return {
            "source": "东方财富",
            "data": records
        }
    except Exception as e:
        print(f"AKShare获取热门板块失败，使用测试数据: {e}")

    # 最后使用数据库测试数据
    sectors = get_test_hot_sectors()
    return {
        "source": "测试数据",
        "data": sectors
    }
