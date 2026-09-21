"""
日志查询 API
"""
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Query

from utils.logging import LogQuery

router = APIRouter(prefix="/api/logs", tags=["日志"])


@router.get("/query")
def query_logs(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    level: Optional[str] = Query(None, description="日志级别 DEBUG/INFO/WARNING/ERROR"),
    category: Optional[str] = Query(None, description="分类 API/DATA/DISCOVERY/COLLECTOR/SYSTEM"),
    start_time: Optional[str] = Query(None, description="开始时间 YYYY-MM-DD HH:MM:SS"),
    end_time: Optional[str] = Query(None, description="结束时间 YYYY-MM-DD HH:MM:SS"),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """
    查询系统日志

    支持按关键词、级别、分类、时间范围过滤
    """
    start_dt = None
    end_dt = None

    if start_time:
        try:
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                start_dt = datetime.strptime(start_time, "%Y-%m-%d")
            except ValueError:
                pass

    if end_time:
        try:
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                end_dt = datetime.strptime(end_time, "%Y-%m-%d")
            except ValueError:
                pass

    result = LogQuery.query(
        keyword=keyword,
        level=level,
        category=category,
        start_time=start_dt,
        end_time=end_dt,
        limit=limit,
        offset=offset,
    )

    return result


@router.get("/levels")
def get_log_levels():
    """获取支持的日志级别"""
    return ["DEBUG", "INFO", "WARNING", "ERROR"]


@router.get("/categories")
def get_log_categories():
    """获取支持的日志分类"""
    return ["API", "DATA", "DISCOVERY", "COLLECTOR", "SYSTEM"]