"""
板块数据采集器

从新浪财经获取行业/概念板块数据
"""
import re
import json
from typing import List, Dict, Optional
from datetime import datetime

import requests

from collectors.base import BaseCollector
from models.database import get_db_context
from models.stock import Stock
from models.sector import Sector
from utils.logging import app_logger


class SectorCollector(BaseCollector):
    """
    板块数据采集器

    数据来源：新浪财经
    接口：vip.stock.finance.sina.com.cn/q/view/newFLJK.php?param=class
    """

    name = "sector_collector"

    def collect(self, sector_type: str = None, **kwargs) -> List[Dict]:
        """
        采集板块数据

        Args:
            sector_type: 板块类型过滤 ('industry'/'concept'/'area')

        Returns:
            板块数据列表
        """
        session = requests.Session()
        session.trust_env = False

        url = 'https://vip.stock.finance.sina.com.cn/q/view/newFLJK.php?param=class'
        try:
            resp = session.get(
                url,
                timeout=15,
                headers={'Referer': 'https://finance.sina.com.cn/'}
            )
            text = resp.text.strip()
            match = re.search(r'= (\{.*\})', text, re.DOTALL)
            if not match:
                return []

            data = json.loads(match.group(1))

            sectors = []
            for code, info in data.items():
                parts = info.split(',')
                if len(parts) < 5:
                    continue

                # 解析板块数据
                # 格式: code,name,stock_count,avg_price,change_pct,...
                try:
                    change_pct = float(parts[4]) if parts[4] else 0
                except (ValueError, TypeError):
                    change_pct = 0

                sector_data = {
                    'code': code,
                    'name': parts[1] if len(parts) > 1 else code,
                    'stock_count': int(parts[2]) if parts[2].isdigit() else 0,
                    'avg_price': float(parts[3]) if parts[3] else 0,
                    'change_pct': change_pct,
                    'lead_stock_code': parts[8] if len(parts) > 8 else None,
                    'lead_stock_name': parts[12] if len(parts) > 12 else None,
                    'total_amount': float(parts[7]) if len(parts) > 7 and parts[7] else 0,
                    'type': self._guess_sector_type(code),
                }

                # 类型过滤
                if sector_type and sector_data['type'] != sector_type:
                    continue

                sectors.append(sector_data)

            # 按涨跌幅排序
            sectors.sort(key=lambda x: x['change_pct'], reverse=True)

            self.update_collect_time()
            return sectors

        except Exception as e:
            app_logger.error(f"获取新浪财经板块数据失败: {e}", category="COLLECTOR")
            return []

    def _guess_sector_type(self, code: str) -> str:
        """根据板块代码猜测类型"""
        if code.startswith('bk_') or code.startswith('gn_'):
            return 'concept'  # 概念
        elif code.startswith('hy_'):
            return 'industry'  # 行业
        elif code.startswith('dy_'):
            return 'area'  # 地域
        return 'concept'

    def save_sectors(self, sectors: List[Dict]) -> int:
        """
        保存板块数据到数据库

        Returns:
            保存的板块数量
        """
        saved = 0
        with get_db_context() as db:
            for s in sectors:
                code = s['code']
                existing = db.query(Sector).filter(Sector.code == code).first()

                if existing:
                    existing.name = s['name']
                    existing.type = s['type']
                else:
                    sector = Sector(
                        code=code,
                        name=s['name'],
                        type=s['type'],
                    )
                    db.add(sector)
                    saved += 1

            db.commit()
        return saved

    def get_sector_stocks(self, sector_code: str) -> List[str]:
        """
        获取板块成分股

        Args:
            sector_code: 板块代码

        Returns:
            股票代码列表
        """
        # 新浪财经板块详情接口（如果需要）
        # 这里简化处理，返回空列表
        return []


class StockSectorCollector(BaseCollector):
    """
    股票-板块关系采集器

    采集股票的板块归属关系
    """

    name = "stock_sector_collector"

    def collect(self, **kwargs) -> List[Dict]:
        """
        采集股票-板块关系

        Returns:
            股票-板块关系列表 [{stock_code, sector_code, sector_name}]
        """
        session = requests.Session()
        session.trust_env = False

        url = 'https://vip.stock.finance.sina.com.cn/q/view/newFLJK.php?param=class'
        try:
            resp = session.get(
                url,
                timeout=15,
                headers={'Referer': 'https://finance.sina.com.cn/'}
            )
            text = resp.text.strip()
            match = re.search(r'= (\{.*\})', text, re.DOTALL)
            if not match:
                return []

            data = json.loads(match.group(1))

            relations = []
            for sector_code, info in data.items():
                parts = info.split(',')
                if len(parts) < 9:
                    continue

                sector_name = parts[1] if len(parts) > 1 else sector_code
                lead_code = parts[8] if len(parts) > 8 else None

                if lead_code:
                    # 去掉市场前缀 (sz002886 -> 002886)
                    clean_code = lead_code.replace('sz', '').replace('sh', '')
                    relations.append({
                        'stock_code': clean_code,
                        'sector_code': sector_code,
                        'sector_name': sector_name,
                        'is_lead': True,
                    })

            return relations

        except Exception as e:
            app_logger.error(f"获取股票-板块关系失败: {e}", category="COLLECTOR")
            return []

    def save_stock_sector_relations(self, relations: List[Dict]) -> int:
        """
        保存股票-板块关系到数据库

        Returns:
            保存的关系数量
        """
        from models.sector import stock_sector as stock_sector_table

        saved = 0
        with get_db_context() as db:
            # 获取所有板块，建立code到id的映射
            sectors = db.query(Sector).all()
            sector_code_to_id = {s.code: s.id for s in sectors}

            # 获取所有股票，建立code到id的映射
            stocks = db.query(Stock).all()
            stock_code_to_id = {s.code: s.id for s in stocks}

            for rel in relations:
                stock_code = rel['stock_code']
                sector_code = rel['sector_code']

                if stock_code not in stock_code_to_id:
                    continue
                if sector_code not in sector_code_to_id:
                    continue

                stock_id = stock_code_to_id[stock_code]
                sector_id = sector_code_to_id[sector_code]

                # 检查是否已存在
                existing = db.execute(
                    stock_sector_table.select().where(
                        stock_sector_table.c.stock_id == stock_id,
                        stock_sector_table.c.sector_id == sector_id
                    )
                ).first()

                if not existing:
                    db.execute(
                        stock_sector_table.insert().values(
                            stock_id=stock_id,
                            sector_id=sector_id
                        )
                    )
                    saved += 1

            db.commit()
        return saved
