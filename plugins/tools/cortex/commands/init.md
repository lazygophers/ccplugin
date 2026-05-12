---
description: 初始化/重建 cortex vault 骨架 (双 namespace + seed 文件)
---

# /cortex:init

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

按 cortex-install SKILL 完整流程执行 vault 初始化:

1. 读 `~/.cortex/config.json` → vault / lang / install_path
2. 若 `$VAULT/_meta/version.json` 存在 → 报已初始化, 提示 `--force` (用户在 claude 内无法传, 跳过)
3. preset = `lyt` (固定)
4. 写共享根: `_meta/version.json` / `memory-policy.yaml` / `template-manifest.json` / `_templates/` / `index.md` / `hot.md` / `主页.md` / `焦点.md`
5. 按 `presets/_structure.json` 创建知识库 + 记忆 + 仪表盘 + 归档目录树
6. 复制 seed_files (含占位符: `{{TITLE}} {{CURRENT_PATH}} {{LAST_UPDATED}}`)
7. **跳过** git auto-sync 询问 (默认 off)
8. **跳过** cron 注册询问 (用户单独跑 `/cortex:install_cron`)

不动用户已写入笔记 (frontmatter `last_modified > created` 则跳过)。
回报创建/跳过文件总数。

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
