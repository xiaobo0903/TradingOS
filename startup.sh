#!/bin/bash
# ================================================
# TradingOS 数据库服务启动脚本
# 固定方案：PostgreSQL + Redis + ChromaDB
# ================================================

set -e

echo "================================================"
echo "  TradingOS 数据库服务启动"
echo "================================================"

# 目录设置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"

# 1. 创建数据目录
echo ""
echo "[1/5] 创建数据目录..."
mkdir -p "$DATA_DIR/postgres"
mkdir -p "$DATA_DIR/redis"
mkdir -p "$DATA_DIR/chroma"

# 设置权限 (PostgreSQL 用 999 用户)
echo "设置目录权限..."
sudo chown -R 999:999 "$DATA_DIR/postgres" 2>/dev/null || true
sudo chown -R 1000:1000 "$DATA_DIR/redis" 2>/dev/null || true
sudo chown -R 888:888 "$DATA_DIR/chroma" 2>/dev/null || true

# 2. 停止并删除旧容器
echo ""
echo "[2/5] 清理旧容器..."
docker rm -f tradingos-postgres 2>/dev/null || true
docker rm -f tradingos-redis 2>/dev/null || true
docker rm -f tradingos-chromadb 2>/dev/null || true

# 3. 启动 PostgreSQL
echo ""
echo "[3/5] 启动 PostgreSQL + TimescaleDB..."
docker run --name tradingos-postgres \
  -e POSTGRES_USER=tradingos \
  -e POSTGRES_PASSWORD=tradingos_password \
  -e POSTGRES_DB=tradingos \
  -p 0.0.0.0:5432:5432 \
  -v "$DATA_DIR/postgres:/var/lib/postgresql/data" \
  -d timescale/timescaledb:latest-pg16

# 4. 启动 Redis
echo ""
echo "[4/5] 启动 Redis..."
docker run --name tradingos-redis \
  -p 0.0.0.0:6379:6379 \
  -v "$DATA_DIR/redis:/data" \
  -d redis:7-alpine

# 5. 启动 ChromaDB
echo ""
echo "[5/5] 启动 ChromaDB (向量数据库)..."
docker run --name tradingos-chromadb \
  -p 0.0.0.0:8800:8000 \
  -v "$DATA_DIR/chroma:/chroma/chroma/.chroma_internal" \
  -d chromadb/chroma:latest

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 5

# 检查状态
echo ""
echo "================================================"
echo "  服务状态"
echo "================================================"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 验证 PostgreSQL
echo ""
echo "验证 PostgreSQL..."
if docker exec tradingos-postgres pg_isready -U tradingos > /dev/null 2>&1; then
    echo "  ✓ PostgreSQL 正常运行"
else
    echo "  ✗ PostgreSQL 未正常运行"
fi

# 验证 ChromaDB
echo ""
echo "验证 ChromaDB..."
if curl -s http://localhost:8800/api/v1/heartbeat > /dev/null 2>&1; then
    echo "  ✓ ChromaDB 正常运行"
else
    echo "  ✗ ChromaDB 未正常运行 (可能在远程服务器上)"
fi

echo ""
echo "================================================"
echo "  连接信息"
echo "================================================"
echo ""
echo "PostgreSQL:"
echo "  地址: 192.168.31.132"
echo "  端口: 5432"
echo "  用户: tradingos"
echo "  密码: tradingos_password"
echo "  数据库: tradingos"
echo ""
echo "Redis:"
echo "  地址: 192.168.31.132"
echo "  端口: 6379"
echo ""
echo "ChromaDB (向量数据库):"
echo "  地址: 192.168.31.132"
echo "  端口: 8800"
echo ""
echo "================================================"
echo "  下一步操作"
echo "================================================"
echo ""
echo "1. 启用 TimescaleDB 扩展:"
echo "   docker exec -it tradingos-postgres psql -U tradingos -d tradingos"
echo "   > CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"
echo "   > \\dx"
echo ""
echo "2. 导入建表脚本:"
echo "   docker exec -i tradingos-postgres psql -U tradingos -d tradingos < backend/database/init.sql"
echo ""
echo "3. 测试 ChromaDB:"
echo "   curl http://localhost:8800/api/v1/heartbeat"
echo ""
