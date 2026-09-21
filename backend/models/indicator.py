from datetime import date
from sqlalchemy import Column, Integer, Date, Numeric, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from models.database import Base


class StockIndicator(Base):
    __tablename__ = "stock_indicator"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)

    # MA - 移动平均线
    ma5 = Column(Numeric(10, 3))
    ma10 = Column(Numeric(10, 3))
    ma20 = Column(Numeric(10, 3))
    ma30 = Column(Numeric(10, 3))
    ma60 = Column(Numeric(10, 3))
    ma120 = Column(Numeric(10, 3))
    ma250 = Column(Numeric(10, 3))

    # EMA - 指数移动平均
    ema12 = Column(Numeric(10, 3))
    ema26 = Column(Numeric(10, 3))

    # MACD
    dif = Column(Numeric(10, 5))
    dea = Column(Numeric(10, 5))
    macd = Column(Numeric(10, 5))  # MACD柱 = 2 * (DIF - DEA)

    # RSI
    rsi6 = Column(Numeric(10, 4))
    rsi12 = Column(Numeric(10, 4))
    rsi24 = Column(Numeric(10, 4))

    # BOLL - 布林带
    boll_mb = Column(Numeric(10, 3))  # 中轨
    boll_ub = Column(Numeric(10, 3))  # 上轨
    boll_lb = Column(Numeric(10, 3))  # 下轨
    boll_width = Column(Numeric(10, 6))  # 带宽

    # KDJ
    kdj_k = Column(Numeric(10, 4))
    kdj_d = Column(Numeric(10, 4))
    kdj_j = Column(Numeric(10, 4))

    stock = relationship("Stock", back_populates="indicators")

    __table_args__ = (
        UniqueConstraint('stock_id', 'trade_date', name='uq_indicator_date'),
        Index('idx_indicator_stock_date', 'stock_id', 'trade_date'),
    )

    def __repr__(self):
        return f"<StockIndicator {self.stock_id} {self.trade_date}>"
