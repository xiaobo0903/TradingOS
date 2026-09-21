#!/usr/bin/env python3
"""
板块和资金流数据采集脚本

采集：
1. 新浪财经板块数据（175个概念/行业板块）
2. 腾讯财经资金流数据（个股主力/大单/中单/小单净流入）

用法：
    python3 backend/collect_sector_capital.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.sector_collector import SectorCollector
from collectors.capital_flow_collector import CapitalFlowCollector
from utils.logging import app_logger


def main():
    app_logger.info("=" * 50, category="SYSTEM")
    app_logger.info("开始执行板块和资金流数据采集", category="SYSTEM")

    # 1. 采集板块数据
    app_logger.info("正在采集板块数据...", category="COLLECTOR")
    try:
        sector_collector = SectorCollector()
        sectors = sector_collector.collect()
        app_logger.info(f"获取到 {len(sectors)} 个板块", category="COLLECTOR")

        # 保存板块数据
        saved = sector_collector.save_sectors(sectors)
        app_logger.info(f"保存 {saved} 个新板块到数据库", category="COLLECTOR")

        # 显示热点板块
        hot_sectors = sorted(sectors, key=lambda x: x['change_pct'], reverse=True)[:5]
        app_logger.info(f"今日涨幅前5板块: {', '.join([s['name'] for s in hot_sectors])}", category="COLLECTOR")

    except Exception as e:
        app_logger.error(f"采集板块数据失败: {e}", category="COLLECTOR")

    # 2. 采集资金流数据
    app_logger.info("正在采集资金流数据...", category="COLLECTOR")
    try:
        capital_collector = CapitalFlowCollector()

        # 获取所有股票代码
        from models.database import get_db_context
        from models.stock import Stock

        with get_db_context() as db:
            stocks = db.query(Stock).filter(Stock.status == 'active').all()
            stock_codes = []
            for s in stocks:
                prefix = 'sh' if s.market == 'SH' else 'sz'
                stock_codes.append(f"{prefix}{s.code}")

        app_logger.info(f"需要采集 {len(stock_codes)} 只股票的资金流数据", category="COLLECTOR")

        # 批量采集并保存
        saved_count = 0
        batch_size = 50
        for i in range(0, len(stock_codes), batch_size):
            batch = stock_codes[i:i + batch_size]
            try:
                data = capital_collector._fetch_batch_capital(','.join(batch))
                if data:
                    saved = capital_collector.save_capital_flow(data)
                    saved_count += saved
            except Exception as e:
                app_logger.error(f"批次 {i//batch_size + 1} 失败: {e}", category="COLLECTOR")
                continue

        app_logger.info(f"成功采集并保存 {saved_count} 条资金流数据", category="COLLECTOR")

    except Exception as e:
        app_logger.error(f"采集资金流数据失败: {e}", category="COLLECTOR")

    app_logger.info("板块和资金流数据采集完成", category="SYSTEM")


if __name__ == "__main__":
    main()
