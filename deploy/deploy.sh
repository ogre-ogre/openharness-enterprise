#!/bin/bash
# OpenHarness Enterprise 部署脚本
# 用法: ./deploy.sh

set -e

echo "=========================================="
echo "  OpenHarness Enterprise 部署脚本"
echo "=========================================="

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "[INFO] Python 版本: $PYTHON_VERSION"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "[INFO] 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "[INFO] 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 创建必要的目录
echo "[INFO] 创建目录结构..."
mkdir -p ~/.oh-enterprise/users
mkdir -p ~/.oh-enterprise/shared/skills
mkdir -p ~/.oh-enterprise/logs
mkdir -p ~/.oh-enterprise/uploads

# 检查环境变量
if [ -z "$ANTHROPIC_AUTH_TOKEN" ]; then
    echo "[WARN] ANTHROPIC_AUTH_TOKEN 未设置，请在 .env 文件中配置"
fi

# 初始化数据库
echo "[INFO] 初始化数据库..."
python -c "from openharness.enterprise.storage.database import get_database; get_database()"

echo ""
echo "=========================================="
echo "  部署完成!"
echo "=========================================="
echo ""
echo "启动服务: ./start.sh"
echo "停止服务: ./stop.sh"
echo ""