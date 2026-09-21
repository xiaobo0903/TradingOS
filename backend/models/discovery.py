import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import relationship

from models.database import Base


class DiscoveryType(str, enum.Enum):
    """股票发现类型"""
    STRONG = "strong"           # 强势股
    VOLUME_SURGE = "volume_surge"  # 放量股
    BREAKOUT = "breakout"       # 突破股
    PULLBACK = "pullback"       # 回调股
    CAPITAL_FLOW = "capital_flow"  # 资金异动
    SENTIMENT = "sentiment"     # 人气股
    LEADER = "leader"           # 龙头候选
    ABNORMAL = "abnormal"       # 异常股
    NEW_HIGH = "new_high"       # 新高
    NEW_LOW = "new_low"         # 新低
    LIMIT_UP = "limit_up"       # 涨停相关
    LARGE_ORDER = "large_order"  # 大单异常


class StockDiscovery(Base):
    """股票发现记录"""
    __tablename__ = "stock_discovery"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False, index=True)
    discovery_type = Column(String(50), nullable=False, index=True)  # DiscoveryType
    score = Column(Numeric(10, 2))  # 发现评分 0-100
    reason = Column(Text)  # 发现原因

    # 分析数据快照（JSON格式存储当时的指标数据）
    data_snapshot = Column(Text)

    # 发现时间
    trade_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    stock = relationship("Stock", back_populates="discoveries")

    def __repr__(self):
        return f"<StockDiscovery {self.stock_id} {self.discovery_type}>"
