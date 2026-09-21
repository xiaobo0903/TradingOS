"""
AKShare 数据源实现
"""
from typing import List, Dict, Optional
import pandas as pd
import akshare as ak

from providers.base import BaseProvider


class AKShareProvider(BaseProvider):
    """AKShare 数据源实现"""

    name = "akshare"

    def get_stock_list(self) -> List[Dict]:
        """获取A股列表"""
        try:
            df = ak.stock_zh_a_spot_em()
            # 重命名为标准字段
            df = df.rename(columns={
                '代码': 'code',
                '名称': 'name',
                '最新价': 'price',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '最高': 'high',
                '最低': 'low',
                '今开': 'open',
                '昨收': 'pre_close',
                '量比': 'volume_ratio',
                '换手率': 'turnover_rate',
                '市盈率-动态': 'pe',
                '市净率': 'pb',
                '总市值': 'total_market_cap',
                '流通市值': 'float_market_cap',
                '成交额': 'amount',
                '换手率': 'turnover_rate',
            })
            # 添加市场标识
            df['market'] = df['code'].apply(lambda x: 'SH' if x.startswith('6') else 'SZ')
            return df.to_dict('records')
        except Exception as e:
            print(f"Error getting stock list: {e}")
            return []

    def get_realtime_price(self, stock_code: str = None) -> List[Dict]:
        """获取实时行情"""
        try:
            df = ak.stock_zh_a_spot_em()
            if stock_code:
                df = df[df['代码'] == stock_code]
            return df.to_dict('records')
        except Exception as e:
            print(f"Error getting realtime price: {e}")
            return []

    def get_daily(self, stock_code: str, start_date: str, end_date: str, adjust: str = "qfq") -> List[Dict]:
        """
        获取日线数据

        Args:
            stock_code: 股票代码，如 "000001"
            start_date: 开始日期，如 "20230101"
            end_date: 结束日期，如 "20231231"
            adjust: 复权类型，"qfq"前复权，"hfq"后复权，"None"不复权
        """
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            # 重命名列
            df = df.rename(columns={
                '日期': 'trade_date',
                '股票代码': 'code',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change',
                '换手率': 'turnover_rate',
            })
            return df.to_dict('records')
        except Exception as e:
            print(f"Error getting daily data for {stock_code}: {e}")
            return []

    def get_minute(self, stock_code: str, period: str = "1") -> List[Dict]:
        """
        获取分钟数据

        Args:
            stock_code: 股票代码，如 "000001"
            period: 周期，"1"=1分钟，"5"=5分钟，"15"=15分钟，"30"=30分钟，"60"=60分钟
        """
        try:
            # AKShare 的分钟数据接口
            symbol = f"sh{stock_code}" if stock_code.startswith('6') else f"sz{stock_code}"
            df = ak.stock_zh_a_minute(
                symbol=symbol,
                period=period,
                adjust="qfq"
            )
            return df.to_dict('records')
        except Exception as e:
            print(f"Error getting minute data for {stock_code}: {e}")
            return []

    def get_capital_flow(self, stock_code: str) -> Dict:
        """获取资金流向"""
        try:
            df = ak.stock_individual_fund_flow(stock_code=stock_code, market="all")
            return df.to_dict('records') if not df.empty else {}
        except Exception as e:
            print(f"Error getting capital flow for {stock_code}: {e}")
            return {}

    def get_sector_list(self) -> List[Dict]:
        """获取板块列表（行业板块）"""
        try:
            df = ak.stock_board_industry_name_em()
            return df.to_dict('records')
        except Exception as e:
            print(f"Error getting sector list: {e}")
            return []

    def get_sector_stocks(self, sector_name: str) -> List[Dict]:
        """获取板块成分股"""
        try:
            df = ak.stock_board_industry_cons_em(symbol=sector_name)
            return df.to_dict('records')
        except Exception as e:
            print(f"Error getting sector stocks for {sector_name}: {e}")
            return []

    def get_index_stocks(self, index_code: str = "000001") -> List[Dict]:
        """获取指数成分股"""
        try:
            df = ak.stock_index_weight_cons(symbol=index_code)
            return df.to_dict('records')
        except Exception as e:
            print(f"Error getting index stocks for {index_code}: {e}")
            return []

    def get_market_index(self) -> List[Dict]:
        """获取主要指数行情"""
        try:
            df = ak.stock_zh_index_spot_em()
            return df.to_dict('records')
        except Exception as e:
            print(f"Error getting market index: {e}")
            return []
