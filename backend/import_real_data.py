#!/usr/bin/env python3
"""
使用 Tushare 导入真实市场数据

功能：
1. 获取全市场股票列表
2. 批量获取日线数据
3. 计算技术指标
4. 保存到数据库
"""
import sys
import os
from datetime import datetime, timedelta
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tushare as ts
import pandas as pd
from sqlalchemy import text

from models.database import get_db_context, engine
from models.stock import Stock, StockStatus
from models.stock import StockDaily
from models.indicator import StockIndicator
from indicators.calculator import get_calculator


# Tushare Token
TUSHARE_TOKEN = '2dd290408413995cd8d95d15145173a1e1aac6bcec65e5c57c830088'

# 获取 Tushare API
pro = ts.pro_api(TUSHARE_TOKEN)


def to_float(val):
    """Convert numpy float to native Python float"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return float(val)


def to_int(val):
    """Convert to integer"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return int(val)


def get_stock_list():
    """获取全市场股票列表"""
    print("正在获取股票列表...")
    try:
        df = pro.stock_basic(
            ts_code='',
            market='',
            status='',
            fields='ts_code,symbol,name,area,industry,market,list_date,is_hs'
        )
        # 从 ts_code 解析市场 (000001.SZ -> SZ, 600000.SH -> SH)
        df['code'] = df['ts_code'].str.split('.').str[0]
        df['mkt'] = df['ts_code'].str.split('.').str[1]
        # 过滤沪深股票（排除北交所 BJ）
        df = df[df['mkt'].isin(['SH', 'SZ'])]
        print(f"获取到 {len(df)} 只股票")
        return df
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return None


def save_stock_list(df):
    """保存股票列表到数据库"""
    print("正在保存股票列表...")
    saved = 0
    with get_db_context() as db:
        for _, row in df.iterrows():
            code = row['code']  # 已在 get_stock_list 中解析
            market = row['mkt']  # SH 或 SZ

            # 检查是否已存在
            existing = db.query(Stock).filter(Stock.code == code).first()
            if existing:
                continue

            stock = Stock(
                code=code,
                name=row['name'],
                market=market,
                industry=row.get('industry') or '未知',
                status=StockStatus.ACTIVE,
            )
            db.add(stock)
            saved += 1

            # 批量提交
            if saved % 100 == 0:
                db.commit()
                print(f"  已保存 {saved} 只股票")

        db.commit()
    print(f"股票列表保存完成，新增 {saved} 只")


def get_daily_data(ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取单只股票的日线数据"""
    try:
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is not None and len(df) > 0:
            df = df.sort_values('trade_date')
        return df
    except Exception as e:
        print(f"获取 {ts_code} 日线数据失败: {e}")
        return pd.DataFrame()


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """计算技术指标"""
    if df.empty or len(df) < 30:
        return df

    calculator = get_calculator()

    # Tushare 返回的字段名: trade_date, ts_code, open, high, low, close, vol, amount, pct_chg
    # 重命名字段以匹配指标计算器，同时保留 pct_chg
    data = pd.DataFrame({
        'trade_date': df['trade_date'],
        'open': df['open'].apply(to_float),
        'high': df['high'].apply(to_float),
        'low': df['low'].apply(to_float),
        'close': df['close'].apply(to_float),
        'volume': df['vol'].apply(to_int),
        'pct_chg': df['pct_chg'].apply(to_float),  # 保留涨跌幅
    })

    # 计算指标
    result = calculator.calculate_all(data)

    # 确保 pct_chg 在结果中（calculator.calculate_all 可能不保留它）
    result['pct_chg'] = data['pct_chg']
    return result


def save_daily_and_indicators(stocks, start_date: str, end_date: str):
    """
    批量获取并保存日线数据和指标

    Args:
        stocks: 股票列表 DataFrame
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD
    """
    calculator = get_calculator()
    total = len(stocks)
    success = 0
    failed = 0
    batch_size = 50  # 每50只股票批量提交

    for idx, row in stocks.iterrows():
        ts_code = row['ts_code']  # 000001.SZ
        code = ts_code.split('.')[0]

        try:
            # 获取日线数据
            df = get_daily_data(ts_code, start_date, end_date)

            if df.empty:
                failed += 1
                continue

            # 计算技术指标
            df = calculate_indicators(df)

            if df is None or len(df) == 0:
                failed += 1
                continue

            # 保存到数据库
            with get_db_context() as db:
                # 获取股票ID
                stock = db.query(Stock).filter(Stock.code == code).first()
                if not stock:
                    failed += 1
                    continue

                stock_id = stock.id

                for _, day_row in df.iterrows():
                    trade_date = datetime.strptime(
                        str(day_row['trade_date']), '%Y%m%d'
                    ).date()

                    # 检查是否已存在
                    existing = db.query(StockDaily).filter(
                        StockDaily.stock_id == stock_id,
                        StockDaily.trade_date == trade_date
                    ).first()

                    # Tushare 日线字段: open, high, low, close, vol, amount, pct_chg
                    high = to_float(day_row.get('high'))
                    low = to_float(day_row.get('low'))
                    amplitude = 0
                    if high and low and low > 0:
                        amplitude = (high - low) / low * 100

                    if existing:
                        # 更新
                        existing.open = to_float(day_row.get('open'))
                        existing.high = high
                        existing.low = low
                        existing.close = to_float(day_row.get('close'))
                        existing.volume = to_int(day_row.get('vol'))
                        existing.amount = to_float(day_row.get('amount'))
                        existing.change_pct = to_float(day_row.get('pct_chg'))
                        existing.amplitude = round(amplitude, 2)
                    else:
                        # 新增日线数据
                        daily = StockDaily(
                            stock_id=stock_id,
                            trade_date=trade_date,
                            open=to_float(day_row.get('open')),
                            high=high,
                            low=low,
                            close=to_float(day_row.get('close')),
                            volume=to_int(day_row.get('vol')),
                            amount=to_float(day_row.get('amount')),
                            change_pct=to_float(day_row.get('pct_chg')),
                            amplitude=round(amplitude, 2),
                        )
                        db.add(daily)

                    # 保存指标
                    ind_data = {
                        'stock_id': stock_id,
                        'trade_date': trade_date,
                        'ma5': to_float(day_row.get('ma5')),
                        'ma10': to_float(day_row.get('ma10')),
                        'ma20': to_float(day_row.get('ma20')),
                        'ma30': to_float(day_row.get('ma30')),
                        'ma60': to_float(day_row.get('ma60')),
                        'ma120': to_float(day_row.get('ma120')),
                        'ma250': to_float(day_row.get('ma250')),
                        'ema12': to_float(day_row.get('ema12')),
                        'ema26': to_float(day_row.get('ema26')),
                        'dif': to_float(day_row.get('dif')),
                        'dea': to_float(day_row.get('dea')),
                        'macd': to_float(day_row.get('macd')),
                        'rsi6': to_float(day_row.get('rsi6')),
                        'rsi12': to_float(day_row.get('rsi12')),
                        'rsi24': to_float(day_row.get('rsi24')),
                        'boll_mb': to_float(day_row.get('boll_mb')),
                        'boll_ub': to_float(day_row.get('boll_ub')),
                        'boll_lb': to_float(day_row.get('boll_lb')),
                        'boll_width': to_float(day_row.get('boll_width')),
                        'kdj_k': to_float(day_row.get('kdj_k')),
                        'kdj_d': to_float(day_row.get('kdj_d')),
                        'kdj_j': to_float(day_row.get('kdj_j')),
                    }

                    existing_ind = db.query(StockIndicator).filter(
                        StockIndicator.stock_id == stock_id,
                        StockIndicator.trade_date == trade_date
                    ).first()

                    if existing_ind:
                        for key, value in ind_data.items():
                            if key not in ['stock_id', 'trade_date']:
                                setattr(existing_ind, key, value)
                    else:
                        indicator = StockIndicator(**ind_data)
                        db.add(indicator)

                db.commit()

            success += 1

            # 进度显示
            if success % 20 == 0:
                print(f"  进度: {success}/{total} ({success*100//total}%)")

            # Tushare 频率限制：每秒最多 200 次调
            time.sleep(0.01)

        except Exception as e:
            print(f"处理 {ts_code} 失败: {e}")
            failed += 1
            continue

    print(f"\n日线数据导入完成: 成功 {success}, 失败 {failed}")
    return success, failed


def clear_test_data():
    """清空测试数据"""
    print("正在清空测试数据...")
    with get_db_context() as db:
        # 清空指标
        db.query(StockIndicator).delete()
        # 清空日线数据
        db.query(StockDaily).delete()
        # 清空股票发现记录
        from models.discovery import StockDiscovery
        db.query(StockDiscovery).delete()
        db.commit()
    print("测试数据已清空")


def main():
    print("=" * 50)
    print("TradingOS 真实数据导入工具 (Tushare)")
    print("=" * 50)

    # 确认操作
    print("\n操作说明:")
    print("1. 获取全市场股票列表")
    print("2. 批量获取日线数据（最近250个交易日）")
    print("3. 计算技术指标")
    print("4. 保存到数据库")
    print("\n注意: 这将清空现有的测试数据")

    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')

    print(f"\n日期范围: {start_str} ~ {end_str}")

    # 步骤1: 获取股票列表
    stocks_df = get_stock_list()
    if stocks_df is None or stocks_df.empty:
        print("获取股票列表失败，退出")
        return

    # 步骤2: 清空测试数据
    confirm = input("\n是否清空现有测试数据？(y/n): ")
    if confirm.lower() == 'y':
        clear_test_data()

    # 步骤3: 保存股票列表
    save_stock_list(stocks_df)

    # 步骤4: 获取并保存日线数据和指标
    print("\n开始获取日线数据（这可能需要较长时间）...")
    success, failed = save_daily_and_indicators(stocks_df, start_str, end_str)

    print("\n" + "=" * 50)
    print("数据导入完成!")
    print(f"成功: {success} 只股票")
    print(f"失败: {failed} 只股票")
    print("=" * 50)


if __name__ == "__main__":
    main()
