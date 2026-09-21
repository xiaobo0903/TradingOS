"""
资金流数据采集器

从腾讯财经获取个股资金流数据
资金流字段：主力净流入、超大单净流入、大单净流入等
"""
from typing import List, Dict, Optional
from datetime import datetime, date

import requests

from collectors.base import BaseCollector
from models.database import get_db_context
from models.stock import Stock
from models.capital import StockCapital
from utils.logging import app_logger


class CapitalFlowCollector(BaseCollector):
    """
    资金流数据采集器

    数据来源：腾讯财经
    接口：qt.gtimg.cn

    字段说明（腾讯财经单只股票数据 ~ 分隔）：
    [41] f62: 主力净流入（万元）
    [42] f184: 主力净流入占比(%)
    [43] f66: 超大单净流入（万元）
    [44] f185: 超大单净流入占比(%)
    [45] f69: 大单净流入（万元）
    [46] f186: 大单净流入占比(%)
    [47] f70: 中单净流入（万元）
    [48] f187: 中单净流入占比(%)
    [49] f71: 小单净流入（万元）
    [50] f188: 小单净流入占比(%)
    """

    name = "capital_flow_collector"

    def collect(self, stock_codes: List[str] = None, **kwargs) -> List[Dict]:
        """
        采集资金流数据

        Args:
            stock_codes: 股票代码列表，如 ['sh600000', 'sz000001']
                        如果为None，则采集全市场

        Returns:
            资金流数据列表
        """
        if not stock_codes:
            # 获取全市场股票代码
            stock_codes = self._get_all_stock_codes()

        if not stock_codes:
            return []

        # 批量获取（每批50只）
        all_data = []
        batch_size = 50

        for i in range(0, len(stock_codes), batch_size):
            batch = stock_codes[i:i + batch_size]
            codes_param = ','.join(batch)

            try:
                data = self._fetch_batch_capital(codes_param)
                all_data.extend(data)
                app_logger.info(f"资金流采集批次 {i//batch_size + 1} 完成，获取 {len(data)} 条", category="COLLECTOR")
            except Exception as e:
                app_logger.error(f"批量获取资金流失败: {e}", category="COLLECTOR")

        self.update_collect_time()
        return all_data

    def _get_all_stock_codes(self) -> List[str]:
        """获取全市场股票代码"""
        with get_db_context() as db:
            stocks = db.query(Stock).filter(Stock.status == 'active').all()
            codes = []
            for s in stocks:
                prefix = 'sh' if s.market == 'SH' else 'sz'
                codes.append(f"{prefix}{s.code}")
            return codes

    def _fetch_batch_capital(self, codes_param: str) -> List[Dict]:
        """
        批量获取资金流数据

        Args:
            codes_param: 逗号分隔的股票代码，如 'sh600000,sz000001'

        Returns:
            资金流数据列表
        """
        session = requests.Session()
        session.trust_env = False

        url = f'https://qt.gtimg.cn/q={codes_param}'
        resp = session.get(url, timeout=15)
        lines = resp.text.strip().split('\n')

        results = []
        for line in lines:
            if not line.strip() or '=' not in line:
                continue

            # 格式: v_sh600000="1~浦发银行~600000~..."
            # 需要先提取引号内的内容
            try:
                quote_start = line.index('="')
                quote_end = line.rindex('"')
                content = line[quote_start + 2:quote_end]
                parts = content.split('~')
            except (ValueError, IndexError):
                continue

            if len(parts) < 50:
                continue

            try:
                # 解析股票代码
                code_raw = parts[2]  # 股票代码在 parts[2]
                market = 'SH' if code_raw.startswith('6') else 'SZ'

                # 解析资金流数据（单位：万元）
                # 根据腾讯财经当前格式（实际验证）：
                # [44] 超大单净流入(万元), [45] 大单净流入(万元)
                # [46] 主力净流入占比(%), [47] 中单净流入(万元)
                # [48] 小单净流入(万元), [49] 超大单净流入占比(%)
                # 主力净流入 = 超大单净流入 + 大单净流入
                super_inflow = float(parts[44]) if parts[44] else 0  # 超大单净流入
                large_inflow = float(parts[45]) if parts[45] else 0  # 大单净流入
                main_inflow = super_inflow + large_inflow  # 主力净流入 = 超大单 + 大单
                main_inflow_pct = float(parts[46]) if parts[46] else 0  # 主力净流入占比
                medium_inflow = float(parts[47]) if parts[47] else 0  # 中单净流入
                small_inflow = float(parts[48]) if parts[48] else 0  # 小单净流入
                super_inflow_pct = float(parts[49]) if parts[49] else 0  # 超大单净流入占比
                large_inflow_pct = 0  # 大单净流入占比（API未直接提供）
                medium_inflow_pct = 0  # 中单净流入占比（API未直接提供）
                small_inflow_pct = 0  # 小单净流入占比（API未直接提供）

                # 单位转换为元（万元 * 10000）
                results.append({
                    'stock_code': code_raw,
                    'market': market,
                    'trade_time': datetime.now(),
                    'main_inflow': main_inflow * 10000,
                    'main_inflow_pct': main_inflow_pct,
                    'super_large_inflow': super_inflow * 10000,
                    'super_large_inflow_pct': super_inflow_pct,
                    'large_inflow': large_inflow * 10000,
                    'large_inflow_pct': large_inflow_pct,
                    'medium_inflow': medium_inflow * 10000,
                    'medium_inflow_pct': medium_inflow_pct,
                    'small_inflow': small_inflow * 10000,
                    'small_inflow_pct': small_inflow_pct,
                })
            except (ValueError, TypeError, IndexError) as e:
                app_logger.warning(f"解析资金流数据失败: {e}", category="COLLECTOR")
                continue

        return results

    def save_capital_flow(self, capital_data: List[Dict]) -> int:
        """
        保存资金流数据到数据库

        Args:
            capital_data: 资金流数据列表

        Returns:
            保存的记录数
        """
        saved = 0
        with get_db_context() as db:
            for data in capital_data:
                code = data['stock_code']

                # 获取股票ID
                stock = db.query(Stock).filter(Stock.code == code).first()
                if not stock:
                    continue

                stock_id = stock.id
                trade_time = data.get('trade_time', datetime.now())

                # 检查是否已存在
                existing = db.query(StockCapital).filter(
                    StockCapital.stock_id == stock_id,
                    StockCapital.trade_time == trade_time
                ).first()

                if existing:
                    existing.main_inflow = data.get('main_inflow')
                    existing.main_inflow_pct = data.get('main_inflow_pct')
                    existing.super_large_inflow = data.get('super_large_inflow')
                    existing.large_inflow = data.get('large_inflow')
                    existing.medium_inflow = data.get('medium_inflow')
                    existing.small_inflow = data.get('small_inflow')
                else:
                    capital = StockCapital(
                        stock_id=stock_id,
                        trade_time=trade_time,
                        main_inflow=data.get('main_inflow'),
                        main_inflow_pct=data.get('main_inflow_pct'),
                        super_large_inflow=data.get('super_large_inflow'),
                        large_inflow=data.get('large_inflow'),
                        medium_inflow=data.get('medium_inflow'),
                        small_inflow=data.get('small_inflow'),
                    )
                    db.add(capital)

                saved += 1

            db.commit()
        return saved

    def get_realtime_capital(self, stock_code: str) -> Optional[Dict]:
        """
        获取单只股票实时资金流

        Args:
            stock_code: 股票代码，如 '000001'

        Returns:
            资金流数据字典
        """
        # 获取市场
        with get_db_context() as db:
            stock = db.query(Stock).filter(Stock.code == stock_code).first()
            if not stock:
                return None
            prefix = 'sh' if stock.market == 'SH' else 'sz'
            full_code = f"{prefix}{stock_code}"

        data = self._fetch_batch_capital(full_code)
        return data[0] if data else None

    def get_capital_by_date(self, trade_date: date) -> List[Dict]:
        """
        获取指定日期的资金流数据

        Args:
            trade_date: 交易日期

        Returns:
            资金流数据列表
        """
        with get_db_context() as db:
            from datetime import datetime, time
            start_dt = datetime.combine(trade_date, time.min)
            end_dt = datetime.combine(trade_date, time.max)

            capitals = db.query(StockCapital).filter(
                StockCapital.trade_time >= start_dt,
                StockCapital.trade_time <= end_dt
            ).all()

            results = []
            for c in capitals:
                stock = db.query(Stock).filter(Stock.id == c.stock_id).first()
                if stock:
                    results.append({
                        'stock_code': stock.code,
                        'stock_name': stock.name,
                        'main_inflow': float(c.main_inflow) if c.main_inflow else 0,
                        'main_inflow_pct': float(c.main_inflow_pct) if c.main_inflow_pct else 0,
                        'super_large_inflow': float(c.super_large_inflow) if c.super_large_inflow else 0,
                        'large_inflow': float(c.large_inflow) if c.large_inflow else 0,
                        'medium_inflow': float(c.medium_inflow) if c.medium_inflow else 0,
                        'small_inflow': float(c.small_inflow) if c.small_inflow else 0,
                    })
            return results
