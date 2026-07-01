#!/bin/sh
# SQLite 数据备份脚本（建议配 crontab 每日执行）
# 用法：sh scripts/backup.sh
# 定时：crontab -e 添加  ->  0 2 * * * cd /opt/fangchan && sh scripts/backup.sh

set -e
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DB_FILE="$PROJECT_DIR/data/data.db"
BACKUP_DIR="$PROJECT_DIR/backups"
KEEP=30   # 保留最近 30 份

mkdir -p "$BACKUP_DIR"

if [ ! -f "$DB_FILE" ]; then
  echo "未找到数据库文件：$DB_FILE"
  exit 1
fi

TS=$(date +%Y%m%d_%H%M%S)
cp "$DB_FILE" "$BACKUP_DIR/data_$TS.db"
echo "已备份：$BACKUP_DIR/data_$TS.db"

# 清理旧备份，仅保留最近 KEEP 份
ls -1t "$BACKUP_DIR"/data_*.db 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f
echo "备份完成，当前保留 $(ls -1 "$BACKUP_DIR"/data_*.db 2>/dev/null | wc -l) 份。"
