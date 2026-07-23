"""
资金流数据采集模块
使用 AKShare 获取资金流向数据
"""

import akshare as ak
import pandas as pd
from typing import Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CapitalCollector:
    """资金流数据采集器"""

    def get_stock_money_flow(self, symbol: str) -> pd.DataFrame:
        """
        获取个股资金流数据

        Args:
            symbol: 股票代码，如 "600519"
        """
        logger.info(f"正在获取 {symbol} 资金流数据...")
        try:
            df = ak.stock_money_flow(symbol=symbol)
            logger.info(f"获取到 {len(df)} 条资金流数据")
            return df
        except Exception as e:
            logger.error(f"获取资金流失败: {e}")
            return pd.DataFrame()

    def get_market_money_flow(self) -> pd.DataFrame:
        """
        获取大盘资金流（行业板块资金流）
        """
        logger.info("正在获取大盘资金流数据...")
        try:
            df = ak.stock_money_flow_ind_em()
            logger.info(f"获取到 {len(df)} 条行业资金流数据")
            return df
        except Exception as e:
            logger.error(f"获取大盘资金流失败: {e}")
            return pd.DataFrame()

    def get_north_money(self) -> pd.DataFrame:
        """
        获取北向资金数据（沪股通+深股通）
        """
        logger.info("正在获取北向资金数据...")
        try:
            df = ak.stock_em_hsgt_north_net_flow_in(indicator="北向资金")
            logger.info(f"获取到 {len(df)} 条北向资金数据")
            return df
        except Exception as e:
            logger.error(f"获取北向资金失败: {e}")
            return pd.DataFrame()

    def get_north_hold_stock(self) -> pd.DataFrame:
        """
        获取北向资金持股明细
        """
        logger.info("正在获取北向资金持股明细...")
        try:
            df = ak.stock_em_hsgt_north_hold_stock()
            logger.info(f"获取到 {len(df)} 条持股明细")
            return df
        except Exception as e:
            logger.error(f"获取北向持股失败: {e}")
            return pd.DataFrame()

    def get_limit_up_list(self, date: str = None) -> pd.DataFrame:
        """
        获取涨停股票列表

        Args:
            date: 日期，格式 YYYYMMDD，None 表示今天
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        logger.info(f"正在获取 {date} 涨停股票列表...")
        try:
            df = ak.stock_em_zt_pool(date=date)
            logger.info(f"获取到 {len(df)} 只涨停股票")
            return df
        except Exception as e:
            logger.error(f"获取涨停列表失败: {e}")
            return pd.DataFrame()

    def get_limit_down_list(self, date: str = None) -> pd.DataFrame:
        """
        获取跌停股票列表
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        logger.info(f"正在获取 {date} 跌停股票列表...")
        try:
            df = ak.stock_em_zt_pool_subnormal(date=date, ignore_status=True)
            logger.info(f"获取到 {len(df)} 只跌停股票")
            return df
        except Exception as e:
            logger.error(f"获取跌停列表失败: {e}")
            return pd.DataFrame()

    def get_dragon_tiger(self, date: str = None) -> pd.DataFrame:
        """
        获取龙虎榜数据

        Args:
            date: 日期，格式 YYYYMMDD，None 表示最近一个交易日
        """
        logger.info(f"正在获取龙虎榜数据...")
        try:
            df = ak.stock_em_tiger_trade(date=date)
            logger.info(f"获取到 {len(df)} 条龙虎榜数据")
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜失败: {e}")
            return pd.DataFrame()

    def format_money_flow_for_db(self, df: pd.DataFrame, symbol: str) -> list:
        """
        将资金流数据格式化为数据库写入格式
        对应 fund.stock_money_flow 表
        """
        records = []
        if df.empty:
            return records

        for _, row in df.iterrows():
            try:
                record = {
                    "symbol": symbol,
                    "trade_date": row.get("日期"),
                    "main_inflow": float(row.get("主力净流入", 0) or 0),
                    "main_outflow": float(row.get("主力净流出", 0) or 0),
                    "super_large_in": float(row.get("超大单净流入", 0) or 0),
                    "super_large_out": float(row.get("超大单净流出", 0) or 0),
                    "large_in": float(row.get("大单净流入", 0) or 0),
                    "large_out": float(row.get("大单净流出", 0) or 0),
                    "medium_in": float(row.get("中单净流入", 0) or 0),
                    "medium_out": float(row.get("中单净流出", 0) or 0),
                    "small_in": float(row.get("小单净流入", 0) or 0),
                    "small_out": float(row.get("小单净流出", 0) or 0),
                }
                records.append(record)
            except Exception as e:
                logger.warning(f"格式化资金流数据失败: {e}")
                continue
        return records

    def format_north_money_for_db(self, df: pd.DataFrame) -> list:
        """
        将北向资金数据格式化为数据库写入格式
        对应 fund.north_money 表
        """
        records = []
        if df.empty:
            return records

        for _, row in df.iterrows():
            try:
                record = {
                    "trade_date": row.get("日期"),
                    "sh_connect": float(row.get("沪股通", 0) or 0),
                    "sz_connect": float(row.get("深股通", 0) or 0),
                    "total": float(row.get("北向资金", 0) or 0),
                }
                records.append(record)
            except Exception as e:
                logger.warning(f"格式化北向资金失败: {e}")
                continue
        return records


if __name__ == "__main__":
    collector = CapitalCollector()

    # 测试获取个股资金流
    print("=== 测试获取资金流 (贵州茅台 600519) ===")
    df = collector.get_stock_money_flow("600519")
    if not df.empty:
        print(f"获取 {len(df)} 条数据")
        print("列名:", df.columns.tolist())
        print(df.tail())

    # 测试北向资金
    print("\n=== 测试获取北向资金 ===")
    north_df = collector.get_north_money()
    if not north_df.empty:
        print(f"获取 {len(north_df)} 条数据")
        print(north_df.tail())

    # 测试涨停列表
    print("\n=== 测试获取涨停列表 ===")
    limit_df = collector.get_limit_up_list()
    if not limit_df.empty:
        print(f"获取 {len(limit_df)} 只涨停股票")
        print(limit_df.head())
