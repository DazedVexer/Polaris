# ====== 后端 ======
FROM python:3.11-slim AS backend

WORKDIR /app

# 安装系统依赖（PyMuPDF 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY . .

# ====== 前端构建 ======
FROM node:20-alpine AS frontend

WORKDIR /web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# ====== 最终镜像 ======
FROM python:3.11-slim

WORKDIR /app

# 从 backend 阶段复制 Python 环境
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin

# 复制后端代码
COPY . .

# 从 frontend 阶段复制构建产物
COPY --from=frontend /web/dist /app/web/dist

# 创建必要目录
RUN mkdir -p /app/kb /app/sessions /app/chroma_db

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "server.main"]
