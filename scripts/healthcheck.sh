#!/bin/bash
# https://ura-post.com が正常に応答しているか確認する。
# systemdのRestart=on-failureはプロセスが「異常終了」した場合しか検知できないため、
# プロセスは生きているがHTTPに応答しなくなった(ハング)ケースをここで補う。
# 失敗時は自動でura-post.serviceを再起動し、結果をログに残す。
# 注意: このスクリプト自体は「誰かに通知する」ことはしない(メール等の送信手段が無いため)。
# 本当の意味での死活監視・通知が必要な場合は、UptimeRobot等の外形監視サービスを別途使うこと。
set -uo pipefail

URL="https://ura-post.com/"
LOG_FILE="/var/log/ura-post-healthcheck.log"
TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${URL}")

if [ "${HTTP_CODE}" = "200" ]; then
  exit 0
fi

echo "${TIMESTAMP} healthcheck failed (http_code=${HTTP_CODE}), restarting ura-post.service" >> "${LOG_FILE}"
systemctl restart ura-post
sleep 3
NEW_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${URL}")
echo "${TIMESTAMP} after restart: http_code=${NEW_HTTP_CODE}" >> "${LOG_FILE}"
