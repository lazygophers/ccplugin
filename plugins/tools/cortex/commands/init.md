---
description: 初始化/重建 cortex vault 骨架 (双 namespace + seed 文件)
---

# /cortex:init

[AUTO_MODE strict: 禁询问, fail-fast, 强制默认决策]

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
