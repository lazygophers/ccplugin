---
name: cortex-lint
description: 跑 18 条 vault lint (frontmatter / wikilink / orphan / 命名 / i18n / 评分字段) + autofix 循环。默认 dry-run, --fix 才改盘。触发: "wiki audit" / "lint" / "vault 体检" / "知识库 audit" / "lint --fix"。
allowed-tools: Bash Read Glob mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_patch_content
---

# cortex-lint

对 vault 跑 18 条 lint 规则, 输出 JSON 报告 (errors/warns/summary)。默认 dry-run, `--fix` 落盘。

## 触发场景

- 用户问 "vault 健康吗 / 知识库 audit / 找 orphan" / 显式 `/cortex:lint`
- cron daily 任务 (01:00)
- cortex-curator agent 调用

## 关键决策树

1. **解析 vault** — 跑 `<PLUGIN_ROOT>/scripts/hooks/_lib/resolve_vault.sh`; 失败报错
2. **调 run.py** — `python3 <PLUGIN_ROOT>/scripts/lint/run.py --vault <path> [--fix] [--scope=<glob>]`

> `<PLUGIN_ROOT>` = **cortex 插件根目录** (`.../plugins/tools/cortex/`), **不是** skill 自身目录。若 AI 通过 opencode/codex symlink 加载 skill, 须先解析 symlink 目标定位 cortex plugin 根, 再拼 `scripts/lint/run.py`。如 `readlink ~/.config/opencode/skills/cortex-lint` → 取父目录 (`.../plugins/tools/cortex`)。
3. **解 JSON 报告** — 按 severity 分 errors / warns; 18 条规则详见 [references/lint-rules.md](references/lint-rules.md)
4. **--fix 模式**: backup 到 `<vault>/_meta/.cortex-backup/lint/<ts>/` → 跑 `autofix:true` 规则 (rule 1/2/6/8/9/11/14/15/16/17) → 输出 JSON
5. **结构违规 (vault-structure-violation)** 走专用 BATCH_MV / BATCH_WHITELIST / PER_ITEM / CANCEL 4 选 (`AskUserQuestion`); 详见 [references/autofix-loop.md](references/autofix-loop.md)
6. **schema 校验** 由 lint 内联 (PR1 合入 cortex-schema), `frontmatter-schema-violation` 检 frontmatter required + tags_required 字段; 详见 [references/schema-validate.md](references/schema-validate.md)

## AUTO_MODE (wrapper / cron 传 `auto` 后缀, persistent 自决修复)

**核心**: "禁问" ≠ "中止". AI 必须**自决循环执行**直至 lint 稳定; 禁报 "需人工"/"无法处理"。

- **不调** AskUserQuestion (wrapper allowed-tools 已禁)
- **结构违规** 走 **BATCH_MV** 默认 (`mkdir -p <backup_root>` → 遍历 `mv_plan[]` mv 到 backup, 跳过 per-item 二次确认)
- **autofix=true** 项: 直接落盘
- **非 autofix** 项: AI 按 [references/autofix-loop.md](references/autofix-loop.md) "自选执行路径" 表执行
- **强制循环**: 跑 `lint.run --fix` → 若 `errors_remaining==0 && structure_purge==0` → exit; 否则继续修, 回 1
- **终态**: clean (任务完成) 或 stuck (工具客观失败: 磁盘只读 / git lock / 权限拒绝)
- 同一规则连 5 轮无进展 (穷尽所有工具路径) 才允许停

## References

| 文件 | 内容 |
|---|---|
| [references/lint-rules.md](references/lint-rules.md) | 18 条规则详表 (id/severity/autofix) + 输出 markdown 格式 |
| [references/autofix-loop.md](references/autofix-loop.md) | --fix 循环 + 自选执行路径表 + 工具优先级 + 严禁辞令 + 终态输出 |
| [references/schema-validate.md](references/schema-validate.md) | frontmatter-schema-violation 启发式补字段 + 模板/示例 lint-skip + 白名单匹配规则 |

## 安全

- 默认 dry-run, 不动盘
- `--fix` 前在 `_meta/.cortex-backup/lint/<ts>/` 全量 backup 待修改文件
- backup 目录由 cortex 维护, 用户可手动 git ignore (`_meta/.cortex-backup/`)
- 永远 mv 到 backup, **从不**真 rm

## 错误处理

- vault 路径解析失败: 立即退出, 提示配置
- run.py 异常退出: 输出 stderr, 不动盘
- 单 rule autofix 失败: 标错继续, 末尾汇总
