# 使用官方 Python 镜像作为基础
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装 Flask 和其他必要的依赖
RUN pip install --no-cache-dir flask
RUN apt-get update && apt-get install -y git

# 复制项目文件到容器中（不包括 app.log）
COPY . /app

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# 暴露端口
EXPOSE 5000

# 运行 Flask 应用
CMD ["flask", "run"]