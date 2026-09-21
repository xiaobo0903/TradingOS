"""
TradingOS 应用日志工具

提供结构化的应用日志记录，支持：
- 不同级别：DEBUG, INFO, WARNING, ERROR
- 分类标签：API, DATA, DISCOVERY, COLLECTOR, SYSTEM
- 日志文件持久化
- 日志查询接口
"""
import os
import logging
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from functools import wraps
import threading


# 日志目录
LOG_DIR = Path("/tmp/tradingos_logs")
LOG_DIR.mkdir(exist_ok=True)

# 当前日志文件
CURRENT_LOG_FILE = LOG_DIR / f"tradingos_{date.today().strftime('%Y%m%d')}.log"


class JsonFormatter(logging.Formatter):
    """JSON 格式化器"""
    def format(self, record):
        log_obj = {
            'timestamp': datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'category': getattr(record, 'category', 'SYSTEM'),
        }
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


class AppLogger:
    """
    应用日志记录器

    使用示例：
        from utils.logging import app_logger

        app_logger.info("这是一条信息日志", category="API")
        app_logger.error("这是一个错误", category="DISCOVERY")
        app_logger.warning("这是一个警告", category="COLLECTOR")
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 创建应用日志记录器
        self.logger = logging.getLogger('tradingos')
        self.logger.setLevel(logging.DEBUG)

        # 避免重复添加 handler
        if self.logger.handlers:
            self.logger.handlers.clear()

        # 文件 Handler（JSON 格式）
        file_handler = logging.FileHandler(CURRENT_LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JsonFormatter())

        # 控制台 Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        ))

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _log(self, level: int, message: str, category: str = "SYSTEM", **kwargs):
        """内部日志方法"""
        extra = {'category': category, **kwargs}
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, category: str = "SYSTEM", **kwargs):
        self._log(logging.DEBUG, message, category, **kwargs)

    def info(self, message: str, category: str = "SYSTEM", **kwargs):
        self._log(logging.INFO, message, category, **kwargs)

    def warning(self, message: str, category: str = "SYSTEM", **kwargs):
        self._log(logging.WARNING, message, category, **kwargs)

    def error(self, message: str, category: str = "SYSTEM", **kwargs):
        self._log(logging.ERROR, message, category, **kwargs)

    def exception(self, message: str, category: str = "SYSTEM", **kwargs):
        """记录异常信息"""
        self._log(logging.ERROR, message, category, exc_info=True, **kwargs)


# 全局实例
app_logger = AppLogger()


class LogQuery:
    """
    日志查询器

    用于查询历史日志
    """

    @staticmethod
    def get_log_files(days: int = 7) -> List[Path]:
        """获取最近N天的日志文件"""
        files = []
        today = date.today()
        for i in range(days):
            log_date = today - timedelta(days=i)
            log_file = LOG_DIR / f"tradingos_{log_date.strftime('%Y%m%d')}.log"
            if log_file.exists():
                files.append(log_file)
        return files

    @staticmethod
    def query(
        keyword: str = None,
        level: str = None,
        category: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict:
        """
        查询日志

        Args:
            keyword: 关键词搜索
            level: 日志级别（DEBUG/INFO/WARNING/ERROR）
            category: 分类（API/DATA/DISCOVERY/COLLECTOR/SYSTEM）
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            {'total': int, 'logs': List[Dict]}
        """
        all_logs = []
        log_files = LogQuery.get_log_files()

        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            log_obj = json.loads(line)
                            all_logs.append(log_obj)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                continue

        # 按时间倒序
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        # 过滤
        filtered_logs = []
        for log in all_logs:
            # 关键词过滤
            if keyword and keyword not in log.get('message', ''):
                continue

            # 级别过滤
            if level and log.get('level') != level.upper():
                continue

            # 分类过滤
            if category and log.get('category') != category.upper():
                continue

            # 时间过滤
            log_time = log.get('timestamp', '')
            if log_time:
                log_dt = datetime.strptime(log_time, '%Y-%m-%d %H:%M:%S')
                if start_time and log_dt < start_time:
                    continue
                if end_time and log_dt > end_time:
                    continue

            filtered_logs.append(log)

        # 分页
        total = len(filtered_logs)
        page_logs = filtered_logs[offset:offset + limit]

        return {
            'total': total,
            'logs': page_logs
        }


# 便捷的日志装饰器
def log_execution(category: str = "SYSTEM"):
    """记录函数执行的装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            func_name = func.__name__
            app_logger.info(f"开始执行 {func_name}", category=category)
            try:
                result = func(*args, **kwargs)
                elapsed = (datetime.now() - start_time).total_seconds()
                app_logger.info(f"{func_name} 执行成功，耗时 {elapsed:.2f}秒", category=category)
                return result
            except Exception as e:
                app_logger.exception(f"{func_name} 执行失败: {str(e)}", category=category)
                raise
        return wrapper
    return decorator


# 快捷日志函数
def log_api(message: str, **kwargs):
    """记录 API 相关日志"""
    app_logger.info(message, category="API", **kwargs)

def log_data(message: str, **kwargs):
    """记录数据相关日志"""
    app_logger.info(message, category="DATA", **kwargs)

def log_discovery(message: str, **kwargs):
    """记录发现相关日志"""
    app_logger.info(message, category="DISCOVERY", **kwargs)

def log_collector(message: str, **kwargs):
    """记录采集相关日志"""
    app_logger.info(message, category="COLLECTOR", **kwargs)

def log_error(message: str, **kwargs):
    """记录错误日志"""
    app_logger.error(message, category="ERROR", **kwargs)
