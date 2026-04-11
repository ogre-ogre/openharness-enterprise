#!/bin/bash
# OpenHarness Enterprise 一键打包脚本
# 在开发机上运行，生成部署包

set -e

VERSION="1.0.0"
PACKAGE_NAME="oh-enterprise-${VERSION}"
DIST_DIR="dist"

echo "=========================================="
echo "  OpenHarness Enterprise 打包脚本"
echo "=========================================="
echo ""

# 清理
echo "[1/6] 清理旧文件..."
rm -rf $DIST_DIR
mkdir -p $DIST_DIR/$PACKAGE_NAME

# 复制 Python 代码
echo "[2/6] 复制后端代码..."
cp -r src/openharness $DIST_DIR/$PACKAGE_NAME/
cp pyproject.toml $DIST_DIR/$PACKAGE_NAME/ 2>/dev/null || true
cp setup.py $DIST_DIR/$PACKAGE_NAME/ 2>/dev/null || true

# 复制部署脚本
echo "[3/6] 复制部署脚本..."
cp deploy/requirements.txt $DIST_DIR/$PACKAGE_NAME/
cp deploy/.env.example $DIST_DIR/$PACKAGE_NAME/
cp deploy/deploy.sh $DIST_DIR/$PACKAGE_NAME/
cp deploy/start.sh $DIST_DIR/$PACKAGE_NAME/
cp deploy/stop.sh $DIST_DIR/$PACKAGE_NAME/
cp deploy/oh-enterprise.service $DIST_DIR/$PACKAGE_NAME/

# 构建前端
echo "[4/6] 构建前端..."
cd web
npm install
npm run build
cd ..

# 复制前端构建产物
echo "[5/6] 复制前端文件..."
mkdir -p $DIST_DIR/$PACKAGE_NAME/web
cp -r web/dist/* $DIST_DIR/$PACKAGE_NAME/web/

# 创建 README
echo "[6/6] 创建部署说明..."
cat > $DIST_DIR/$PACKAGE_NAME/README.md << 'EOF'
# OpenHarness Enterprise 部署指南

## 系统要求

- Linux (CentOS 7+ / Ubuntu 18.04+)
- Python 3.10+
- Node.js 18+ (仅开发模式需要，生产环境不需要)

## 快速部署

### 1. 上传部署包

```bash
# 解压
tar -xzf oh-enterprise-1.0.0.tar.gz
cd oh-enterprise-1.0.0
```

### 2. 配置环境变量

```bash
# 复制配置文件
cp .env.example .env

# 编辑配置
vim .env
```

**必须配置的项：**
- `ANTHROPIC_AUTH_TOKEN`: LLM API Key
- `ANTHROPIC_BASE_URL`: LLM API 地址 (百炼用户填写)
- `ANTHROPIC_MODEL`: 模型名称

### 3. 部署

```bash
chmod +x deploy.sh start.sh stop.sh
./deploy.sh
```

### 4. 启动服务

```bash
./start.sh
```

### 5. 访问

- 前端地址: http://服务器IP:8000/web/
- API 文档: http://服务器IP:8000/docs
- 管理后台: http://服务器IP:8000/admin

**默认账号**: admin / admin123

## 生产环境部署 (systemd)

```bash
# 复制服务文件
sudo cp oh-enterprise.service /etc/systemd/system/

# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start oh-enterprise

# 开机自启
sudo systemctl enable oh-enterprise

# 查看状态
sudo systemctl status oh-enterprise
```

## 目录结构

```
~/.oh-enterprise/
├── data.db              # 数据库
├── users/               # 用户数据
│   └── {user_id}/
│       ├── skills/      # 个人技能
│       ├── uploads/     # 上传文件
│       └── memory/      # 记忆文件
├── shared/              # 共享资源
│   └── skills/          # 共享技能
└── logs/                # 日志文件
```

## 常用命令

```bash
# 启动
./start.sh

# 停止
./stop.sh

# 查看日志
tail -f ~/.oh-enterprise/logs/server.log

# 查看服务状态
curl http://localhost:8000/health
```

## 故障排查

### 服务无法启动

1. 检查端口是否被占用: `netstat -tlnp | grep 8000`
2. 检查日志: `cat ~/.oh-enterprise/logs/server.log`
3. 检查 Python 版本: `python3 --version`

### 无法访问

1. 检查防火墙: `sudo firewall-cmd --list-ports`
2. 开放端口: `sudo firewall-cmd --add-port=8000/tcp --permanent`
3. 重载防火墙: `sudo firewall-cmd --reload`

## 更新

```bash
# 停止服务
./stop.sh

# 备份数据
cp -r ~/.oh-enterprise ~/.oh-enterprise.bak

# 解压新版本
tar -xzf oh-enterprise-new.tar.gz

# 部署
./deploy.sh

# 启动
./start.sh
```
EOF

# 设置权限
chmod +x $DIST_DIR/$PACKAGE_NAME/deploy.sh
chmod +x $DIST_DIR/$PACKAGE_NAME/start.sh
chmod +x $DIST_DIR/$PACKAGE_NAME/stop.sh

# 打包
echo ""
echo "[INFO] 创建压缩包..."
cd $DIST_DIR
tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_NAME}
cd ..

echo ""
echo "=========================================="
echo "  打包完成!"
echo "=========================================="
echo ""
echo "部署包: $DIST_DIR/${PACKAGE_NAME}.tar.gz"
echo "大小: $(du -h $DIST_DIR/${PACKAGE_NAME}.tar.gz | cut -f1)"
echo ""
echo "部署步骤:"
echo "1. 上传 ${PACKAGE_NAME}.tar.gz 到服务器"
echo "2. 解压: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "3. 进入目录: cd ${PACKAGE_NAME}"
echo "4. 配置: cp .env.example .env && vim .env"
echo "5. 部署: ./deploy.sh"
echo "6. 启动: ./start.sh"
echo ""