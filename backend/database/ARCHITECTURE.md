# TradingOS 数据库架构

## 数据库选型

| 数据库 | 用途 | 端口 |
|--------|------|------|
| **PostgreSQL + TimescaleDB** | 主业务数据、时序行情数据 | 5432 |
| **Redis** | 实时缓存、热点数据、任务队列 | 6379 |
| **ChromaDB** | 向量存储（RAG知识库） | 8800 |

## 架构图

```
┌─────────────────────────────────────────────────┐
│              TradingOS 数据库层                   │
├─────────────┬──────────────┬────────────────────┤
│  PostgreSQL │    Redis     │     ChromaDB       │
│ +TimescaleDB│  (独立服务)  │    (向量存储)      │
│    5432    │    6379     │      8800         │
├─────────────┴──────────────┴────────────────────┤
│                                                │
│  PostgreSQL (5432)                             │
│  ├── base (基础数据)                           │
│  ├── market (行情数据)                         │
│  ├── indicator (技术指标)                       │
│  ├── fund (资金数据)                          │
│  ├── ai (AI分析数据)                          │
│  └── user_schema (用户系统)                    │
│                                                │
│  TimescaleDB 扩展 ──→ 日K、分钟K 时序优化      │
│                                                │
│  Redis (6379)                                  │
│  ├── 实时行情缓存                              │
│  ├── 热点股票列表                              │
│  └── 会话/任务队列                            │
│                                                │
│  ChromaDB (8800)                               │
│  └── RAG知识库向量存储                        │
│                                                │
└─────────────────────────────────────────────────┘
```

## 扩展说明

| 扩展 | 作用 | 启用命令 |
|------|------|----------|
| **TimescaleDB** | 时序数据优化（日K、分钟K查询加速） | `CREATE EXTENSION timescaledb;` |
| **pgvector** | ~~向量存储~~ (不推荐，见下方) | 不使用 |

### 为什么不用 pgvector？

pgvector 需要 CPU 支持 **AVX2 指令集**，部分低功耗 CPU（如 Intel Celeron N5105）不支持。

**替代方案**：使用 **ChromaDB** 作为独立的向量数据库。

## ChromaDB 配置

ChromaDB 提供 REST API，可通过后端服务调用：

```python
import chromadb
client = chromadb.HttpClient(host='192.168.31.132', port=8800)
collection = client.get_collection("stock_knowledge")
```

## 启动顺序

```bash
# 1. PostgreSQL + Redis + ChromaDB 一键启动
docker-compose up -d

# 2. 检查状态
docker ps

# 3. 初始化数据库
docker exec -it tradingos-postgres psql -U tradingos -d tradingos
# 执行: CREATE EXTENSION timescaledb;

# 4. 验证 ChromaDB
curl http://192.168.31.132:8800/api/v1/heartbeat
```

## 连接信息

| 服务 | 地址 | 端口 |
|------|------|------|
| PostgreSQL | 192.168.31.132 | 5432 |
| Redis | 192.168.31.132 | 6379 |
| ChromaDB | 192.168.31.132 | 8800 |

## 数据流向

```
行情数据 ──→ PostgreSQL ──→ TimescaleDB (时序优化) ──→ 后端API
              │
              └──→ Redis (实时缓存) ──→ 前端展示

RAG知识库 ──→ ChromaDB (向量存储) ──→ LLM推理 ──→ AI分析
```
