#!/bin/bash
# OpenHarness Enterprise 启动脚本
# 用法: ./start.sh [options]

set -e

# 默认配置
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
LOG_DIR="$HOME/.oh-enterprise/logs"
PID_FILE="$HOME/.oh-enterprise/server.pid"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 检查是否已运行
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "[ERROR] 服务已在运行 (PID: $PID)"
        echo "如需重启，请先运行: ./stop.sh"
        exit 1
    fi
fi

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 加载环境变量
if [ -f ".env" ]; then
    echo "[INFO] 加载 .env 配置..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# 设置默认值
export ANTHROPIC_AUTH_TOKEN=${ANTHROPIC_AUTH_TOKEN:-"sk-test"}
export ANTHROPIC_BASE_URL=${ANTHROPIC_BASE_URL:-"https://coding.dashscope.aliyuncs.com/apps/anthropic"}
export ANTHROPIC_MODEL=${ANTHROPIC_MODEL:-"glm-5"}

echo "=========================================="
echo "  OpenHarness Enterprise"
echo "=========================================="
echo ""
echo "[INFO] 启动服务..."
echo "[INFO] 地址: http://$HOST:$PORT"
echo "[INFO] 日志: $LOG_DIR/server.log"
echo ""

# 启动服务
nohup python -m openharness.enterprise.server --port $PORT --host $HOST > "$LOG_DIR/server.log" 2>&1 &
PID=$!

# 保存 PID
echo $PID > "$PID_FILE"

# 等待启动
sleep 2

# 检查是否成功
if ps -p $PID > /dev/null 2>&1; then
    echo "[OK] 服务已启动 (PID: $PID)"
    echo ""
    echo "访问地址: http://localhost:$PORT"
    echo "API 文档: http://localhost:$PORT/docs"
    echo "管理后台: http://localhost:$PORT/admin"
    echo ""
    echo "默认账号: admin / admin123"
    echo ""
    echo "查看日志: tail -f $LOG_DIR/server.log"
else
    echo "[ERROR] 服务启动失败"
    echo "查看日志: cat $LOG_DIR/server.log"
    exit 1
fi