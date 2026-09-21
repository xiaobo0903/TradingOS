import enum
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, ForeignKey,
    Numeric, BigInteger, Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship

from models.database import Base


class StockStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELISTED = "delisted"


class Stock(Base):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(50), nullable=False)
    market = Column(String(10))  # SH, SZ
    industry = Column(String(50))
    sector = Column(String(50))  # 板块
    status = Column(SQLEnum(StockStatus), default=StockStatus.ACTIVE)
    list_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    daily_prices = relationship("StockDaily", back_populates="stock", cascade="all, delete-orphan")
    price_minutes = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    indicators = relationship("StockIndicator", back_populates="stock", cascade="all, delete-orphan")
    capitals = relationship("StockCapital", back_populates="stock", cascade="all, delete-orphan")
    watchlists = relationship("StockWatchlist", back_populates="stock")
    discoveries = relationship("StockDiscovery", back_populates="stock")
    sectors = relationship("Sector", secondary="stock_sector", back_populates="stocks")
    realtime_data = relationship("StockRealtime", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stock {self.code} {self.name}>"


class StockDaily(Base):
    __tablename__ = "stock_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(10, 3))
    high = Column(Numeric(10, 3))
    low = Column(Numeric(10, 3))
    close = Column(Numeric(10, 3))
    volume = Column(BigInteger)  # 成交量
    amount = Column(Numeric(20, 2))  # 成交额
    turnover_rate = Column(Numeric(10, 4))  # 换手率
    change_pct = Column(Numeric(10, 4))  # 涨跌幅
    amplitude = Column(Numeric(10, 4))  # 振幅

    stock = relationship("Stock", back_populates="daily_prices")

    __table_args__ = (
        UniqueConstraint('stock_id', 'trade_date', name='uq_stock_daily_date'),
        Index('idx_daily_stock_date', 'stock_id', 'trade_date'),
    )

    def __repr__(self):
        return f"<StockDaily {self.stock_id} {self.trade_date}>"


class StockPrice(Base):
    """Minute-level price data"""
    __tablename__ = "stock_price"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Numeric(10, 3))
    high = Column(Numeric(10, 3))
    low = Column(Numeric(10, 3))
    close = Column(Numeric(10, 3))
    volume = Column(BigInteger)
    amount = Column(Numeric(20, 2))

    stock = relationship("Stock", back_populates="price_minutes")

    __table_args__ = (
        Index('idx_price_stock_timestamp', 'stock_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<StockPrice {self.stock_id} {self.timestamp}>"
