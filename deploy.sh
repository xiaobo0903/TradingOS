#!/bin/bash
# TradingOS 自动部署脚本 - 在远程服务器上构建

set -e

# 配置
REMOTE_HOST="192.168.31.132"
REMOTE_USER="xiaobo"
REMOTE_PATH="/home/xiaobo/tradingos"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查必要工具
check_tools() {
    log_info "检查必要工具..."
    for tool in ssh scp rsync; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool 未安装"
            exit 1
        fi
    done
    log_info "工具检查完成"
}

# 部署到远程
deploy_remote() {
    log_info "部署到 $REMOTE_HOST..."

    # 创建远程目录
    ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_PATH/backend $REMOTE_PATH/frontend $REMOTE_PATH/deploy/images"

    # 复制 docker-compose.yml
    log_info "复制 docker-compose.yml..."
    scp docker-compose.yml $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

    # 复制后端文件
    log_info "复制后端文件..."
    rsync -avz --exclude='venv' --exclude='__pycache__' --exclude='*.pyc' --exclude='.git' \
        ./backend/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/backend/

    # 复制前端文件
    log_info "复制前端文件..."
    rsync -avz --exclude='node_modules' --exclude='.git' \
        ./frontend/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/frontend/

    # 在远程服务器上构建并启动
    log_info "在远程服务器上构建镜像..."
    ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_PATH && docker-compose up -d --build"

    log_info "部署完成!"
    log_info "访问地址: http://$REMOTE_HOST"
}

# 重启服务
restart_remote() {
    log_info "重启远程服务..."
    ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_PATH && docker-compose restart"
    log_info "重启完成"
}

# 停止服务
stop_remote() {
    log_info "停止远程服务..."
    ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_PATH && docker-compose down"
    log_info "停止完成"
}

# 查看日志
logs_remote() {
    ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_PATH && docker-compose logs -f"
}

# 帮助
show_help() {
    echo "TradingOS 部署脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  deploy   部署到远程服务器"
    echo "  restart  重启远程服务"
    echo "  stop     停止远程服务"
    echo "  logs     查看远程日志"
}

case "${1:-help}" in
    deploy)  check_tools; deploy_remote ;;
    restart) restart_remote ;;
    stop)    stop_remote ;;
    logs)    logs_remote ;;
    help|--help|-h) show_help ;;
    *) log_error "未知命令: $1"; show_help; exit 1 ;;
esac
