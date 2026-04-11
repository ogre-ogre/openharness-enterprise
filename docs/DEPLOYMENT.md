# OpenHarness Enterprise 部署指南

## 环境要求

### 后端
- Python 3.10+
- uv (Python 包管理器)
- SQLite3

### 前端（可选，开发模式）
- Node.js 18+
- npm 或 yarn

---

## 快速部署（开发模式）

### Windows

```powershell
# 1. 进入项目目录
cd D:\openharness-enterprise

# 2. 安装依赖
uv sync --extra dev

# 3. 设置环境变量
$env:ANTHROPIC_AUTH_TOKEN = "your-api-key"
$env:ANTHROPIC_BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic"
$env:ANTHROPIC_MODEL = "glm-5"

# 4. 初始化
uv run oh-enterprise init

# 5. 启动服务
uv run oh-enterprise start --port 8000

# 6. 启动前端（另一个终端）
cd web
npm install
npm run dev
```

### Linux/macOS

```bash
# 1. 进入项目目录
cd /opt/openharness-enterprise

# 2. 安装依赖
uv sync --extra dev

# 3. 设置环境变量
export ANTHROPIC_AUTH_TOKEN="your-api-key"
export ANTHROPIC_BASE_URL="https://coding.dashscope.aliyuncs.com/apps/anthropic"
export ANTHROPIC_MODEL="glm-5"

# 4. 初始化
uv run oh-enterprise init

# 5. 启动服务
uv run oh-enterprise start --port 8000
```

---

## 生产部署（Linux）

### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3 python3-pip python3-venv git curl

# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 2. 上传代码

**方式一：SCP 上传**

```bash
# 在本地执行
scp -r D:\openharness-enterprise user@server:/opt/openharness-enterprise
```

**方式二：Git 克隆**

```bash
# 在服务器执行
cd /opt
git clone <your-repo-url> openharness-enterprise
```

### 3. 安装依赖

```bash
cd /opt/openharness-enterprise
uv sync --extra dev
```

### 4. 创建 systemd 服务

```bash
sudo nano /etc/systemd/system/openharness.service
```

**服务文件内容**:

```ini
[Unit]
Description=OpenHarness Enterprise Server
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/openharness-enterprise

# 环境变量
Environment="ANTHROPIC_AUTH_TOKEN=your-api-key"
Environment="ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic"
Environment="ANTHROPIC_MODEL=glm-5"

# 启动命令
ExecStart=/home/www-data/.local/bin/uv run oh-enterprise start --host 127.0.0.1 --port 8000

# 重启策略
Restart=always
RestartSec=5

# 日志
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 5. 初始化并启动

```bash
# 初始化数据库
cd /opt/openharness-enterprise
sudo -u www-data /home/www-data/.local/bin/uv run oh-enterprise init

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable openharness
sudo systemctl start openharness

# 查看状态
sudo systemctl status openharness

# 查看日志
journalctl -u openharness -f
```

### 6. 构建前端

```bash
cd /opt/openharness-enterprise/web
npm install
npm run build

# 构建产物在 web/dist/ 目录
```

---

## Nginx 反向代理

### 安装 Nginx

```bash
sudo apt install -y nginx
```

### 配置 Nginx

```bash
sudo nano /etc/nginx/sites-available/openharness
```

**配置内容**:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /opt/openharness-enterprise/web/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 代理
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }
}
```

### 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/openharness /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## HTTPS 配置（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo systemctl enable certbot.timer
```

---

## Docker 部署（可选）

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制依赖文件
COPY pyproject.toml .
RUN uv sync --extra dev

# 复制源码
COPY src/ ./src/

# 环境变量
ENV ANTHROPIC_AUTH_TOKEN=""
ENV ANTHROPIC_BASE_URL=""
ENV ANTHROPIC_MODEL="glm-5"

# 数据目录
VOLUME /root/.oh-enterprise

# 端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "oh-enterprise", "start", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  openharness:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_AUTH_TOKEN=your-api-key
      - ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
      - ANTHROPIC_MODEL=glm-5
    volumes:
      - ./data:/root/.oh-enterprise
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./web/dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - openharness
    restart: always
```

### 构建和运行

```bash
# 构建前端
cd web && npm install && npm run build

# 构建并启动
docker-compose up -d --build
```

---

## 目录结构（生产环境）

```
/opt/openharness-enterprise/        # 代码目录
├── src/
├── web/
│   └── dist/                       # 前端构建产物
├── pyproject.toml
└── ...

/var/lib/openharness/               # 数据目录（可选，软链接）
├── data.db
├── users/
├── shared/
│   └── skills/
└── logs/

/etc/nginx/sites-available/openharness   # Nginx 配置
/etc/systemd/system/openharness.service  # Systemd 服务
```

---

## 运维命令

### 服务管理

```bash
# 启动服务
sudo systemctl start openharness

# 停止服务
sudo systemctl stop openharness

# 重启服务
sudo systemctl restart openharness

# 查看状态
sudo systemctl status openharness

# 查看日志
journalctl -u openharness -f
```

### 用户管理

```bash
# 命令行创建用户
cd /opt/openharness-enterprise
sudo -u www-data uv run oh-enterprise create-user username password --role admin

# 或通过 API
curl -X POST http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser","password":"password123"}'
```

### 数据备份

```bash
# 备份数据库
cp ~/.oh-enterprise/data.db ~/.oh-enterprise/data.db.backup

# 备份用户数据
tar -czvf openharness-backup.tar.gz ~/.oh-enterprise/
```

---

## 性能优化

### 数据库优化

```bash
# 定期清理旧日志
sqlite3 ~/.oh-enterprise/data.db "DELETE FROM audit_logs WHERE created_at < datetime('now', '-90 days')"
```

### Nginx 优化

```nginx
# 添加到 http 块
client_max_body_size 10M;
keepalive_timeout 65;
gzip on;
gzip_types text/plain application/json;
```

---

## 常见问题

### 端口被占用

```bash
# 查看端口占用
sudo lsof -i :8000

# 杀死进程
sudo kill -9 <pid>
```

### 权限问题

```bash
# 修改数据目录所有者
sudo chown -R www-data:www-data ~/.oh-enterprise
```

### 连接超时

```nginx
# 增加 Nginx 超时时间
proxy_read_timeout 300;
proxy_connect_timeout 300;
```