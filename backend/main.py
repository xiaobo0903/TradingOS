from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import market, stock, indicator, capital, ai, knowledge

app = FastAPI(
    title="TradingOS API",
    description="TradingOS 智能股票分析系统 API",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(market.router, prefix="/api/market", tags=["市场数据"])
app.include_router(stock.router, prefix="/api/stock", tags=["股票数据"])
app.include_router(indicator.router, prefix="/api/indicator", tags=["技术指标"])
app.include_router(capital.router, prefix="/api/capital", tags=["资金数据"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI分析"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])


@app.get("/")
async def root():
    return {"message": "TradingOS API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
