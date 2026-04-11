# OpenHarness Enterprise Windows 打包脚本
# 在 Windows 上运行，生成 Linux 部署包

$VERSION = "1.0.0"
$PACKAGE_NAME = "oh-enterprise-$VERSION"
$PROJECT_DIR = "D:\openharness-enterprise"
$DIST_DIR = "$PROJECT_DIR\dist"
$PACKAGE_DIR = "$DIST_DIR\$PACKAGE_NAME"

Write-Host "=========================================="
Write-Host "  OpenHarness Enterprise 打包脚本"
Write-Host "=========================================="
Write-Host ""

# 清理
Write-Host "[1/6] 清理旧文件..."
if (Test-Path $DIST_DIR) {
    Remove-Item -Recurse -Force $DIST_DIR
}
New-Item -ItemType Directory -Path $PACKAGE_DIR | Out-Null

# 复制 Python 代码
Write-Host "[2/6] 复制后端代码..."
Copy-Item -Recurse -Path "$PROJECT_DIR\src\openharness" -Destination $PACKAGE_DIR

# 复制部署脚本
Write-Host "[3/6] 复制部署脚本..."
Copy-Item -Path "$PROJECT_DIR\deploy\requirements.txt" -Destination $PACKAGE_DIR
Copy-Item -Path "$PROJECT_DIR\deploy\.env.example" -Destination $PACKAGE_DIR
Copy-Item -Path "$PROJECT_DIR\deploy\deploy.sh" -Destination $PACKAGE_DIR
Copy-Item -Path "$PROJECT_DIR\deploy\start.sh" -Destination $PACKAGE_DIR
Copy-Item -Path "$PROJECT_DIR\deploy\stop.sh" -Destination $PACKAGE_DIR
Copy-Item -Path "$PROJECT_DIR\deploy\oh-enterprise.service" -Destination $PACKAGE_DIR

# 复制前端构建产物
Write-Host "[4/6] 复制前端文件..."
New-Item -ItemType Directory -Path "$PACKAGE_DIR\web" | Out-Null
Copy-Item -Recurse -Path "$PROJECT_DIR\web\dist\*" -Destination "$PACKAGE_DIR\web"

# 创建 README
Write-Host "[5/6] 创建部署说明..."
$readme = @"
# OpenHarness Enterprise 部署指南

## 系统要求

- Linux (CentOS 7+ / Ubuntu 18.04+)
- Python 3.10+

## 快速部署

### 1. 上传部署包

``````bash
# 解压
tar -xzf oh-enterprise-1.0.0.tar.gz
cd oh-enterprise-1.0.0
``````

### 2. 配置环境变量

``````bash
# 复制配置文件
cp .env.example .env

# 编辑配置
vim .env
``````

**必须配置的项：**
- ``ANTHROPIC_AUTH_TOKEN``: LLM API Key
- ``ANTHROPIC_BASE_URL``: LLM API 地址 (百炼用户填写)
- ``ANTHROPIC_MODEL``: 模型名称

### 3. 部署

``````bash
chmod +x deploy.sh start.sh stop.sh
./deploy.sh
``````

### 4. 启动服务

``````bash
./start.sh
``````

### 5. 访问

- 前端地址: http://服务器IP:8000/web/
- API 文档: http://服务器IP:8000/docs
- 管理后台: http://服务器IP:8000/admin

**默认账号**: admin / admin123

## 生产环境部署 (systemd)

``````bash
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
``````

## 目录结构

``````
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
``````

## 常用命令

``````bash
# 启动
./start.sh

# 停止
./stop.sh

# 查看日志
tail -f ~/.oh-enterprise/logs/server.log

# 查看服务状态
curl http://localhost:8000/health
``````
"@

Set-Content -Path "$PACKAGE_DIR\README.md" -Value $readme

# 打包
Write-Host "[6/6] 打包..."

# 使用 Python 打包
Set-Location $DIST_DIR
python -c @"
import tarfile
import os
with tarfile.open('$PACKAGE_NAME.tar.gz', 'w:gz') as tar:
    tar.add('$PACKAGE_NAME')
print('Package created: $PACKAGE_NAME.tar.gz')
"@

# 显示结果
Write-Host ""
Write-Host "=========================================="
Write-Host "  打包完成!"
Write-Host "=========================================="
Write-Host ""

$fileSize = (Get-Item "$DIST_DIR\$PACKAGE_NAME.tar.gz").Length / 1MB
Write-Host "部署包: $DIST_DIR\$PACKAGE_NAME.tar.gz"
Write-Host "大小: $([math]::Round($fileSize, 2)) MB"
Write-Host ""
Write-Host "部署步骤:"
Write-Host "1. 上传 $PACKAGE_NAME.tar.gz 到服务器"
Write-Host "2. 解压: tar -xzf $PACKAGE_NAME.tar.gz"
Write-Host "3. 进入目录: cd $PACKAGE_NAME"
Write-Host "4. 配置: cp .env.example .env && vim .env"
Write-Host "5. 部署: ./deploy.sh"
Write-Host "6. 启动: ./start.sh"
Write-Host ""