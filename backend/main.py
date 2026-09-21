"""
TradingOS FastAPI 应用入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from models.database import init_db
from utils.logging import app_logger

from api import data_center


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    app_logger.info("TradingOS 启动中...", category="SYSTEM")
    init_db()
    app_logger.info("数据库初始化完成", category="SYSTEM")

    # 启动定时任务调度器
    from scheduler import start_scheduler
    start_scheduler()

    yield

    # 关闭时停止调度器
    from scheduler import stop_scheduler
    stop_scheduler()

    app_logger.info("TradingOS 关闭", category="SYSTEM")


# 创建 FastAPI 应用
app = FastAPI(
    title="TradingOS",
    description="A 股智能分析系统 API",
    version=settings.VERSION,
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(data_center.router)


@app.get("/")
def root():
    return {
        "name": "TradingOS",
        "version": settings.VERSION,
        "description": "A 股智能分析系统"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
