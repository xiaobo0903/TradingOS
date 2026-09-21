# 导入所有模型，以便 SQLAlchemy 能够创建表
from .stock import Stock, StockDaily, StockPrice
from .indicator import StockIndicator
from .capital import StockCapital
from .sector import Sector, SectorDaily
from .watchlist import WatchlistGroup, StockWatchlist
from .discovery import StockDiscovery
from .data_center import DataTask, DataQuality
from .ai import AIAnalysis

__all__ = [
    'Stock',
    'StockDaily',
    'StockPrice',
    'StockIndicator',
    'StockCapital',
    'Sector',
    'SectorDaily',
    'WatchlistGroup',
    'StockWatchlist',
    'StockDiscovery',
    'DataTask',
    'DataQuality',
    'AIAnalysis',
]
