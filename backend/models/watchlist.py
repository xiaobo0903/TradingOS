import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from models.database import Base


class WatchlistStatus(str, enum.Enum):
    """股票关注状态"""
    CANDIDATE = "candidate"      # 候选
    OBSERVING = "observing"       # 观察中
    KEY_OBSERVING = "key_observing"  # 重点观察
    HOLDING = "holding"          # 持仓
    CONTINUE_HOLD = "continue_hold"  # 继续持有
    RISK_OBSERVING = "risk_observing"  # 风险观察
    ELIMINATED = "eliminated"    # 淘汰


class WatchlistGroup(Base):
    """关注分组"""
    __tablename__ = "watchlist_group"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    type = Column(String(20))  # system, user
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<WatchlistGroup {self.name}>"


class StockWatchlist(Base):
    """股票关注"""
    __tablename__ = "stock_watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("watchlist_group.id"), nullable=False, index=True)
    status = Column(String(20), default=WatchlistStatus.OBSERVING.value)

    # 优先级和备注
    priority = Column(Integer, default=0)  # 0-100
    note = Column(Text)  # 备注信息
    reason = Column(Text)  # 加入原因

    # 状态变化记录
    status_change_reason = Column(Text)
    last_status_change = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stock = relationship("Stock", back_populates="watchlists")
    group = relationship("WatchlistGroup")

    __table_args__ = (
        # 确保同一只股票在同一个分组中只有一个记录
    )

    def __repr__(self):
        return f"<StockWatchlist {self.stock_id} {self.status}>"
