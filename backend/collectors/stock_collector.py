"""
股票基础信息采集器
"""
from typing import List, Dict, Optional
from datetime import datetime

from collectors.base import BaseCollector, StockCollectorMixin
from models.database import get_db_context
from models.stock import Stock, StockStatus


class StockCollector(BaseCollector, StockCollectorMixin):
    """
    股票基础信息采集器

    从数据源获取A股列表，并更新到数据库
    """

    name = "stock_collector"

    def collect(self, force: bool = False, **kwargs) -> List[Dict]:
        """
        采集股票列表

        Args:
            force: 是否强制更新已有股票

        Returns:
            采集并标准化后的股票列表
        """
        raw_data = self.provider.get_stock_list()

        if not raw_data:
            return []

        # 标准化数据
        stocks = self.collect_and_normalize(raw_data)

        # 保存到数据库
        self._save_stocks(stocks, force=force)

        self.update_collect_time()
        return stocks

    def _save_stocks(self, stocks: List[Dict], force: bool = False):
        """保存股票列表到数据库"""
        with get_db_context() as db:
            for stock_data in stocks:
                code = stock_data['code']

                # 查询是否已存在
                existing = db.query(Stock).filter(Stock.code == code).first()

                if existing:
                    if force:
                        # 强制更新
                        existing.name = stock_data.get('name', existing.name)
                        existing.industry = stock_data.get('industry', existing.industry)
                        existing.status = StockStatus.ACTIVE
                else:
                    # 新增
                    new_stock = Stock(
                        code=code,
                        name=stock_data.get('name', ''),
                        market=stock_data.get('market', ''),
                        industry=stock_data.get('industry', ''),
                        status=StockStatus.ACTIVE,
                    )
                    db.add(new_stock)

            db.commit()

    def get_stock_by_code(self, code: str) -> Optional[Dict]:
        """根据代码获取股票信息"""
        with get_db_context() as db:
            stock = db.query(Stock).filter(Stock.code == code).first()
            if stock:
                return {
                    'id': stock.id,
                    'code': stock.code,
                    'name': stock.name,
                    'market': stock.market,
                    'industry': stock.industry,
                    'status': stock.status.value if stock.status else None,
                }
            return None
