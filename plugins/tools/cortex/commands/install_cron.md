---
description: 注册 cortex 定时任务 (lint/fold/dashboard/memory-*) 到 crontab (无入参)
---

# /cortex:install_cron

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

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

## AUTO_MODE (shell wrapper 触发, persistent)

**核心原则**: "禁问" ≠ "中止". AI 必须**自决并执行直至任务完成**。遇歧义按推荐默认值执行; 工具不熟悉则尝试其他工具组合 (Bash/Edit/Write/MCP/WebSearch/WebFetch/Read 现有样本); 禁报"需人工"/"AI 不会"/"建议后续处理"。

### 严禁 (任一出现 = 契约违反)

| # | 禁止 |
|---|------|
| 1 | 任何"修复建议"/"建议"/"推荐操作" 章节/表格/列表 (`## 修复建议`, `\| 类型 \| 操作 \|`) |
| 2 | 用户确认问句 (`需确认?`, `是否执行?`, `要继续吗?`, `ok?`, 末尾问号) |
| 3 | AskUserQuestion 调用 (allowed-tools 已禁) |
| 4 | "下一步"/"后续"/"如需"/"可选" 导引 |
| 5 | "需人工"/"待人工"/"建议人工" 推卸辞令 |
| 6 | "AI 能力不足"/"无法自动" 类借口 |
| 7 | 报状态后停 (除非工具客观失败: 磁盘只读/权限拒绝/git lock) |
