from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Numeric, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from models.database import Base


class StockCapital(Base):
    """资金流向数据"""
    __tablename__ = "stock_capital"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False, index=True)
    trade_time = Column(DateTime, nullable=False, index=True)

    # 主力资金
    main_inflow = Column(Numeric(20, 2))  # 主力净流入（元）
    main_inflow_pct = Column(Numeric(10, 4))  # 主力净流入占比(%)

    # 超大单
    super_large_inflow = Column(Numeric(20, 2))  # 超大单净流入（元）
    super_large_inflow_pct = Column(Numeric(10, 4))

    # 大单
    large_inflow = Column(Numeric(20, 2))  # 大单净流入（元）
    large_inflow_pct = Column(Numeric(10, 4))

    # 中单
    medium_inflow = Column(Numeric(20, 2))  # 中单净流入（元）
    medium_inflow_pct = Column(Numeric(10, 4))

    # 小单
    small_inflow = Column(Numeric(20, 2))  # 小单净流入（元）
    small_inflow_pct = Column(Numeric(10, 4))

    # Relationship
    stock = relationship("Stock", back_populates="capitals")

    __table_args__ = (
        Index('idx_capital_stock_time', 'stock_id', 'trade_time'),
    )

    def __repr__(self):
        return f"<StockCapital {self.stock_id} {self.trade_time}>"


class StockRealtime(Base):
    """个股实时行情数据

    每日15:30从Tushare提取，包含量比、换手率、股本、市值等字段
    """
    __tablename__ = "stock_realtime"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False, index=True)
    trade_date = Column(DateTime, nullable=False, index=True)

    # 行情数据
    pre_close = Column(Numeric(10, 2))  # 昨收
    open = Column(Numeric(10, 2))  # 今开
    high = Column(Numeric(10, 2))  # 今最高
    low = Column(Numeric(10, 2))  # 今最低
    close = Column(Numeric(10, 2))  # 收盘价
    change = Column(Numeric(10, 2))  # 涨跌
    pct_chg = Column(Numeric(10, 4))  # 涨跌幅(%)
    amplitude = Column(Numeric(10, 4))  # 振幅(%)

    # 交易数据
    volume = Column(Numeric(20, 2))  # 成交量（手）
    amount = Column(Numeric(20, 2))  # 成交额（元）

    # 流动性指标
    turnover_rate = Column(Numeric(10, 4))  # 换手率(%)
    volume_ratio = Column(Numeric(10, 4))  # 量比

    # 股本数据
    total_share = Column(Numeric(20, 2))  # 总股本（万股）
    float_share = Column(Numeric(20, 2))  # 流通股本（万股）

    # 市值数据
    total_market_cap = Column(Numeric(20, 2))  # 总市值（元）
    float_market_cap = Column(Numeric(20, 2))  # 流通市值（元）

    # 估值指标
    pe = Column(Numeric(10, 2))  # 市盈率
    pb = Column(Numeric(10, 2))  # 市净率

    # 资金流数据
    main_inflow = Column(Numeric(20, 2))  # 主力净流入（元）
    weibi = Column(Numeric(10, 4))  # 委比(%)
    buy_price = Column(Numeric(10, 2))  # 买一价
    sell_price = Column(Numeric(10, 2))  # 卖一价

    # Relationship
    stock = relationship("Stock", back_populates="realtime_data")

    __table_args__ = (
        Index('idx_realtime_stock_date', 'stock_id', 'trade_date'),
    )

    def __repr__(self):
        return f"<StockRealtime {self.stock_id} {self.trade_date}>"
