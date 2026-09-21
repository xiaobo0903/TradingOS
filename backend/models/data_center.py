import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey

from models.database import Base


class DataTaskStatus(str, enum.Enum):
    """采集任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class DataTask(Base):
    """数据采集任务"""
    __tablename__ = "data_task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type = Column(String(50), nullable=False, index=True)  # stock_list, daily, minute, capital
    source = Column(String(50))  # 数据源: akshare, tushare
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(20), default=DataTaskStatus.PENDING.value)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)
    records_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DataTask {self.task_type} {self.status}>"


class DataQualityStatus(str, enum.Enum):
    """数据质量状态"""
    NORMAL = "normal"
    MISSING = "missing"
    ABNORMAL = "abnormal"
    DUPLICATE = "duplicate"
    HANDLED = "handled"


class DataQuality(Base):
    """数据质量记录"""
    __tablename__ = "data_quality"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), index=True)
    data_type = Column(String(50), nullable=False, index=True)  # daily, minute, capital
    data_time = Column(DateTime, nullable=False, index=True)

    status = Column(String(20), default=DataQualityStatus.NORMAL.value)
    reason = Column(Text)  # 异常原因
    handled = Column(String(20), default="false")  # 是否已处理
    handler = Column(String(100))  # 处理人
    handle_time = Column(DateTime)
    handle_result = Column(Text)  # 处理结果

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DataQuality {self.stock_id} {self.data_type} {self.status}>"
