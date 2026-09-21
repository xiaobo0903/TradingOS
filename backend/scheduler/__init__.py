"""
TradingOS 定时任务调度器
简化为只采集Tushare实时行情数据
每个工作日下午15:30执行
"""
import threading
import time as time_module

import schedule

from utils.logging import app_logger

_scheduler_thread = None
_stop_event = None


def collect_realtime_task():
    """采集实时行情任务"""
    app_logger.info("定时任务：开始采集Tushare实时行情数据", category="SCHEDULER")
    try:
        from collectors.realtime_collector import TushareRealtimeCollector
        collector = TushareRealtimeCollector()
        data = collector.collect()
        saved = collector.save_realtime_data(data)
        app_logger.info(f"定时任务：采集完成，获取 {len(data)} 条，保存 {saved} 条", category="SCHEDULER")
        return f"成功采集 {len(data)} 条，保存 {saved} 条"
    except Exception as e:
        app_logger.error(f"定时任务：采集失败 - {e}", category="SCHEDULER")
        return f"采集失败: {e}"


def run_scheduler():
    """运行调度器"""
    global _stop_event

    app_logger.info("调度器启动，每工作日15:30采集实时行情", category="SCHEDULER")

    # 设置每个工作日下午15:30执行
    schedule.every().monday.at("15:30").do(collect_realtime_task)
    schedule.every().tuesday.at("15:30").do(collect_realtime_task)
    schedule.every().wednesday.at("15:30").do(collect_realtime_task)
    schedule.every().thursday.at("15:30").do(collect_realtime_task)
    schedule.every().friday.at("15:30").do(collect_realtime_task)

    while _stop_event is None or not _stop_event.is_set():
        schedule.run_pending()
        time_module.sleep(60)  # 每分钟检查一次

    app_logger.info("调度器已停止", category="SCHEDULER")


def start_scheduler():
    """启动调度器线程"""
    global _scheduler_thread, _stop_event

    if _scheduler_thread and _scheduler_thread.is_alive():
        app_logger.info("调度器已在运行", category="SCHEDULER")
        return "调度器已在运行"

    _stop_event = threading.Event()
    _scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    _scheduler_thread.start()
    app_logger.info("调度器线程已启动", category="SCHEDULER")
    return "调度器已启动"


def stop_scheduler():
    """停止调度器"""
    global _stop_event

    if _stop_event:
        _stop_event.set()
    app_logger.info("调度器停止指令已发送", category="SCHEDULER")
    return "调度器已停止"


def get_scheduler_status():
    """获取调度器状态"""
    global _scheduler_thread

    if _scheduler_thread and _scheduler_thread.is_alive():
        return {"status": "running"}
    return {"status": "stopped"}
