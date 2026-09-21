#!/usr/bin/env python3
"""
导入测试数据
用于在没有网络连接时测试系统功能
"""
import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db_context
from models.stock import Stock, StockStatus
from models.stock import StockDaily
from models.indicator import StockIndicator


def to_float(val):
    """Convert numpy float to native Python float"""
    if val is None:
        return None
    return float(val)


def import_test_stocks():
    """导入测试股票数据"""
    test_stocks = [
        {"code": "600000", "name": "浦发银行", "market": "SH", "industry": "银行"},
        {"code": "000001", "name": "平安银行", "market": "SZ", "industry": "银行"},
        {"code": "600519", "name": "贵州茅台", "market": "SH", "industry": "白酒"},
        {"code": "000858", "name": "五粮液", "market": "SZ", "industry": "白酒"},
        {"code": "601318", "name": "中国平安", "market": "SH", "industry": "保险"},
        {"code": "000333", "name": "美的集团", "market": "SZ", "industry": "家电"},
        {"code": "600276", "name": "恒瑞医药", "market": "SH", "industry": "医药"},
        {"code": "002594", "name": "比亚迪", "market": "SZ", "industry": "汽车"},
        {"code": "600887", "name": "伊利股份", "market": "SH", "industry": "乳业"},
        {"code": "300750", "name": "宁德时代", "market": "SZ", "industry": "新能源"},
        {"code": "002475", "name": "立讯精密", "market": "SZ", "industry": "消费电子"},
        {"code": "601012", "name": "隆基绿能", "market": "SH", "industry": "光伏"},
        {"code": "002230", "name": "科大讯飞", "market": "SZ", "industry": "人工智能"},
    ]

    with get_db_context() as db:
        for stock_data in test_stocks:
            existing = db.query(Stock).filter(Stock.code == stock_data["code"]).first()
            if not existing:
                stock = Stock(
                    code=stock_data["code"],
                    name=stock_data["name"],
                    market=stock_data["market"],
                    industry=stock_data["industry"],
                    status=StockStatus.ACTIVE
                )
                db.add(stock)
        db.commit()
        print(f"成功导入 {len(test_stocks)} 只测试股票")


def import_test_daily_data():
    """为测试股票生成日线数据"""
    with get_db_context() as db:
        stocks = db.query(Stock).all()
        today = datetime.now().date()

        for stock in stocks:
            # 检查是否已有数据
            existing = db.query(StockDaily).filter(StockDaily.stock_id == stock.id).first()
            if existing:
                continue

            # 生成最近60个交易日的数据
            base_price = random.uniform(10, 200)
            for i in range(60, 0, -1):
                trade_date = today - timedelta(days=i)
                # 跳过周末
                if trade_date.weekday() >= 5:
                    continue

                # 随机波动
                change = random.uniform(-0.05, 0.05)
                open_price = base_price * (1 + random.uniform(-0.02, 0.02))
                close_price = open_price * (1 + change)
                high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
                low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))

                daily = StockDaily(
                    stock_id=stock.id,
                    trade_date=trade_date,
                    open=round(open_price, 2),
                    high=round(high_price, 2),
                    low=round(low_price, 2),
                    close=round(close_price, 2),
                    volume=random.randint(1000000, 50000000),
                    amount=round(random.uniform(1e8, 5e9), 2),
                    turnover_rate=round(random.uniform(0.1, 5.0), 2),
                    change_pct=round(change * 100, 2),
                    amplitude=round(random.uniform(1, 5), 2)
                )
                db.add(daily)
                base_price = close_price

            # 计算并保存指标
            calculate_and_save_indicators(stock.id, db)

        db.commit()
        print(f"成功为 {len(stocks)} 只股票生成日线数据和指标")


def calculate_and_save_indicators(stock_id, db):
    """计算并保存技术指标"""
    import pandas as pd
    from indicators.calculator import get_calculator

    # 获取该股票的日线数据
    daily_data = db.query(StockDaily).filter(
        StockDaily.stock_id == stock_id
    ).order_by(StockDaily.trade_date).all()

    if len(daily_data) < 30:
        return

    # 转换为 DataFrame
    df = pd.DataFrame([{
        'trade_date': d.trade_date,
        'open': float(d.open),
        'high': float(d.high),
        'low': float(d.low),
        'close': float(d.close),
        'volume': d.volume
    } for d in daily_data])

    # 计算指标
    calculator = get_calculator()
    result = calculator.calculate_all(df)

    # 保存最新一天的指标
    latest = result.iloc[-1]

    indicator = StockIndicator(
        stock_id=stock_id,
        trade_date=daily_data[-1].trade_date,
        ma5=to_float(latest.get('ma5')),
        ma10=to_float(latest.get('ma10')),
        ma20=to_float(latest.get('ma20')),
        ma30=to_float(latest.get('ma30')),
        ma60=to_float(latest.get('ma60')),
        ma120=to_float(latest.get('ma120')),
        ma250=to_float(latest.get('ma250')),
        ema12=to_float(latest.get('ema12')),
        ema26=to_float(latest.get('ema26')),
        dif=to_float(latest.get('dif')),
        dea=to_float(latest.get('dea')),
        macd=to_float(latest.get('macd')),
        rsi6=to_float(latest.get('rsi6')),
        rsi12=to_float(latest.get('rsi12')),
        rsi24=to_float(latest.get('rsi24')),
        boll_mb=to_float(latest.get('boll_mb')),
        boll_ub=to_float(latest.get('boll_ub')),
        boll_lb=to_float(latest.get('boll_lb')),
        boll_width=to_float(latest.get('boll_width')),
        kdj_k=to_float(latest.get('kdj_k')),
        kdj_d=to_float(latest.get('kdj_d')),
        kdj_j=to_float(latest.get('kdj_j')),
    )
    db.add(indicator)


if __name__ == "__main__":
    print("开始导入测试数据...")
    import_test_stocks()
    import_test_daily_data()
    print("测试数据导入完成!")
