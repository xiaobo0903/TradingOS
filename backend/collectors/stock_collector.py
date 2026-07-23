"""
股票基础信息采集模块
使用 AKShare 获取 A 股实时行情和基本信息
"""

import akshare as ak
import pandas as pd
from typing import List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockCollector:
    """股票信息采集器"""

    def __init__(self):
        self.exchange_map = {
            "SH": "SH",  # 上海
            "SZ": "SZ",  # 深圳
        }

    def get_all_stocks_spot(self) -> pd.DataFrame:
        """
        获取所有 A 股实时行情
        返回: 包含 code, name, price, change, volume 等字段的 DataFrame
        """
        logger.info("正在获取所有 A 股实时行情...")
        try:
            df = ak.stock_zh_a_spot_em()
            logger.info(f"获取到 {len(df)} 只股票的信息")
            return df
        except Exception as e:
            logger.error(f"获取股票行情失败: {e}")
            return pd.DataFrame()

    def get_stock_info(self, symbol: str) -> Optional[dict]:
        """
        获取单只股票信息

        Args:
            symbol: 股票代码，如 "600519"
        """
        df = self.get_all_stocks_spot()
        if df.empty:
            return None

        # 匹配股票代码
        stock = df[df["代码"] == symbol]
        if stock.empty:
            # 尝试模糊匹配
            stock = df[df["代码"].str.contains(symbol)]

        if stock.empty:
            logger.warning(f"未找到股票 {symbol}")
            return None

        row = stock.iloc[0]
        return {
            "code": str(row.get("代码", "")),
            "name": str(row.get("名称", "")),
            "price": float(row.get("最新价", 0)),
            "change": float(row.get("涨跌额", 0)),
            "change_percent": float(row.get("涨跌幅", 0)),
            "volume": int(row.get("成交量", 0)),
            "amount": float(row.get("成交额", 0)),
            "turnover": float(row.get("换手率", 0)),
            "pe": float(row.get("市盈率-动态", 0) or 0),
            "pb": float(row.get("市净率", 0) or 0),
            "high_52w": float(row.get("52周最高", 0) or 0),
            "low_52w": float(row.get("52周最低", 0) or 0),
            "volume_ratio": float(row.get("量比", 0) or 0),
        }

    def get_index_spot(self) -> pd.DataFrame:
        """
        获取大盘指数实时行情
        返回: 上证指数、深证成指、创业板、科创50 等
        """
        logger.info("正在获取大盘指数行情...")
        try:
            df = ak.stock_zh_index_spot_em()
            return df
        except Exception as e:
            logger.error(f"获取指数行情失败: {e}")
            return pd.DataFrame()

    def format_for_db(self, df: pd.DataFrame) -> List[dict]:
        """
        将行情数据格式化为数据库写入格式
        """
        records = []
        for _, row in df.iterrows():
            try:
                record = {
                    "symbol": str(row.get("代码", "")),
                    "name": str(row.get("名称", "")),
                    "price": float(row.get("最新价", 0) or 0),
                    "change": float(row.get("涨跌额", 0) or 0),
                    "change_percent": float(row.get("涨跌幅", 0) or 0),
                    "volume": int(row.get("成交量", 0) or 0),
                    "amount": float(row.get("成交额", 0) or 0),
                    "turnover": float(row.get("换手率", 0) or 0),
                    "pe": float(row.get("市盈率-动态", 0) or 0),
                    "pb": float(row.get("市净率", 0) or 0),
                    "high_52w": float(row.get("52周最高", 0) or 0),
                    "low_52w": float(row.get("52周最低", 0) or 0),
                    "volume_ratio": float(row.get("量比", 0) or 0),
                    "updated_at": datetime.now(),
                }
                records.append(record)
            except Exception as e:
                logger.warning(f"格式化股票 {row.get('代码')} 失败: {e}")
                continue
        return records


if __name__ == "__main__":
    collector = StockCollector()

    # 测试获取所有股票
    print("=== 测试获取所有 A 股行情 ===")
    df = collector.get_all_stocks_spot()
    if not df.empty:
        print(f"共获取 {len(df)} 只股票")
        print("列名:", df.columns.tolist())
        print(df.head(3))

    # 测试获取指数
    print("\n=== 测试获取大盘指数 ===")
    index_df = collector.get_index_spot()
    if not index_df.empty:
        print(f"共获取 {len(index_df)} 个指数")
        print(index_df.head())
