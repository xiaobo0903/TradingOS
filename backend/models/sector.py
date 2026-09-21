import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

from models.database import Base


class SectorType(str, enum.Enum):
    INDUSTRY = "industry"  # 行业板块
    CONCEPT = "concept"   # 概念板块
    REGION = "region"     # 地域板块


# 关联表
stock_sector = Table(
    'stock_sector',
    Base.metadata,
    Column('stock_id', Integer, ForeignKey('stock.id'), primary_key=True),
    Column('sector_id', Integer, ForeignKey('sector.id'), primary_key=True)
)


class Sector(Base):
    """板块"""
    __tablename__ = "sector"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    type = Column(String(20))  # industry, concept, region
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stocks = relationship("Stock", secondary=stock_sector, back_populates="sectors")

    def __repr__(self):
        return f"<Sector {self.code} {self.name}>"


class SectorDaily(Base):
    """板块每日行情"""
    __tablename__ = "sector_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sector_id = Column(Integer, ForeignKey("sector.id"), nullable=False, index=True)
    trade_date = Column(DateTime, nullable=False, index=True)

    # 涨跌幅、成交额等
    change_pct = Column(String(20))
    turnover_rate = Column(String(20))
    leading_stocks = Column(String(500))  # 龙头股列表(JSON)

    sector = relationship("Sector")

    def __repr__(self):
        return f"<SectorDaily {self.sector_id} {self.trade_date}>"


class SectorStockDaily(Base):
    """板块内个股每日行情

    用于存储从外部导入的板块内股票数据（如华泰App导出的数据）
    """
    __tablename__ = "sector_stock_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sector_id = Column(Integer, ForeignKey("sector.id"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=True, index=True)  # 可为空（如果股票不在库中）
    trade_date = Column(DateTime, nullable=False, index=True)

    # 股票信息
    stock_code = Column(String(10), nullable=False, index=True)  # 股票代码（字符串，保留前导零）
    stock_name = Column(String(50))  # 股票名称（供参考）

    # 行情数据
    close = Column(String(20))  # 收盘价
    change_pct = Column(String(20))  # 涨跌幅
    volume = Column(String(20))  # 成交量
    turnover_rate = Column(String(20))  # 换手率
    amount = Column(String(20))  # 成交额
    open = Column(String(20))  # 开盘价
    high = Column(String(20))  # 最高价
    low = Column(String(20))  # 最低价

    # 扩展字段（JSON格式存储其他字段）
    extra_data = Column(String(2000))  # 其他数据(JSON)

    sector = relationship("Sector")
    stock = relationship("Stock")

    def __repr__(self):
        return f"<SectorStockDaily {self.sector_id} {self.stock_code} {self.trade_date}>"
