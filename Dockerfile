# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app


# 复制requirements文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 streamlit
RUN chown -R streamlit:streamlit /app
USER streamlit

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 启动命令
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.fileWatcherType=none"] 