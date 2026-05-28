# 使用Python基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖（使用阿里云镜像源加速）
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com gunicorn

# 复制应用代码
COPY . .

# 确保 instance 和 logs 目录存在
RUN mkdir -p /app/instance /app/logs

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# 启动应用
# --preload: master进程先加载app，避免多Worker并发初始化SQLite导致锁冲突
# --workers 2: SQLite不适合大量并发写入，2个Worker足够
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--preload", "wsgi:app"]
