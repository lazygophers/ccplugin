---
name: cortex-locale
description: 切换/查看 vault 语言 — 读写 _meta/version.json:.lang, 列 fallback 链, 不动既有目录。仅显式触发 ("切换语言" / "vault 语言")。
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Glob mcp__obsidian__obsidian_get_file_contents
---

# cortex-locale

读/写 vault 当前语言, 报告 locale fallback 链与覆盖来源。

## 触发场景

- 用户想切换 vault 主语言 (e.g. zh-CN → en)
- 检查当前 lang 与 fallback 行为
- 列出可用 locale 文件 (插件内置 / 用户级 / vault 级)

## 子命令

| 子命令 | 行为 |
|--------|------|
| `cortex-locale show` | 打印当前 vault.lang + fallback 链 + 三层来源 |
| `cortex-locale set <lang>` | 写 `_meta/version.json:.lang`, 不重命名既有目录 |
| `cortex-locale list` | 列已加载的所有 locale 文件 (vault/user/plugin) |
| `cortex-locale diff <lang>` | 对比当前 lang 与目标 lang 的 dirs map 差异 |

## 关键约束

1. **不迁移既有目录** — 切语言后 `_meta/version.json:.lang` 改, 旧目录保留, 新建项走新 lang。lint i18n-path-not-in-locale 仅 info, 不报错。
2. **fallback 链** — `zh-CN → zh → en → 报错`。每个 key miss 单独 fallback (非整文件回退)。
3. **三层 locale 优先级** — vault `<vault>/locales/<lang>.yml` > user `~/.config/cortex/locales/<lang>.yml` > plugin `<plugin>/locales/<lang>.yml`。
4. **rename 既有目录** — 用户主动跑 `cortex-refactor migrate-locale`, 本 skill 不动。

## 输出示例

```text
$ cortex-locale show
vault: /Users/foo/obsidian
lang: zh-CN
fallback chain: zh-CN → zh → en
loaded files:
  - plugin: ~/.claude/plugins/.../cortex/locales/zh-CN.yml (16 dirs, 7 prompts)
  - plugin: ~/.claude/plugins/.../cortex/locales/en.yml (fallback)
overrides: none
```

## 实现要点

- 调 `hooks/_lib/cortex_locale.py:load_locale()` 加载 + `detect_vault_lang()` 读取
- `set` 操作前先 dry-run 打印 diff, 然后调 `AskUserQuestion` 工具询问: "写入新 locale 到 `_meta/version.json`?" options: `写入` / `取消`; 用户选 `写入` 才落盘
- 写 `_meta/version.json` 时保留其他字段 (created/preserve_transcript)
