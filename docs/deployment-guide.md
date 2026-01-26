# 部署指南

## 文档信息

- **项目名称**: 岱山 (daishan-master)
- **生成日期**: 2026-01-26
- **适用范围**: 生产环境部署和运维

## 部署架构概览

岱山项目包含两个独立的 FastAPI 后端服务：

1. **Digital Human Command Interface** (端口 11029)
   - 数字人交互服务
   - 代理 Dify AI 服务

2. **RAG Stream Service** (端口 11027)
   - 多领域 RAG 问答服务
   - 代理 RAGFlow 和 Dify 服务

## 部署方式

### 方式 1: 直接部署（推荐用于开发/测试）

#### 系统要求
- Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- Python 3.12+
- 4GB+ RAM
- 2GB+ 磁盘空间

#### 部署步骤

1. **安装 Python 3.12**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip

# CentOS/RHEL
sudo dnf install python3.12
```

2. **创建部署目录**
```bash
sudo mkdir -p /opt/daishan
sudo chown $USER:$USER /opt/daishan
cd /opt/daishan
```

3. **克隆代码**
```bash
git clone <repository-url> .
```

4. **创建虚拟环境**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

5. **安装依赖**
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -r rag_stream/requirements.txt
```

6. **配置环境变量**
```bash
# 创建 RAG Stream 配置
cat > rag_stream/.env << EOF
RAG_BASE_URL=http://172.16.11.60:8081
RAG_API_KEY=ragflow-I0YmY0NzUwNGZmNzExZjBiZjYzMDI0Mm
REQUEST_TIMEOUT=300
STREAM_TIMEOUT=300
SESSION_EXPIRE_HOURS=1
MAX_SESSIONS_PER_USER=5
EOF
```

7. **使用 systemd 管理服务**

创建 Digital Human 服务：
```bash
sudo tee /etc/systemd/system/digital-human.service << EOF
[Unit]
Description=Digital Human Command Interface
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/daishan/Digital_human_command_interface
Environment="PATH=/opt/daishan/.venv/bin"
ExecStart=/opt/daishan/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 11029 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

创建 RAG Stream 服务：
```bash
sudo tee /etc/systemd/system/rag-stream.service << EOF
[Unit]
Description=RAG Stream Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/daishan/rag_stream
Environment="PATH=/opt/daishan/.venv/bin"
ExecStart=/opt/daishan/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 11027 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

8. **启动服务**
```bash
sudo systemctl daemon-reload
sudo systemctl enable digital-human rag-stream
sudo systemctl start digital-human rag-stream
```

9. **检查服务状态**
```bash
sudo systemctl status digital-human
sudo systemctl status rag-stream
```

10. **查看日志**
```bash
sudo journalctl -u digital-human -f
sudo journalctl -u rag-stream -f
```

### 方式 2: Docker 部署（推荐用于生产）

#### 创建 Dockerfile

**Digital Human Dockerfile:**
```dockerfile
# Digital_human_command_interface/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY main.py .

# 暴露端口
EXPOSE 11029

# 启动服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11029", "--workers", "1"]
```

**RAG Stream Dockerfile:**
```dockerfile
# rag_stream/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY main.py config.py models.py ./

# 暴露端口
EXPOSE 11027

# 启动服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "11027", "--workers", "1"]
```

#### 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  digital-human:
    build:
      context: ./Digital_human_command_interface
      dockerfile: Dockerfile
    container_name: digital-human
    ports:
      - "11029:11029"
    restart: unless-stopped
    environment:
      - DIFY_API_KEY=app-Dkzi2px4Gg8F7vaUdn22Z3VL
      - DIFY_BASE_URL=http://172.16.11.60/v1
      - DIFY_TIMEOUT=30.0
    networks:
      - daishan-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11029/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  rag-stream:
    build:
      context: ./rag_stream
      dockerfile: Dockerfile
    container_name: rag-stream
    ports:
      - "11027:11027"
    restart: unless-stopped
    environment:
      - RAG_BASE_URL=http://172.16.11.60:8081
      - RAG_API_KEY=ragflow-I0YmY0NzUwNGZmNzExZjBiZjYzMDI0Mm
      - REQUEST_TIMEOUT=300
      - STREAM_TIMEOUT=300
      - SESSION_EXPIRE_HOURS=1
      - MAX_SESSIONS_PER_USER=5
    networks:
      - daishan-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11027/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  daishan-network:
    driver: bridge
```

#### 部署步骤

1. **构建镜像**
```bash
docker-compose build
```

2. **启动服务**
```bash
docker-compose up -d
```

3. **查看日志**
```bash
docker-compose logs -f
```

4. **停止服务**
```bash
docker-compose down
```

5. **重启服务**
```bash
docker-compose restart
```

### 方式 3: Kubernetes 部署（推荐用于大规模生产）

#### 创建 Kubernetes 配置

**digital-human-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: digital-human
  labels:
    app: digital-human
spec:
  replicas: 2
  selector:
    matchLabels:
      app: digital-human
  template:
    metadata:
      labels:
        app: digital-human
    spec:
      containers:
      - name: digital-human
        image: daishan/digital-human:latest
        ports:
        - containerPort: 11029
        env:
        - name: DIFY_API_KEY
          valueFrom:
            secretKeyRef:
              name: daishan-secrets
              key: dify-api-key
        - name: DIFY_BASE_URL
          value: "http://172.16.11.60/v1"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 11029
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 11029
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: digital-human-service
spec:
  selector:
    app: digital-human
  ports:
  - protocol: TCP
    port: 11029
    targetPort: 11029
  type: LoadBalancer
```

**rag-stream-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-stream
  labels:
    app: rag-stream
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rag-stream
  template:
    metadata:
      labels:
        app: rag-stream
    spec:
      containers:
      - name: rag-stream
        image: daishan/rag-stream:latest
        ports:
        - containerPort: 11027
        env:
        - name: RAG_BASE_URL
          value: "http://172.16.11.60:8081"
        - name: RAG_API_KEY
          valueFrom:
            secretKeyRef:
              name: daishan-secrets
              key: rag-api-key
        - name: REQUEST_TIMEOUT
          value: "300"
        - name: SESSION_EXPIRE_HOURS
          value: "1"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 11027
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 11027
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: rag-stream-service
spec:
  selector:
    app: rag-stream
  ports:
  - protocol: TCP
    port: 11027
    targetPort: 11027
  type: LoadBalancer
```

**secrets.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: daishan-secrets
type: Opaque
stringData:
  dify-api-key: "app-Dkzi2px4Gg8F7vaUdn22Z3VL"
  rag-api-key: "ragflow-I0YmY0NzUwNGZmNzExZjBiZjYzMDI0Mm"
```

#### 部署步骤

```bash
# 创建 secrets
kubectl apply -f secrets.yaml

# 部署服务
kubectl apply -f digital-human-deployment.yaml
kubectl apply -f rag-stream-deployment.yaml

# 查看部署状态
kubectl get deployments
kubectl get pods
kubectl get services

# 查看日志
kubectl logs -f deployment/digital-human
kubectl logs -f deployment/rag-stream
```

## 反向代理配置

### Nginx 配置

```nginx
# /etc/nginx/sites-available/daishan

upstream digital_human {
    server localhost:11029;
}

upstream rag_stream {
    server localhost:11027;
}

server {
    listen 80;
    server_name daishan.example.com;

    # Digital Human API
    location /digital-human/ {
        proxy_pass http://digital_human/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # RAG Stream API
    location /rag-stream/ {
        proxy_pass http://rag_stream/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/daishan /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL/TLS 配置（使用 Let's Encrypt）

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d daishan.example.com

# 自动续期
sudo certbot renew --dry-run
```

## 监控和日志

### 日志管理

#### 使用 systemd 日志
```bash
# 查看实时日志
sudo journalctl -u digital-human -f
sudo journalctl -u rag-stream -f

# 查看最近日志
sudo journalctl -u digital-human -n 100
sudo journalctl -u rag-stream -n 100

# 按时间范围查看
sudo journalctl -u digital-human --since "2026-01-26 10:00:00"
```

#### 日志轮转配置

创建 `/etc/logrotate.d/daishan`:
```
/var/log/daishan/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload digital-human rag-stream
    endscript
}
```

### 性能监控

#### 使用 Prometheus + Grafana

安装 Prometheus Python 客户端：
```bash
pip install prometheus-client
```

在代码中添加 metrics 端点（示例）：
```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# 定义指标
request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### 健康检查

两个服务都提供 `/health` 端点：

```bash
# Digital Human
curl http://localhost:11029/health

# RAG Stream
curl http://localhost:11027/health
```

配置监控脚本：
```bash
#!/bin/bash
# /opt/daishan/health-check.sh

check_service() {
    local service=$1
    local port=$2

    if curl -f -s http://localhost:$port/health > /dev/null; then
        echo "$service is healthy"
        return 0
    else
        echo "$service is unhealthy"
        systemctl restart $service
        return 1
    fi
}

check_service "digital-human" 11029
check_service "rag-stream" 11027
```

添加到 crontab：
```bash
*/5 * * * * /opt/daishan/health-check.sh >> /var/log/daishan/health-check.log 2>&1
```

## 备份和恢复

### 备份配置文件

```bash
#!/bin/bash
# /opt/daishan/backup.sh

BACKUP_DIR="/backup/daishan"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份配置
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    /opt/daishan/rag_stream/.env \
    /etc/systemd/system/digital-human.service \
    /etc/systemd/system/rag-stream.service \
    /etc/nginx/sites-available/daishan

# 保留最近 30 天的备份
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +30 -delete
```

### 恢复

```bash
# 解压备份
tar -xzf /backup/daishan/config_20260126_120000.tar.gz -C /

# 重启服务
sudo systemctl daemon-reload
sudo systemctl restart digital-human rag-stream nginx
```

## 安全加固

### 1. 防火墙配置

```bash
# 使用 ufw
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 内部服务端口不对外开放
# 11029 和 11027 仅通过 nginx 反向代理访问
```

### 2. API 密钥管理

**不要在代码中硬编码密钥！**

使用环境变量或密钥管理服务：
```bash
# 使用 systemd 环境文件
sudo tee /etc/daishan/secrets.env << EOF
DIFY_API_KEY=app-Dkzi2px4Gg8F7vaUdn22Z3VL
RAG_API_KEY=ragflow-I0YmY0NzUwNGZmNzExZjBiZjYzMDI0Mm
EOF

sudo chmod 600 /etc/daishan/secrets.env
```

修改 systemd 服务文件：
```ini
[Service]
EnvironmentFile=/etc/daishan/secrets.env
```

### 3. CORS 限制

修改代码，限制允许的来源：
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 指定域名
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

### 4. 速率限制

使用 nginx 限制请求速率：
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /digital-human/ {
    limit_req zone=api_limit burst=20 nodelay;
    # ... 其他配置
}
```

## 性能优化

### 1. 增加 Worker 数量

对于高并发场景，可以增加 worker 数量：
```bash
# 注意：流式处理建议使用单 worker
uvicorn main:app --host 0.0.0.0 --port 11029 --workers 4
```

### 2. 使用 Gunicorn + Uvicorn

```bash
pip install gunicorn

gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:11029
```

### 3. 启用 HTTP/2

在 nginx 中启用 HTTP/2：
```nginx
listen 443 ssl http2;
```

### 4. 缓存静态内容

```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 故障排查

### 服务无法启动

1. 检查端口占用：
```bash
sudo lsof -i :11029
sudo lsof -i :11027
```

2. 检查日志：
```bash
sudo journalctl -u digital-human -n 50
sudo journalctl -u rag-stream -n 50
```

3. 检查依赖：
```bash
source .venv/bin/activate
pip list
```

### 外部服务连接失败

1. 测试网络连接：
```bash
curl -v http://172.16.11.60/v1/health
curl -v http://172.16.11.60:8081/health
```

2. 检查 API 密钥：
```bash
curl -H "Authorization: Bearer <API_KEY>" http://172.16.11.60/v1/health
```

### 内存泄漏

1. 监控内存使用：
```bash
ps aux | grep uvicorn
top -p <PID>
```

2. 定期重启服务：
```bash
# 添加到 crontab
0 3 * * * systemctl restart digital-human rag-stream
```

## 升级和回滚

### 升级流程

1. 备份当前版本
2. 拉取新代码
3. 更新依赖
4. 测试新版本
5. 重启服务

```bash
# 备份
cp -r /opt/daishan /opt/daishan.backup

# 更新代码
cd /opt/daishan
git pull

# 更新依赖
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# 重启服务
sudo systemctl restart digital-human rag-stream
```

### 回滚流程

```bash
# 停止服务
sudo systemctl stop digital-human rag-stream

# 恢复备份
rm -rf /opt/daishan
mv /opt/daishan.backup /opt/daishan

# 启动服务
sudo systemctl start digital-human rag-stream
```

## 运维检查清单

### 日常检查
- [ ] 检查服务状态
- [ ] 查看错误日志
- [ ] 监控资源使用
- [ ] 检查磁盘空间

### 每周检查
- [ ] 审查安全日志
- [ ] 检查备份完整性
- [ ] 更新依赖包
- [ ] 性能分析

### 每月检查
- [ ] 系统更新
- [ ] 证书续期检查
- [ ] 容量规划
- [ ] 灾难恢复演练

## 联系和支持

- 技术支持: 联系项目维护者
- 紧急问题: 查看日志并提交 issue
- 文档更新: 参考最新文档