---
title: hook 入口统一 hooks.py（非 skein.py）
layer: recall
category: arch
keywords: [hook,入口,hooks.py,unified,cmd_*,DISPATCH,plugin.json]
source: sediment
authored-by: skein-spec
created: 1784613382
status: active
related: []
updated: 1784613382
---

## 铁律

- MUST：所有 hook 入口统一在 `hooks.py` 中的 `cmd_*` 函数，禁止分散在 `skein.py` 等其他文件
- MUST：新增 hook 一律在 `hooks.py` 添加 `cmd_<hook-name>` 函数并注册到 `DISPATCH` 字典
- MUST：hook 调用统一经 `bin/skein-hooks <subcmd>` → `hooks.py`，不经 `bin/skein <hook>` → `skein.py`
- MUST：`plugin.json` 中 hook command 指向 `bin/skein-hooks` (非 `bin/skein`)

## 反例表

| 禁 | 改为 |
|---|---|
| 在 `skein.py` 添加新 hook 方法 | 在 `hooks.py` 添加 `cmd_*` 函数 + 注册到 `DISPATCH` |
| hook 入口经 `bin/skein` → `skein.py` | 统一经 `bin/skein-hooks` → `hooks.py` |
| `plugin.json` 指向 `bin/skein user-prompt` | 改为 `bin/skein-hooks user-prompt` |
| 新 hook 不注册到 `DISPATCH` | 在 `DISPATCH` 字典添加 `"<hook-name>": cmd_<hook-name>` |

## 触发场景

- 新增 Claude Code hook (UserPromptSubmit / PreToolUse / Stop hook 等)
- 将现有 hook 从分散入口迁移到统一 hooks.py
- 修改 hook 行为时误在错误文件添加代码

## 关联

- hook 判定防自降级护栏 — hook 层相关的 prompt 约束
- 并写竞态禁止 — hook 层检测批内写命令 (hooks.py 批检测)
