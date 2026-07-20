# spec metadata hook — 详细设计

## 架构

PostToolUse hook, 复用现有 `hooks.py` + `bin/skein-hooks` dispatch 模式 (同 fmt hook)。

```
Edit|Write|MultiEdit .skein/spec/**/*.md
  → PostToolUse → bin/skein-hooks spec-meta
  → hooks.py cmd_spec_meta(d)
  → 读 tool_input.file_path, 匹配 spec/*.md → 读文件解析 frontmatter
  → 检 title/layer/created/keywords 缺失 + layer∈{core,recall}
  → 有问题: stdout JSON {additionalContext: "⚠️..."}  exit 0
  → 无问题: exit 0 静默
```

## frontmatter 解析

复用 yaml (hooks.py 已 import? 查)。若无, 用简单 `---` 分隔 + `key: value` 行解析 (frontmatter 格式固定, 无嵌套)。

keywords 格式: `[a,b,c]` (YAML inline list) 或多行 `- a`。简单法: 检 key 存在 + 值非空 (strip `[]` 后非空)。

## 检查规则

| 字段 | 检查 | warning 文案 |
|---|---|---|
| title | 缺失或空 | `⚠️ spec metadata 缺失: title (<file>)` |
| layer | 缺失或非 core/recall | `⚠️ spec metadata 非法: layer=<v> (合法: core\|recall) (<file>)` |
| created | 缺失或非数字 | `⚠️ spec metadata 缺失/非法: created (需 unix ts) (<file>)` |
| keywords | 缺失或空数组 | `⚠️ spec metadata 缺失: keywords (<file>)` |

多字段问题合并一条 warning (换行分隔)。

## 取舍

- **非阻塞**: exit 0 + additionalContext。理由: spec 是长尾记忆, 写时阻断太重; warning 提醒即可, 用户自行补。
- **category 不校验**: 用户裁定允许任意类目名 (CATS 只是默认集, 不强制)。
- **created 不校验范围**: 只检存在 + 数字 (负数/未来值不拦, ts 语义留给用户)。
- **路径匹配**: regex `(?:^|/)\.skein/spec/.+\.md$` (同 PRD_RE 模式)。

## 不含调度图

单 task 单 subtask (改动集中 hooks.py + plugin.json, ≤3 文件微改, worktree 豁免原地做)。调度归 task.json。
