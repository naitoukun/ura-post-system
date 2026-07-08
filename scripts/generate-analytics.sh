#!/bin/bash
# Nginxのアクセスログ(access.log + 直近のローテーション分access.log.1)からGoAccessで
# 静的HTMLレポートを生成する。生成先(/var/www/ura-post-analytics/)はNginx側で
# Basic認証をかけて配信している(location /analytics/、認証ファイルは
# /etc/nginx/.htpasswd-analyticsで別途作成済み)。
# GAタグ等の外部サービスを使わず、既存のアクセスログだけで完結させることで、
# アダルトサイトでのGoogle系解析ツール利用リスクを避けている。
set -euo pipefail

OUTPUT_DIR="/var/www/ura-post-analytics"

LOG_FILES=("/var/log/nginx/access.log")
if [ -f "/var/log/nginx/access.log.1" ]; then
  LOG_FILES+=("/var/log/nginx/access.log.1")
fi

mkdir -p "${OUTPUT_DIR}"
goaccess "${LOG_FILES[@]}" --log-format=COMBINED -o "${OUTPUT_DIR}/report.html" -a --ignore-crawlers 2>/dev/null
chown www-data:www-data "${OUTPUT_DIR}/report.html"
