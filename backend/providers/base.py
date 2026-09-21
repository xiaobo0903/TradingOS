from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseProvider(ABC):
    """数据源提供商基类"""

    name: str = ""

    @abstractmethod
    def get_stock_list(self) -> List[Dict]:
        """获取A股列表"""
        pass

    @abstractmethod
    def get_realtime_price(self, stock_code: str = None) -> List[Dict]:
        """获取实时行情"""
        pass

    @abstractmethod
    def get_daily(self, stock_code: str, start_date: str, end_date: str, adjust: str = "qfq") -> List[Dict]:
        """获取日线数据"""
        pass

    @abstractmethod
    def get_minute(self, stock_code: str, period: str = "1") -> List[Dict]:
        """获取分钟数据"""
        pass

    @abstractmethod
    def get_capital_flow(self, stock_code: str) -> Dict:
        """获取资金流向"""
        pass

    @abstractmethod
    def get_sector_list(self) -> List[Dict]:
        """获取板块列表"""
        pass
