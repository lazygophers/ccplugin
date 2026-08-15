#!/bin/bash
# SKEIN 集成测试一键跑: compose 起 → 等健康 → venv 装测试依赖 → pytest → 收尾关容器。
# 用法: make integration-test (或直接 ./integration/run.sh)
set -euo pipefail
cd "$(dirname "$0")"

echo "[itest] 构建并启动容器 (首次约 1-2 分钟)…"
docker compose up -d --build --wait
echo "[itest] 容器健康: $(docker compose ps --format '{{.Name}} {{.Status}}')"

if [ ! -x .venv/bin/python ]; then
  echo "[itest] 创建测试 venv…"
  python3 -m venv .venv
fi
.venv/bin/pip install -q -r requirements-test.txt
# 直连 cdn.playwright.dev 会 TLS reset, 走 npmmirror 镜像 (已缓存则秒过)
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright \
  .venv/bin/python -m playwright install chromium >/dev/null 2>&1 || \
  echo "[itest] Playwright chromium 安装失败 (UI 测试将跳过)" >&2

rc=0
.venv/bin/python -m pytest tests -v || rc=$?

echo "[itest] 关闭容器…"
docker compose down -v
exit $rc
