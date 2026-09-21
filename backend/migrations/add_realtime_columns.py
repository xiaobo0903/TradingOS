"""
数据库迁移：为 stock_realtime 表添加新字段

执行方式：
    python migrations/add_realtime_columns.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import engine, Base
from models.capital import StockRealtime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """执行迁移"""
    from sqlalchemy import text

    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'stock_realtime'
        """))
        existing_columns = [row[0] for row in result]

        new_columns = [
            ('main_inflow', 'NUMERIC(20, 2)'),
            ('weibi', 'NUMERIC(10, 4)'),
            ('buy_price', 'NUMERIC(10, 2)'),
            ('sell_price', 'NUMERIC(10, 2)'),
        ]

        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                conn.execute(text(f"""
                    ALTER TABLE stock_realtime
                    ADD COLUMN {col_name} {col_type}
                """))
                conn.commit()
                logger.info(f"Added column: {col_name}")
            else:
                logger.info(f"Column already exists: {col_name}")

        logger.info("Migration completed")


if __name__ == '__main__':
    migrate()
