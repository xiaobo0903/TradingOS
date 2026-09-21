import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey

from models.database import Base


class AIAnalysisType(str, enum.Enum):
    """AI分析类型"""
    STOCK = "stock"           # 个股分析
    SECTOR = "sector"         # 板块分析
    MARKET = "market"         # 市场分析
    COMPREHENSIVE = "comprehensive"  # 综合报告


class RiskLevel(str, enum.Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class AIAnalysis(Base):
    """AI分析结果"""
    __tablename__ = "ai_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), index=True)
    sector_id = Column(Integer, ForeignKey("sector.id"), index=True)

    analysis_type = Column(String(50), nullable=False, index=True)  # AIAnalysisType
    period = Column(String(20))  # short, medium, long

    # 输入快照
    input_snapshot = Column(Text)  # JSON格式存储分析输入数据

    # 分析结果
    result = Column(Text)  # AI生成的自然语言分析结果
    trend_score = Column(String(10))  # 趋势评分 ★★★★☆
    volume_score = Column(String(10))  # 量能评分
    capital_score = Column(String(10))  # 资金评分
    sector_score = Column(String(10))  # 板块评分

    # 风险等级
    risk_level = Column(String(20), default=RiskLevel.MEDIUM.value)

    # 主要优势和风险
    strengths = Column(Text)  # JSON格式
    risks = Column(Text)  # JSON格式
    observations = Column(Text)  # 需要观察的点

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AIAnalysis {self.stock_id} {self.analysis_type}>"
