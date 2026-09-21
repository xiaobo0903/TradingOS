"""
资金流向数据采集器
"""
from typing import List, Dict, Optional
from datetime import datetime

from collectors.base import BaseCollector
from models.database import get_db_context
from models.stock import Stock
from models.capital import StockCapital
from utils.logging import app_logger


class CapitalCollector(BaseCollector):
    """
    资金流向数据采集器

    从数据源获取股票资金流向数据
    """

    name = "capital_collector"

    def collect(self, stock_code: str = None, **kwargs) -> List[Dict]:
        """
        采集资金流向数据

        Args:
            stock_code: 股票代码，如果为None则采集所有股票

        Returns:
            采集并标准化后的资金流向数据列表
        """
        results = []

        if stock_code:
            # 单只股票
            data = self.provider.get_capital_flow(stock_code)
            if data:
                normalized = self.normalizer(stock_code, data)
                if normalized:
                    results.append(normalized)
                    self._save_capital(stock_code, normalized)
        else:
            # 全市场 - 获取所有股票的资金流
            from collectors.stock_collector import StockCollector
            stock_collector = StockCollector(self.provider)
            stocks = stock_collector.collect()

            for stock in stocks:
                try:
                    data = self.provider.get_capital_flow(stock['code'])
                    if data:
                        normalized = self.normalizer(stock['code'], data)
                        if normalized:
                            results.append(normalized)
                            self._save_capital(stock['code'], normalized)
                except Exception as e:
                    app_logger.error(f"采集资金流向失败 {stock['code']}: {e}", category="COLLECTOR")
                    continue

        self.update_collect_time()
        return results

    def normalizer(self, stock_code: str, raw_data: Dict) -> Optional[Dict]:
        """
        标准化资金流向数据

        AKShare的资金流数据格式可能有所不同，这里做兼容处理
        """
        if not raw_data:
            return None

        # 尝试不同的列名格式
        return {
            'stock_code': stock_code,
            'trade_time': datetime.now(),
            'main_inflow': raw_data.get('主力净流入', raw_data.get('main_net_inflow', 0)),
            'main_outflow': raw_data.get('主力净流出', raw_data.get('main_net_outflow', 0)),
            'super_large_inflow': raw_data.get('超大单净流入', raw_data.get('super_large_net_inflow', 0)),
            'super_large_outflow': raw_data.get('超大单净流出', raw_data.get('super_large_net_outflow', 0)),
            'large_inflow': raw_data.get('大单净流入', raw_data.get('large_net_inflow', 0)),
            'large_outflow': raw_data.get('大单净流出', raw_data.get('large_net_outflow', 0)),
            'medium_inflow': raw_data.get('中单净流入', raw_data.get('medium_net_inflow', 0)),
            'medium_outflow': raw_data.get('中单净流出', raw_data.get('medium_net_outflow', 0)),
            'small_inflow': raw_data.get('小单净流入', raw_data.get('small_net_inflow', 0)),
            'small_outflow': raw_data.get('小单净流出', raw_data.get('small_net_outflow', 0)),
            'net_inflow': raw_data.get('净流入', raw_data.get('net_inflow', 0)),
        }

    def validate(self, data: Dict) -> bool:
        """验证资金流向数据"""
        if not data.get('stock_code'):
            return False
        return True

    def _save_capital(self, stock_code: str, capital_data: Dict):
        """保存资金流向数据到数据库"""
        with get_db_context() as db:
            stock = db.query(Stock).filter(Stock.code == stock_code).first()
            if not stock:
                app_logger.warning(f"股票 {stock_code} 未找到，跳过资金流向", category="COLLECTOR")
                return

            stock_id = stock.id

            new_capital = StockCapital(
                stock_id=stock_id,
                trade_time=capital_data.get('trade_time', datetime.now()),
                trade_date=capital_data.get('trade_time', datetime.now()),
                main_inflow=capital_data.get('main_inflow', 0),
                main_outflow=capital_data.get('main_outflow', 0),
                super_large_inflow=capital_data.get('super_large_inflow', 0),
                super_large_outflow=capital_data.get('super_large_outflow', 0),
                large_inflow=capital_data.get('large_inflow', 0),
                large_outflow=capital_data.get('large_outflow', 0),
                medium_inflow=capital_data.get('medium_inflow', 0),
                medium_outflow=capital_data.get('medium_outflow', 0),
                small_inflow=capital_data.get('small_inflow', 0),
                small_outflow=capital_data.get('small_outflow', 0),
                net_inflow=capital_data.get('net_inflow', 0),
            )
            db.add(new_capital)
            db.commit()
