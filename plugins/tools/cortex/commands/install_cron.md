---
description: 注册 cortex 定时任务 (lint/fold/dashboard/memory-*) 到 crontab (无入参)
---

# /cortex:install_cron

[AUTO_MODE strict: 禁询问, fail-fast]

注册 cortex 定时任务到系统 crontab。

**必须**用 Bash 工具执行:

```bash
INSTALL_PATH="$(jq -r .install_path ~/.cortex/config.json)"
bash "$INSTALL_PATH/scripts/install_cron.sh"
```

默认任务:
- `lint --check` 每日 03:00
- `fold` 每周日 02:00
- `dashboard` 每周日 02:30
- `memory-promote` 每周一 02:15
- `memory-forget` 每月 1 号 02:45
- `memory-consolidate` 每周日 03:00

报告注册了哪些 cron 行 + 完整 crontab 摘要。
