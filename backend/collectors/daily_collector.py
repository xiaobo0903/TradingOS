"""
日线数据采集器
"""
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta

from collectors.base import BaseCollector, PriceCollectorMixin
from models.database import get_db_context
from models.stock import Stock, StockDaily
from indicators.calculator import get_calculator
from utils.logging import app_logger


class DailyCollector(BaseCollector, PriceCollectorMixin):
    """
    日线数据采集器

    从数据源获取股票日线数据，并计算技术指标
    """

    name = "daily_collector"

    def __init__(self, provider):
        super().__init__(provider)
        self.calculator = get_calculator()

    def collect(self, stock_code: str = None, start_date: str = None, end_date: str = None, **kwargs) -> List[Dict]:
        """
        采集日线数据

        Args:
            stock_code: 股票代码，如果为None则采集所有股票
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD

        Returns:
            采集并标准化后的日线数据列表
        """
        # 默认时间范围：最近250个交易日
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            # 大约一年前的日期
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

        results = []

        if stock_code:
            # 单只股票
            results = self._collect_single(stock_code, start_date, end_date)
        else:
            # 全市场 - 需要先获取股票列表
            from collectors.stock_collector import StockCollector
            stock_collector = StockCollector(self.provider)
            stocks = stock_collector.collect()

            for stock in stocks:
                try:
                    data = self._collect_single(stock['code'], start_date, end_date)
                    results.extend(data)
                except Exception as e:
                    app_logger.error(f"采集日线数据失败 {stock['code']}: {e}", category="COLLECTOR")
                    continue

        self.update_collect_time()
        return results

    def _collect_single(self, stock_code: str, start_date: str, end_date: str) -> List[Dict]:
        """采集单只股票的日线数据"""
        raw_data = self.provider.get_daily(stock_code, start_date, end_date)

        if not raw_data:
            return []

        # 标准化
        daily_data = self.collect_and_normalize(raw_data)

        # 保存到数据库
        self._save_daily(stock_code, daily_data)

        # 计算技术指标
        self._calculate_indicators(stock_code, daily_data)

        return daily_data

    def _save_daily(self, stock_code: str, daily_data: List[Dict]):
        """保存日线数据到数据库"""
        with get_db_context() as db:
            # 获取股票ID
            stock = db.query(Stock).filter(Stock.code == stock_code).first()
            if not stock:
                app_logger.warning(f"股票 {stock_code} 未找到，跳过日线数据", category="COLLECTOR")
                return

            stock_id = stock.id

            for data in daily_data:
                trade_date = data.get('trade_date')
                if isinstance(trade_date, str):
                    from datetime import datetime
                    trade_date = datetime.strptime(trade_date, '%Y-%m-%d').date()

                # 检查是否已存在
                existing = db.query(StockDaily).filter(
                    StockDaily.stock_id == stock_id,
                    StockDaily.trade_date == trade_date
                ).first()

                if existing:
                    # 更新
                    existing.open = data.get('open')
                    existing.high = data.get('high')
                    existing.low = data.get('low')
                    existing.close = data.get('close')
                    existing.volume = data.get('volume')
                    existing.amount = data.get('amount')
                    existing.turnover_rate = data.get('turnover_rate')
                    existing.change_pct = data.get('change_pct')
                    existing.amplitude = data.get('amplitude')
                else:
                    # 新增
                    new_daily = StockDaily(
                        stock_id=stock_id,
                        trade_date=trade_date,
                        open=data.get('open'),
                        high=data.get('high'),
                        low=data.get('low'),
                        close=data.get('close'),
                        volume=data.get('volume'),
                        amount=data.get('amount'),
                        turnover_rate=data.get('turnover_rate'),
                        change_pct=data.get('change_pct'),
                        amplitude=data.get('amplitude'),
                    )
                    db.add(new_daily)

            db.commit()

    def _calculate_indicators(self, stock_code: str, daily_data: List[Dict]):
        """计算并保存技术指标"""
        if not daily_data:
            return

        import pandas as pd

        # 转换为DataFrame
        df = pd.DataFrame(daily_data)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date')

        # 计算指标
        df = self.calculator.calculate_all(df)

        # 保存指标到数据库
        with get_db_context() as db:
            stock = db.query(Stock).filter(Stock.code == stock_code).first()
            if not stock:
                return

            stock_id = stock.id

            for _, row in df.iterrows():
                trade_date = row['trade_date'].date()

                # 检查是否已存在
                from models.indicator import StockIndicator
                existing = db.query(StockIndicator).filter(
                    StockIndicator.stock_id == stock_id,
                    StockIndicator.trade_date == trade_date
                ).first()

                indicator_data = {
                    'stock_id': stock_id,
                    'trade_date': trade_date,
                    'ma5': row.get('ma5'),
                    'ma10': row.get('ma10'),
                    'ma20': row.get('ma20'),
                    'ma30': row.get('ma30'),
                    'ma60': row.get('ma60'),
                    'ma120': row.get('ma120'),
                    'ma250': row.get('ma250'),
                    'ema12': row.get('ema12'),
                    'ema26': row.get('ema26'),
                    'dif': row.get('dif'),
                    'dea': row.get('dea'),
                    'macd': row.get('macd'),
                    'rsi6': row.get('rsi6'),
                    'rsi12': row.get('rsi12'),
                    'rsi24': row.get('rsi24'),
                    'boll_mb': row.get('boll_mb'),
                    'boll_ub': row.get('boll_ub'),
                    'boll_lb': row.get('boll_lb'),
                    'boll_width': row.get('boll_width'),
                    'kdj_k': row.get('kdj_k'),
                    'kdj_d': row.get('kdj_d'),
                    'kdj_j': row.get('kdj_j'),
                }

                if existing:
                    # 更新
                    for key, value in indicator_data.items():
                        if key not in ['stock_id', 'trade_date']:
                            setattr(existing, key, value)
                else:
                    # 新增
                    new_indicator = StockIndicator(**indicator_data)
                    db.add(new_indicator)

            db.commit()
