from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class KnowledgeItem(BaseModel):
    id: int
    title: str
    category: str
    summary: str
    content: str


class QARequest(BaseModel):
    question: str


@router.get("/categories")
async def get_categories():
    return [
        {"name": "股票基础", "count": 15, "children": ["股票基本概念", "PE和PB", "市值与流通", "交易规则"]},
        {"name": "技术分析", "count": 25, "children": ["K线基础", "均线系统", "MACD指标", "RSI指标", "BOLL指标", "KDJ指标"]},
        {"name": "K线形态", "count": 12, "children": ["底部形态", "顶部形态", "持续形态"]},
        {"name": "主力行为", "count": 8, "children": ["吸筹特征", "洗盘识别", "出货信号"]},
        {"name": "交易心理", "count": 10, "children": ["恐惧与贪婪", "止损原则", "仓位管理"]}
    ]


@router.get("/list")
async def get_knowledge_list(category: Optional[str] = None):
    knowledge_items = [
        {
            "id": 1,
            "title": "MACD指标详解",
            "category": "技术分析",
            "summary": "MACD是技术分析中最常用的指标之一，本文详细介绍MACD的计算方法和实战应用。",
            "content": "<p>MACD指标是 Moving Average Convergence Divergence 的缩写...</p>"
        },
        {
            "id": 2,
            "title": "RSI指标详解",
            "category": "技术分析",
            "summary": "RSI是衡量股价变动速度和幅度的指标，本文介绍RSI的使用技巧。",
            "content": "<p>RSI (Relative Strength Index) 相对强弱指数...</p>"
        },
        {
            "id": 3,
            "title": "早晨之星形态",
            "category": "K线形态",
            "summary": "早晨之星是重要的底部反转形态，本文详细讲解其特征和识别方法。",
            "content": "<p>早晨之星是由三根K线组成的底部反转形态...</p>"
        }
    ]
    if category:
        knowledge_items = [k for k in knowledge_items if k["category"] == category]
    return knowledge_items


@router.get("/{id}")
async def get_knowledge_detail(id: int):
    return {
        "id": id,
        "title": "MACD指标详解",
        "category": "技术分析",
        "content": """
            <h3>一、MACD简介</h3>
            <p>MACD是技术分析中最常用的指标之一，由Gerald Appel发明。</p>

            <h3>二、计算方法</h3>
            <p>1. 计算短期EMA（通常为12日）<br>
            2. 计算长期EMA（通常为26日）<br>
            3. DIF = EMA12 - EMA26<br>
            4. DEA = DIF的9日EMA<br>
            5. MACD柱 = 2 × (DIF - DEA)</p>

            <h3>三、应用规则</h3>
            <p>1. 金叉：DIF上穿DEA，买入信号<br>
            2. 死叉：DIF下穿DEA，卖出信号<br>
            3. 零轴：DIF和DEA在零轴上方为多头市场</p>
        """
    }


@router.post("/qa")
async def ask_question(request: QARequest):
    return {
        "question": request.question,
        "answer": f"关于您的问题「{request.question}」，根据MACD指标的理论，MACD金叉通常被视为买入信号。但需要结合成交量、市场环境等因素综合判断。",
        "related": [
            {"id": 1, "title": "MACD指标详解"},
            {"id": 2, "title": "RSI指标详解"}
        ]
    }
