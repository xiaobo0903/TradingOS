"""
Tushare实时行情数据采集器

每日15:30从Tushare提取个股实时行情数据
包含：量比、换手率、股本、市值等字段
"""
from typing import List, Dict
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed

import tushare as ts
import pandas as pd

from collectors.base import BaseCollector
from models.database import get_db_context
from models.stock import Stock
from models.capital import StockRealtime
from utils.logging import app_logger


class TushareRealtimeCollector(BaseCollector):
    """
    Tushare实时行情采集器

    数据来源：Tushare Pro
    接口：pro.daily + pro.daily_basic
    采集时间：每日15:30（收盘后）

    字段说明：
    - pre_close: 昨收价
    - open/high/low/close: 今日行情
    - volume/amount: 成交量/成交额
    - turnover_rate: 换手率(%)
    - volume_ratio: 量比
    - total_share/float_share: 总股本/流通股本（万股）
    - total_market_cap/float_market_cap: 总市值/流通市值（元）
    - pe/pb: 市盈率/市净率
    """

    name = "tushare_realtime_collector"
    TUSHARE_TOKEN = '2dd290408413995cd8d95d15145173a1e1aac6bcec65e5c57c830088'

    def __init__(self):
        self.pro = ts.pro_api(self.TUSHARE_TOKEN)

    def collect(self, trade_date: str = None, **kwargs) -> List[Dict]:
        """
        采集实时行情数据

        Args:
            trade_date: 交易日期 YYYYMMDD，默认今日

        Returns:
            实时行情数据列表
        """
        if not trade_date:
            trade_date = datetime.now().strftime('%Y%m%d')

        app_logger.info(f"开始采集Tushare实时行情: {trade_date}", category="COLLECTOR")

        # 获取全市场股票
        with get_db_context() as db:
            stocks = db.query(Stock).filter(Stock.status == 'active').all()
            stock_list = [(s.id, s.code, s.market) for s in stocks]

        app_logger.info(f"需要采集 {len(stock_list)} 只股票", category="COLLECTOR")

        all_data = []
        batch_size = 100  # Tushare每次最多100只

        for i in range(0, len(stock_list), batch_size):
            batch = stock_list[i:i + batch_size]
            ts_codes = [f"{code}.{'SH' if market == 'SH' else 'SZ'}" for _, code, market in batch]

            try:
                # 获取日线数据（支持批量）
                df_daily = self.pro.daily(
                    ts_code=','.join(ts_codes),
                    trade_date=trade_date
                )

                # daily_basic 不支持批量查询，使用线程池并行查询
                def fetch_basic_data(ts_code):
                    try:
                        df = self.pro.daily_basic(ts_code=ts_code, trade_date=trade_date)
                        if df is not None and len(df) > 0:
                            return ts_code, df.iloc[0]
                    except Exception:
                        pass
                    return ts_code, None

                basic_data_map = {}
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = {executor.submit(fetch_basic_data, code): code for code in ts_codes}
                    for future in as_completed(futures):
                        ts_code, row = future.result()
                        if row is not None:
                            basic_data_map[ts_code] = row

                if df_daily is not None and len(df_daily) > 0:
                    for _, row in df_daily.iterrows():
                        ts_code = row['ts_code']
                        basic_row = basic_data_map.get(ts_code)

                        # 提取基本面数据
                        turnover_rate = None
                        volume_ratio = None
                        total_share = None
                        float_share = None
                        total_market_cap = None
                        float_market_cap = None
                        pe = None
                        pb = None

                        if basic_row is not None:
                            # turnover_rate_f 是更精确的换手率
                            turnover_rate = basic_row.get('turnover_rate_f') or basic_row.get('turnover_rate')
                            volume_ratio = basic_row.get('volume_ratio')
                            total_share = basic_row.get('total_share')
                            float_share = basic_row.get('float_share')
                            # total_mv 和 circ_mv 单位是万元，转换为元 (乘以 10000)
                            if basic_row.get('total_mv'):
                                total_market_cap = float(basic_row['total_mv']) * 10000
                            if basic_row.get('circ_mv'):
                                float_market_cap = float(basic_row['circ_mv']) * 10000
                            pe = basic_row.get('pe')
                            pb = basic_row.get('pb')

                        data = {
                            'stock_code': ts_code.split('.')[0],
                            'trade_date': trade_date,
                            'pre_close': row['pre_close'],
                            'open': row['open'],
                            'high': row['high'],
                            'low': row['low'],
                            'close': row['close'],
                            'change': row['change'],
                            'pct_chg': row['pct_chg'],
                            'amplitude': self._calc_amplitude(row['high'], row['low'], row['pre_close']),
                            'volume': row['vol'],
                            'amount': float(row['amount']) * 1000 if row['amount'] else 0,  # Tushare返回千元，转元
                            'turnover_rate': turnover_rate,
                            'volume_ratio': volume_ratio,
                            'total_share': total_share,
                            'float_share': float_share,
                            'total_market_cap': total_market_cap,
                            'float_market_cap': float_market_cap,
                            'pe': pe,
                            'pb': pb,
                        }
                        all_data.append(data)

                batch_num = i // batch_size + 1
                app_logger.info(f"批次 {batch_num} 完成，当前共 {len(all_data)} 条", category="COLLECTOR")

            except Exception as e:
                app_logger.error(f"批次 {i // batch_size + 1} 失败: {e}", category="COLLECTOR")
                continue

        app_logger.info(f"实时行情采集完成，共 {len(all_data)} 条", category="COLLECTOR")
        self.update_collect_time()
        return all_data

    def _calc_amplitude(self, high, low, pre_close) -> float:
        """计算振幅"""
        if high and low and pre_close and pre_close > 0:
            return round((high - low) / pre_close * 100, 4)
        return 0

    def save_realtime_data(self, data_list: List[Dict]) -> int:
        """
        保存实时行情数据到数据库

        Args:
            data_list: 实时行情数据列表

        Returns:
            保存的记录数
        """
        saved = 0

        with get_db_context() as db:
            for data in data_list:
                stock_code = data['stock_code']

                # 获取股票ID
                stock = db.query(Stock).filter(Stock.code == stock_code).first()
                if not stock:
                    app_logger.debug(f"股票 {stock_code} 不存在，跳过")
                    continue

                trade_date = datetime.strptime(data['trade_date'], '%Y%m%d').date()

                # 检查是否已存在
                existing = db.query(StockRealtime).filter(
                    StockRealtime.stock_id == stock.id,
                    StockRealtime.trade_date == trade_date
                ).first()

                def to_numeric(val):
                    if val is None or (isinstance(val, float) and pd.isna(val)):
                        return None
                    return float(val)

                def update_if_present(obj, key, value):
                    """仅当新值不为None时才更新"""
                    v = to_numeric(value)
                    if v is not None:
                        setattr(obj, key, v)

                if existing:
                    # 更新（仅当新值不为None时才更新，保护已有数据）
                    update_if_present(existing, 'pre_close', data.get('pre_close'))
                    update_if_present(existing, 'open', data.get('open'))
                    update_if_present(existing, 'high', data.get('high'))
                    update_if_present(existing, 'low', data.get('low'))
                    update_if_present(existing, 'close', data.get('close'))
                    update_if_present(existing, 'change', data.get('change'))
                    update_if_present(existing, 'pct_chg', data.get('pct_chg'))
                    update_if_present(existing, 'amplitude', data.get('amplitude'))
                    update_if_present(existing, 'volume', data.get('volume'))
                    update_if_present(existing, 'amount', data.get('amount'))
                    update_if_present(existing, 'turnover_rate', data.get('turnover_rate'))
                    update_if_present(existing, 'volume_ratio', data.get('volume_ratio'))
                    update_if_present(existing, 'total_share', data.get('total_share'))
                    update_if_present(existing, 'float_share', data.get('float_share'))
                    update_if_present(existing, 'total_market_cap', data.get('total_market_cap'))
                    update_if_present(existing, 'float_market_cap', data.get('float_market_cap'))
                    update_if_present(existing, 'pe', data.get('pe'))
                    update_if_present(existing, 'pb', data.get('pb'))
                else:
                    realtime = StockRealtime(
                        stock_id=stock.id,
                        trade_date=trade_date,
                        pre_close=to_numeric(data.get('pre_close')),
                        open=to_numeric(data.get('open')),
                        high=to_numeric(data.get('high')),
                        low=to_numeric(data.get('low')),
                        close=to_numeric(data.get('close')),
                        change=to_numeric(data.get('change')),
                        pct_chg=to_numeric(data.get('pct_chg')),
                        amplitude=to_numeric(data.get('amplitude')),
                        volume=to_numeric(data.get('volume')),
                        amount=to_numeric(data.get('amount')),
                        turnover_rate=to_numeric(data.get('turnover_rate')),
                        volume_ratio=to_numeric(data.get('volume_ratio')),
                        total_share=to_numeric(data.get('total_share')),
                        float_share=to_numeric(data.get('float_share')),
                        total_market_cap=to_numeric(data.get('total_market_cap')),
                        float_market_cap=to_numeric(data.get('float_market_cap')),
                        pe=to_numeric(data.get('pe')),
                        pb=to_numeric(data.get('pb')),
                    )
                    db.add(realtime)

                saved += 1

            db.commit()

        return saved
