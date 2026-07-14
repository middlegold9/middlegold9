#!/bin/sh
set -e

# 确保数据目录存在
mkdir -p "$(dirname "$DB_PATH")"

# 仅当数据库不存在且显式开启 SEED_DATA 时，灌入示例数据（避免覆盖客户真实数据）
if [ "$SEED_DATA" = "true" ] && [ ! -f "$DB_PATH" ]; then
  echo "[entrypoint] 首次启动，灌入示例数据 ..."
  python seed_data.py
fi

echo "[entrypoint] 启动 API 服务 (DB_PATH=$DB_PATH) ..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
