#!/bin/bash
# /opt/ura-post/data (creators.json, videos.json, config.json、アップロード済みファイル)を
# 日次で別ディレクトリにtar.gzで退避し、直近分だけ世代管理で残す。
# 同一ディスク上のバックアップなので、VPS/ディスク自体の全損には無力な点に注意
# (誤操作・アプリ側の不具合によるデータ破損/削除に対する安全網)。
set -euo pipefail

SOURCE_DIR="/opt/ura-post/data"
BACKUP_DIR="/root/ura-post-backups"
KEEP_DAYS=14
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE_NAME="ura-post-data-${TIMESTAMP}.tar.gz"

mkdir -p "${BACKUP_DIR}"
tar -czf "${BACKUP_DIR}/${ARCHIVE_NAME}" -C "$(dirname "${SOURCE_DIR}")" "$(basename "${SOURCE_DIR}")"

# KEEP_DAYS日より古いバックアップを削除
find "${BACKUP_DIR}" -name 'ura-post-data-*.tar.gz' -mtime "+${KEEP_DAYS}" -delete

echo "$(date '+%Y-%m-%d %H:%M:%S') backup created: ${ARCHIVE_NAME} ($(du -h "${BACKUP_DIR}/${ARCHIVE_NAME}" | cut -f1))"
