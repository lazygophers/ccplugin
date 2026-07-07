---
created: 2026-07-07
authored-by: trellisx-implement
---

# trellisx skill 拆分 / 重构约定

何时被读: 拆分或重构已有 trellisx skill (一 skill → 多 skill/command) 前
谁读: main / 执行者 agent
不遵守的代价: planning 等逻辑被复制成多份真值源, 拆分后交叉引用批量失效

## 参数化入口开关 (逻辑单一真值源)

- 拆 skill 时若 A (全闭环) 与 B (只做前半段) 共享同一段逻辑, **不复制正文**: 把该逻辑留在 B 的 SKILL 正文作唯一真值源, A 运行时委托 B。
- 委托矛盾 (B 默认「跑完即停」, A 需要续跑) 用**入口层参数开关**化解: 无参 = 默认阻塞 (跑完即停, 交还控制); 有参 (`--continue`/`--exec`, 可接中文别名 `继续`/`执行`) = 不阻塞, 返回产物路径供调用方续跑。
- 「停 / 不停」只是入口行为开关, **逻辑本体零分支** —— 两条路径跑完全同一段正文, 才算真复用。
- 参数解析风格: 选项在描述前 (`[--continue] <描述>`), 复用同族 skill 现有前置选项解析。
- 落地例: `trellisx-flow` 委托 `/trellisx-add --continue` 借用 planning; add 无参时停在 `task.py start` 之前。

## skill 保名 → 交叉引用零改动

- 拆分保留原 skill 名 (如 flow 仍叫 `trellisx-flow`) → 其余 skill / guard.py 对该名的交叉引用**全部存活**, 不动。
- 只有「被迁走的那段逻辑」的触发点描述需随迁移改指向 (如 grill 硬门1 触发点从 `flow step2` 改为 `add planning 阶段`)。
- 拆分后必 grep 校验: 原名交叉引用全绿 + 被迁逻辑触发点已改指。

## 命名空间 command

- `commands/<ns>/<name>.md` 的 slash 名由**子目录派生** = `/<ns>:<name>` (如 `commands/trellisx/go.md` → `/trellisx:go`), 非 frontmatter `name`。
- plugin.json `commands` 数组登记完整相对路径 (`./commands/trellisx/go.md`)。
