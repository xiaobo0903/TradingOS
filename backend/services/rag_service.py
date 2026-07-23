"""
TradingOS RAG 知识库服务
基于 ChromaDB 向量数据库
"""

import chromadb
from chromadb.config import Settings
from typing import List, Optional
import os

class RAGService:
    """RAG 知识库服务"""

    def __init__(self):
        self.chroma_host = os.getenv("CHROMA_HOST", "192.168.31.132")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8800"))

        self.client = chromadb.HttpClient(
            host=self.chroma_host,
            port=self.chroma_port
        )

        self.collection_name = "stock_knowledge"

    def get_or_create_collection(self):
        """获取或创建知识库集合"""
        return self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "股票知识库"}
        )

    def add_knowledge(self, texts: List[str], metadatas: List[dict], ids: List[str]):
        """
        添加知识到向量数据库

        Args:
            texts: 文本内容列表
            metadatas: 元数据列表 (如 {"category": "MACD", "source": "知识库"})
            ids: 唯一ID列表
        """
        collection = self.get_or_create_collection()
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )

    def search(self, query: str, n_results: int = 5) -> dict:
        """
        搜索知识

        Args:
            query: 查询文本
            n_results: 返回结果数量

        Returns:
            包含 documents, metadatas, distances 的字典
        """
        collection = self.get_or_create_collection()
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def delete_knowledge(self, ids: List[str]):
        """删除知识"""
        collection = self.get_or_create_collection()
        collection.delete(ids=ids)

    def get_collection_info(self) -> dict:
        """获取集合信息"""
        collection = self.get_or_create_collection()
        return {
            "name": collection.name,
            "count": collection.count(),
            "metadata": collection.metadata
        }


# 全局实例
rag_service = RAGService()


def init_default_knowledge():
    """初始化默认知识库"""
    default_knowledge = [
        {
            "id": "macd_001",
            "text": "MACD金叉：DIF上穿DEA形成金叉，通常被视为买入信号。当金叉发生在零轴上方时信号更强。",
            "metadata": {"category": "技术指标", "name": "MACD金叉"}
        },
        {
            "id": "macd_002",
            "text": "MACD死叉：DIF下穿DEA形成死叉，通常被视为卖出信号。当死叉发生在零轴下方时信号更强。",
            "metadata": {"category": "技术指标", "name": "MACD死叉"}
        },
        {
            "id": "rsi_001",
            "text": "RSI超买：RSI超过70表示市场处于超买状态，可能面临回调压力。",
            "metadata": {"category": "技术指标", "name": "RSI超买"}
        },
        {
            "id": "rsi_002",
            "text": "RSI超卖：RSI低于30表示市场处于超卖状态，可能存在反弹机会。",
            "metadata": {"category": "技术指标", "name": "RSI超卖"}
        },
        {
            "id": "boll_001",
            "text": "BOLL突破上轨：股价突破布林带上轨，表明强势特征，但可能存在短线回调风险。",
            "metadata": {"category": "技术指标", "name": "BOLL突破"}
        },
        {
            "id": "boll_002",
            "text": "BOLL跌破下轨：股价跌破布林带下轨，表明弱势，可能存在超跌反弹机会。",
            "metadata": {"category": "技术指标", "name": "BOLL跌破"}
        },
        {
            "id": "main_001",
            "text": "主力吸筹特征：低位成交量放大、换手率提升、价格稳定、大单频繁出现。",
            "metadata": {"category": "主力行为", "name": "吸筹特征"}
        },
        {
            "id": "main_002",
            "text": "主力洗盘特征：上涨后回调、成交量下降、关键位置未跌破。",
            "metadata": {"category": "主力行为", "name": "洗盘特征"}
        },
        {
            "id": "main_003",
            "text": "主力出货特征：高位放巨量、换手率异常、上涨乏力、资金持续流出。",
            "metadata": {"category": "主力行为", "name": "出货特征"}
        },
        {
            "id": "pattern_001",
            "text": "早晨之星：底部反转形态，由三根K线组成。第一根大阴线，第二根小实体星线，第三根大阳线。预示下跌趋势可能结束。",
            "metadata": {"category": "K线形态", "name": "早晨之星"}
        },
        {
            "id": "pattern_002",
            "text": "黄昏之星：顶部反转形态，与早晨之星相反。预示上涨趋势可能结束。",
            "metadata": {"category": "K线形态", "name": "黄昏之星"}
        }
    ]

    collection = rag_service.get_or_create_collection()

    # 检查是否已有数据
    if collection.count() == 0:
        texts = [k["text"] for k in default_knowledge]
        metadatas = [k["metadata"] for k in default_knowledge]
        ids = [k["id"] for k in default_knowledge]

        rag_service.add_knowledge(texts, metadatas, ids)
        print(f"已初始化 {len(default_knowledge)} 条知识")


if __name__ == "__main__":
    # 初始化知识库
    init_default_knowledge()

    # 测试搜索
    results = rag_service.search("MACD金叉是什么意思")
    print("\n搜索结果:")
    for i, doc in enumerate(results["documents"][0]):
        print(f"  {i+1}. {doc}")
        print(f"     距离: {results['distances'][0][i]:.4f}")
