# 使用官方轻量级 Python 镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装必要的系统工具（演示命令执行需要）
RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露 Flask 默认端口
EXPOSE 5000

# 运行应用
CMD ["python", "app.py"]
