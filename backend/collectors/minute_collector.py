"""
分钟数据采集器
"""
from typing import List, Dict, Optional
from datetime import datetime

from collectors.base import BaseCollector, PriceCollectorMixin
from models.database import get_db_context
from models.stock import Stock, StockPrice
from utils.logging import app_logger


class MinuteCollector(BaseCollector, PriceCollectorMixin):
    """
    分钟数据采集器

    从数据源获取股票分钟级数据
    """

    name = "minute_collector"

    def collect(self, stock_code: str, period: str = "1", **kwargs) -> List[Dict]:
        """
        采集分钟数据

        Args:
            stock_code: 股票代码
            period: 周期，"1"=1分钟，"5"=5分钟，"15"=15分钟，"30"=30分钟，"60"=60分钟

        Returns:
            采集并标准化后的分钟数据列表
        """
        raw_data = self.provider.get_minute(stock_code, period)

        if not raw_data:
            return []

        # 标准化
        minute_data = self._normalize_minute(raw_data)

        # 过滤有效数据
        minute_data = [d for d in minute_data if self.validate(d)]

        # 保存到数据库
        self._save_minute(stock_code, minute_data)

        self.update_collect_time()
        return minute_data

    def _normalize_minute(self, raw_data: List[Dict]) -> List[Dict]:
        """标准化分钟数据"""
        results = []
        for raw in raw_data:
            # 尝试多种可能的列名
            time_val = raw.get('时间', raw.get('time', raw.get('datetime', '')))
            if not time_val:
                continue

            results.append({
                'stock_code': raw.get('代码', raw.get('code', '')),
                'timestamp': time_val,
                'open': float(raw.get('开盘', raw.get('open', 0))),
                'high': float(raw.get('最高', raw.get('high', 0))),
                'low': float(raw.get('最低', raw.get('low', 0))),
                'close': float(raw.get('收盘', raw.get('close', 0))),
                'volume': int(raw.get('成交量', raw.get('volume', 0))),
                'amount': float(raw.get('成交额', raw.get('amount', 0))),
            })
        return results

    def validate(self, data: Dict) -> bool:
        """验证分钟数据"""
        if not data.get('timestamp'):
            return False
        if data.get('close') is None or data.get('close') <= 0:
            return False
        return True

    def _save_minute(self, stock_code: str, minute_data: List[Dict]):
        """保存分钟数据到数据库"""
        with get_db_context() as db:
            stock = db.query(Stock).filter(Stock.code == stock_code).first()
            if not stock:
                app_logger.warning(f"股票 {stock_code} 未找到，跳过分钟数据", category="COLLECTOR")
                return

            stock_id = stock.id

            for data in minute_data:
                timestamp = data.get('timestamp')
                if isinstance(timestamp, str):
                    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')

                new_price = StockPrice(
                    stock_id=stock_id,
                    timestamp=timestamp,
                    open=data.get('open'),
                    high=data.get('high'),
                    low=data.get('low'),
                    close=data.get('close'),
                    volume=data.get('volume'),
                    amount=data.get('amount'),
                )
                db.add(new_price)

            db.commit()
