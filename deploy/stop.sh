#!/bin/bash
# OpenHarness Enterprise 停止脚本

PID_FILE="$HOME/.oh-enterprise/server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "[INFO] 服务未运行"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p $PID > /dev/null 2>&1; then
    echo "[INFO] 停止服务 (PID: $PID)..."
    kill $PID
    sleep 2
    
    # 强制杀死
    if ps -p $PID > /dev/null 2>&1; then
        echo "[WARN] 强制停止..."
        kill -9 $PID
    fi
    
    rm -f "$PID_FILE"
    echo "[OK] 服务已停止"
else
    echo "[INFO] 服务未运行"
    rm -f "$PID_FILE"
fi