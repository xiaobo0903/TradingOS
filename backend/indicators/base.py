from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd


class BaseIndicator(ABC):
    """所有技术指标的基类"""

    name: str = ""

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算指标值"""
        pass

    @abstractmethod
    def get_params(self) -> Dict:
        """返回指标参数"""
        pass
