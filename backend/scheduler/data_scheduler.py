"""
TradingOS 数据采集定时任务

功能：
- 交易时段每30分钟采集板块+资金流数据
- 每日16:00后采集日线数据
- 每周一09:00更新股票列表
"""
import os
import sys
from datetime import datetime, date

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers import cron, interval
import logging

from utils.logging import app_logger

# 配置日志
logger = logging.getLogger('apscheduler')
logger.setLevel(logging.INFO)


def is_trading_day():
    """判断是否为交易日（周一至周五）"""
    today = date.today()
    # 0=周一, 6=周日
    return today.weekday() < 5


def collect_sectors():
    """采集板块数据"""
    if not is_trading_day():
        app_logger.info("非交易日，跳过板块数据采集", category="COLLECTOR")
        return

    try:
        from collectors.sector_collector import SectorCollector
        collector = SectorCollector()
        sectors = collector.collect()
        saved = collector.save_sectors(sectors)
        app_logger.info(f"定时任务：板块数据采集完成，获取 {len(sectors)} 个，保存 {saved} 个", category="COLLECTOR")
    except Exception as e:
        app_logger.error(f"定时任务：板块数据采集失败: {e}", category="COLLECTOR")


def collect_capital_flow():
    """采集资金流数据"""
    if not is_trading_day():
        app_logger.info("非交易日，跳过资金流数据采集", category="COLLECTOR")
        return

    try:
        from collectors.capital_flow_collector import CapitalFlowCollector
        from models.database import get_db_context
        from models.stock import Stock

        collector = CapitalFlowCollector()

        with get_db_context() as db:
            stocks = db.query(Stock).filter(Stock.status == 'active').all()
            stock_codes = [f"{'sh' if s.market == 'SH' else 'sz'}{s.code}" for s in stocks]

        saved_count = 0
        for i in range(0, len(stock_codes), 50):
            batch = stock_codes[i:i + 50]
            try:
                data = collector._fetch_batch_capital(','.join(batch))
                if data:
                    saved_count += collector.save_capital_flow(data)
            except Exception:
                continue

        app_logger.info(f"定时任务：资金流数据采集完成，共 {saved_count} 条", category="COLLECTOR")
    except Exception as e:
        app_logger.error(f"定时任务：资金流数据采集失败: {e}", category="COLLECTOR")


def collect_daily_data():
    """采集日线数据（收盘后）"""
    if not is_trading_day():
        app_logger.info("非交易日，跳过日线数据采集", category="COLLECTOR")
        return

    try:
        import tushare as ts
        import pandas as pd
        from models.database import get_db_context
        from models.stock import Stock, StockDaily
        from models.indicator import StockIndicator
        from indicators.calculator import get_calculator

        TUSHARE_TOKEN = '2dd290408413995cd8d95d15145173a1e1aac6bcec65e5c57c830088'
        pro = ts.pro_api(TUSHARE_TOKEN)
        calculator = get_calculator()

        def to_float(val):
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None
            return float(val)

        def to_int(val):
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None
            return int(val)

        # 获取今日日期
        today = datetime.now().strftime('%Y%m%d')

        with get_db_context() as db:
            stocks = db.query(Stock).filter(Stock.status == 'active').all()
            stock_list = [(s.id, s.code, s.market) for s in stocks]

        success = 0
        for stock_id, stock_code, stock_market in stock_list:
            ts_code = f"{stock_code}.{'SH' if stock_market == 'SH' else 'SZ'}"
            try:
                df = pro.daily(ts_code=ts_code, start_date=today, end_date=today)
                if df is None or len(df) == 0:
                    continue

                df = df.sort_values('trade_date')

                # 计算指标
                if len(df) >= 1:
                    data = pd.DataFrame({
                        'trade_date': df['trade_date'],
                        'open': df['open'].apply(to_float),
                        'high': df['high'].apply(to_float),
                        'low': df['low'].apply(to_float),
                        'close': df['close'].apply(to_float),
                        'volume': df['vol'].apply(to_int),
                    })
                    df = calculator.calculate_all(data)

                with get_db_context() as db:
                    for _, day_row in df.iterrows():
                        trade_date = datetime.strptime(str(day_row['trade_date']), '%Y%m%d').date()

                        existing = db.query(StockDaily).filter(
                            StockDaily.stock_id == stock_id,
                            StockDaily.trade_date == trade_date
                        ).first()

                        high = to_float(day_row.get('high'))
                        low = to_float(day_row.get('low'))
                        amplitude = 0
                        if high and low and low > 0:
                            amplitude = (high - low) / low * 100

                        pct_chg = to_float(day_row.get('pct_chg')) if 'pct_chg' in day_row else 0

                        if existing:
                            existing.open = to_float(day_row.get('open'))
                            existing.high = high
                            existing.low = low
                            existing.close = to_float(day_row.get('close'))
                            existing.volume = to_int(day_row.get('vol'))
                            existing.amount = to_float(day_row.get('amount'))
                            existing.change_pct = pct_chg
                            existing.amplitude = round(amplitude, 2)
                        else:
                            daily = StockDaily(
                                stock_id=stock_id,
                                trade_date=trade_date,
                                open=to_float(day_row.get('open')),
                                high=high,
                                low=low,
                                close=to_float(day_row.get('close')),
                                volume=to_int(day_row.get('vol')),
                                amount=to_float(day_row.get('amount')),
                                change_pct=pct_chg,
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
                            'dif': to_float(day_row.get('dif')),
                            'dea': to_float(day_row.get('dea')),
                            'macd': to_float(day_row.get('macd')),
                            'rsi6': to_float(day_row.get('rsi6')),
                            'rsi12': to_float(day_row.get('rsi12')),
                            'rsi24': to_float(day_row.get('rsi24')),
                            'boll_mb': to_float(day_row.get('boll_mb')),
                            'boll_ub': to_float(day_row.get('boll_ub')),
                            'boll_lb': to_float(day_row.get('boll_lb')),
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
                import time
                time.sleep(0.01)

            except Exception:
                continue

        app_logger.info(f"定时任务：日线数据采集完成，成功 {success} 只", category="COLLECTOR")
    except Exception as e:
        app_logger.error(f"定时任务：日线数据采集失败: {e}", category="COLLECTOR")


def update_stock_list():
    """更新股票列表（每周一）"""
    try:
        from providers.akshare_provider import AKShareProvider
        from collectors.stock_collector import StockCollector

        provider = AKShareProvider()
        collector = StockCollector(provider)
        stocks = collector.collect(force=True)
        app_logger.info(f"定时任务：股票列表更新完成，共 {len(stocks)} 只", category="COLLECTOR")
    except Exception as e:
        app_logger.error(f"定时任务：股票列表更新失败: {e}", category="COLLECTOR")


def run_discovery():
    """执行股票发现任务"""
    if not is_trading_day():
        return

    try:
        from services.discovery_service import get_discovery_service

        service = get_discovery_service()
        discoveries = service.discover(period='short', limit=50, min_score=60)
        if discoveries:
            service.save_discoveries(discoveries)
        app_logger.info(f"定时任务：股票发现完成，找到 {len(discoveries)} 只候选", category="DISCOVERY")
    except Exception as e:
        app_logger.error(f"定时任务：股票发现失败: {e}", category="DISCOVERY")


def collect_realtime_data():
    """采集实时行情数据（15:30收盘后）"""
    if not is_trading_day():
        app_logger.info("非交易日，跳过实时行情采集", category="COLLECTOR")
        return

    try:
        from collectors.realtime_collector import TushareRealtimeCollector

        collector = TushareRealtimeCollector()
        data = collector.collect()
        saved = collector.save_realtime_data(data)
        app_logger.info(f"定时任务：实时行情采集完成，获取 {len(data)} 条，保存 {saved} 条", category="COLLECTOR")
    except Exception as e:
        app_logger.error(f"定时任务：实时行情采集失败: {e}", category="COLLECTOR")


# 创建调度器
scheduler = BackgroundScheduler(timezone='Asia/Shanghai')


def start_scheduler():
    """启动定时任务调度器"""
    if scheduler.running:
        app_logger.info("调度器已在运行中", category="SYSTEM")
        return

    # 交易日每30分钟采集板块+资金流 (09:30-14:30)
    scheduler.add_job(
        collect_sectors,
        trigger='cron',
        hour='9-14',
        minute='30',
        id='collect_sectors',
        name='采集板块数据',
        replace_existing=True
    )

    scheduler.add_job(
        collect_capital_flow,
        trigger='cron',
        hour='9-14',
        minute='30',
        id='collect_capital_flow',
        name='采集资金流数据',
        replace_existing=True
    )

    # 每日16:00采集日线数据
    scheduler.add_job(
        collect_daily_data,
        trigger='cron',
        hour=16,
        minute=0,
        id='collect_daily',
        name='采集日线数据',
        replace_existing=True
    )

    # 每周一09:00更新股票列表
    scheduler.add_job(
        update_stock_list,
        trigger='cron',
        day_of_week='mon',
        hour=9,
        minute=0,
        id='update_stocks',
        name='更新股票列表',
        replace_existing=True
    )

    # 每日15:30采集实时行情数据（收盘后）
    scheduler.add_job(
        collect_realtime_data,
        trigger='cron',
        hour=15,
        minute=30,
        id='collect_realtime',
        name='采集实时行情',
        replace_existing=True
    )

    # 每日17:00执行股票发现
    scheduler.add_job(
        run_discovery,
        trigger='cron',
        hour=17,
        minute=0,
        id='run_discovery',
        name='执行股票发现',
        replace_existing=True
    )

    scheduler.start()
    app_logger.info("定时任务调度器已启动", category="SYSTEM")

    # 输出所有任务
    jobs = scheduler.get_jobs()
    for job in jobs:
        app_logger.info(f"  任务: {job.name} (ID: {job.id}, 下次执行: {job.next_run_time})", category="SYSTEM")


def stop_scheduler():
    """停止定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        app_logger.info("定时任务调度器已停止", category="SYSTEM")


def get_scheduler_status():
    """获取调度器状态"""
    if not scheduler.running:
        return {"status": "stopped", "jobs": []}

    jobs = scheduler.get_jobs()
    job_list = []
    for job in jobs:
        job_list.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        })

    return {"status": "running", "jobs": job_list}
