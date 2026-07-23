# TradingOS 数据库架构 - 固定方案

## 修订历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-23 | v1.0 | 初始版本，使用 pgvector |
| 2026-07-23 | v2.0 | 因服务器 CPU 不支持 AVX2，改为 ChromaDB |

## 最终架构

```
┌─────────────────────────────────────────────────────────────┐
│                    TradingOS 数据库层                        │
├─────────────────┬─────────────────┬───────────────────────┤
│   PostgreSQL    │      Redis      │      ChromaDB        │
│  +TimescaleDB  │                 │     (向量存储)        │
├─────────────────┼─────────────────┼───────────────────────┤
│    5432 端口     │    6379 端口    │      8800 端口       │
├─────────────────┴─────────────────┴───────────────────────┤
│                                                          │
│  PostgreSQL (5432)                                      │
│  ├── base.*         - 基础数据 (股票信息、分类、配置)     │
│  ├── market.*       - 行情数据 (日K、分钟K、Tick)        │
│  ├── indicator.*     - 技术指标 (MACD、RSI、BOLL等)      │
│  ├── fund.*          - 资金数据 (资金流向、北向资金)       │
│  ├── ai.*            - AI分析数据                         │
│  └── user_schema.*   - 用户系统                          │
│                                                          │
│  TimescaleDB 扩展 → stock_daily_k (时序优化)            │
│                                                          │
│  Redis (6379)                                           │
│  ├── stock:code:quote  - 实时行情缓存                   │
│  ├── market:hot         - 热点股票列表                    │
│  └── session:*          - 会话/任务队列                   │
│                                                          │
│  ChromaDB (8800)                                        │
│  └── stock_knowledge   - RAG 知识库向量存储              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 服务选型

| 服务 | 镜像 | 用途 | CPU要求 |
|------|------|------|---------|
| PostgreSQL | `timescale/timescaledb:latest-pg16` | 主业务数据、时序优化 | 无 |
| Redis | `redis:7-alpine` | 实时缓存 | 无 |
| ChromaDB | `chromadb/chroma:latest` | 向量存储(RAG) | **无 AVX2 要求** |

## 为什么用 ChromaDB 替代 pgvector？

| 对比项 | pgvector | ChromaDB |
|--------|-----------|----------|
| AVX2 要求 | **必须** | 不需要 |
| 部署方式 | PostgreSQL 扩展 | 独立服务 |
| CPU 兼容性 | 需要 AVX2 | 通用 |
| API | SQL | REST API |
| 适用场景 | 与 PG 紧密集成 | 独立向量服务 |

**pgvector 需要 AVX2 指令集，但 Intel Celeron N5105 不支持，因此选用 ChromaDB。**

## 数据持久化

```
TradingOS/
├── data/
│   ├── postgres/    → PostgreSQL 数据
│   ├── redis/      → Redis 数据
│   └── chroma/     → ChromaDB 数据
└── startup.sh      → 启动脚本
```

## 启动脚本

```bash
cd /Volumes/odisk/TradingOS
chmod +x startup.sh
./startup.sh
```

## 初始化步骤

### 1. 启动服务
```bash
./startup.sh
```

### 2. 启用 TimescaleDB
```bash
docker exec -it tradingos-postgres psql -U tradingos -d tradingos
```
```sql
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
\dx
```

### 3. 导入建表脚本
```bash
docker exec -i tradingos-postgres psql -U tradingos -d tradingos < backend/database/init.sql
```

### 4. 验证 ChromaDB
```bash
curl http://192.168.31.132:8800/api/v1/heartbeat
```

## 连接信息

| 服务 | 地址 | 端口 | 用户 | 密码 |
|------|------|------|------|------|
| PostgreSQL | 192.168.31.132 | 5432 | tradingos | tradingos_password |
| Redis | 192.168.31.132 | 6379 | - | - |
| ChromaDB | 192.168.31.132 | 8800 | - | - |

## 后端配置

```python
# PostgreSQL
DATABASE_URL = "postgresql://tradingos:tradingos_password@192.168.31.132:5432/tradingos"

# Redis
REDIS_HOST = "192.168.31.132"
REDIS_PORT = 6379

# ChromaDB (RAG)
CHROMA_HOST = "192.168.31.132"
CHROMA_PORT = 8800
```

## RAG 服务使用

```python
from backend.services.rag_service import rag_service, init_default_knowledge

# 初始化知识库
init_default_knowledge()

# 搜索相关知识
results = rag_service.search("MACD金叉是什么意思")
for doc in results["documents"][0]:
    print(doc)
```

## 注意事项

1. **数据持久化**：所有数据存储在 `data/` 目录下
2. **备份**：定期备份 `data/` 目录
3. **ChromaDB**：作为独立向量数据库，不依赖 PostgreSQL
