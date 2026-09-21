from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime


class DataValidator:
    """数据验证器"""

    @staticmethod
    def validate_stock_data(data: Dict) -> bool:
        """验证股票基础数据"""
        required_fields = ['code', 'name']
        return all(data.get(f) is not None for f in required_fields)

    @staticmethod
    def validate_price_data(data: Dict) -> bool:
        """验证价格数据"""
        # 基础字段检查
        if data.get('close') is None or data.get('volume') is None:
            return False

        # 价格合理性检查
        close = float(data.get('close', 0))
        if close <= 0:
            return False

        # 如果有高低点检查
        if data.get('high') is not None and data.get('low') is not None:
            high = float(data['high'])
            low = float(data['low'])
            if high < low:
                return False

        return True

    @staticmethod
    def validate_required_fields(data: Dict, fields: List[str]) -> bool:
        """验证必填字段"""
        return all(data.get(f) is not None for f in fields)


class BaseCollector(ABC):
    """
    数据采集器基类

    定义采集器接口：
    1. collect() - 主采集方法
    2. normalizer() - 数据标准化
    3. validate() - 数据验证
    """

    def __init__(self, provider=None):
        self.provider = provider
        self.validator = DataValidator()
        self.last_collect_time: Optional[datetime] = None

    @abstractmethod
    def collect(self, **kwargs) -> List[Dict]:
        """
        主采集方法

        Returns:
            List[Dict]: 采集并标准化后的数据列表
        """
        pass

    def normalizer(self, raw_data: Dict) -> Dict:
        """
        数据标准化

        默认实现返回原始数据，子类应覆盖此方法
        """
        return raw_data

    def validate(self, data: Dict) -> bool:
        """
        数据验证

        默认实现使用 DataValidator，子类可覆盖
        """
        return True

    def collect_and_normalize(self, raw_data: List[Dict]) -> List[Dict]:
        """
        采集并标准化数据

        Args:
            raw_data: 原始数据列表

        Returns:
            标准化后的数据列表
        """
        results = []
        for raw in raw_data:
            normalized = self.normalizer(raw)
            if self.validate(normalized):
                results.append(normalized)
        return results

    def update_collect_time(self):
        """更新采集时间"""
        self.last_collect_time = datetime.now()


class PriceCollectorMixin:
    """价格数据采集器混入类"""

    def normalizer(self, raw: Dict) -> Dict:
        """标准化价格数据"""
        return {
            'stock_code': str(raw.get('代码', raw.get('code', ''))),
            'trade_date': raw.get('日期', raw.get('trade_date')),
            'open': float(raw.get('开盘', raw.get('open', 0))),
            'high': float(raw.get('最高', raw.get('high', 0))),
            'low': float(raw.get('最低', raw.get('low', 0))),
            'close': float(raw.get('收盘', raw.get('close', 0))),
            'volume': int(raw.get('成交量', raw.get('volume', 0))),
            'amount': float(raw.get('成交额', raw.get('amount', 0))),
            'turnover_rate': float(raw.get('换手率', raw.get('turnover_rate', 0))),
            'change_pct': float(raw.get('涨跌幅', raw.get('change_pct', 0))),
            'amplitude': float(raw.get('振幅', raw.get('amplitude', 0))),
        }


class StockCollectorMixin:
    """股票基础信息采集器混入类"""

    def normalizer(self, raw: Dict) -> Dict:
        """标准化股票基础数据"""
        code = str(raw.get('代码', raw.get('code', '')))
        return {
            'code': code,
            'name': raw.get('名称', raw.get('name', '')),
            'market': 'SH' if code.startswith('6') else 'SZ',
            'industry': raw.get('行业', raw.get('industry', '')),
            'price': raw.get('最新价', raw.get('price', 0)),
            'change_pct': raw.get('涨跌幅', raw.get('change_pct', 0)),
            'volume': raw.get('成交量', raw.get('volume', 0)),
            'amount': raw.get('成交额', raw.get('amount', 0)),
            'turnover_rate': raw.get('换手率', raw.get('turnover_rate', 0)),
            'pe': raw.get('市盈率-动态', raw.get('pe', '')),
            'pb': raw.get('市净率', raw.get('pb', '')),
            'total_market_cap': raw.get('总市值', raw.get('total_market_cap', '')),
            'float_market_cap': raw.get('流通市值', raw.get('float_market_cap', '')),
        }
