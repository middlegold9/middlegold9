# 后端镜像：FastAPI + 文档解析
FROM python:3.11-slim

WORKDIR /app

# 安装依赖（pdfplumber/python-docx/python-pptx 均为纯 Python，slim 即可）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 入口脚本（首次可选灌入示例数据，然后启动服务）
RUN chmod +x entrypoint.sh

# 数据目录（挂载卷，持久化 SQLite）
ENV DB_PATH=/app/data/data.db
VOLUME ["/app/data"]

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
