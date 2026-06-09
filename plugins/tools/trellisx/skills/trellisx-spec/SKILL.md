---
name: trellisx-spec
description: 初始化 / 优化 / 重写 .trellis/spec/ 规则文档, 允许破坏式变更 (丢弃旧版本、合并、拆分、推翻原结构), 把描述性条款改为可机器验证的命令式契约 (MUST / 禁 / 严禁)。流程: 诊断 (初始化跳过) → 提案 → AskUserQuestion 强制审批 → 执行 + 同步 task manifest 引用清单。严禁未确认改写。
when_to_use: 用户提及 spec 的 初始化/优化/重写/收紧/refactor, 抱怨 spec 弱/不可执行, 任务收尾沉淀, 或说"记不住/老忘/反复犯错/又踩坑"暗示规则未沉淀。短语 "初始化 spec" "优化 spec" "记不住"。
argument-hint: [scope]
arguments: [范围]
context: fork
agent: trellisx-spec
---

# trellisx-spec — Spec 破坏式优化

`.trellis/spec/` 是 trellis 项目的可执行契约层 (在 sub-agent dispatch 时被注入)。**规则不强 = 没规则**。这个 skill 在用户授权"破坏式"修改的前提下, 把 spec 改造为可执行、可验证、可约束 agent 行为的契约。

## 核心立场

| 立场 | 说明 |
| --- | --- |
| 允许破坏 | 推翻原结构、删冗余、改命名、不保持向后兼容 |
| 拒绝静默写 | 每次破坏前必须展示 plan + 影响面, 经用户批准后才动盘 |
| 命令式优于描述式 | "MUST/MUST NOT/禁/必" 替代 "建议/通常/可以考虑" |
| 可机器验证 > 可读 | 优先写能被 lint/test/grep 验证的条目, 而非空泛文字 |
| 引证而非复述 | 外部已有规则用相对路径 + 锚点引用, 不抄过来制造漂移 |

## 参数

| 名称 | 取值 | 默认 |
| --- | --- | --- |
| `$范围` | 目录或文件 glob (e.g. `guides/`) / `all` | `all` (全 `.trellis/spec/`) |

## 模式分支

按触发短语 + `.trellis/spec/` 现状自动判定:

| 触发 | 模式 | 流程入口 |
| --- | --- | --- |
| "初始化 spec" / `.trellis/spec/` 空或仅 `index.md` | **init** | 跳过诊断, 走 propose + approve + execute |
| 用户要求 "优化 / 重写 / 收紧 / refactor" / 抱怨 spec 弱 / "记不住" | **optimize** | 走完整 4 阶段 |
| trellis 任务完成 Phase 3 收尾 (`task.py complete` 前) | **sediment** | 跳过诊断, propose 仅含"本任务学习增量" |

## 工作流概览 (4 阶段, 按模式裁剪)

| 阶段 | 行动 | 详细内容 |
| --- | --- | --- |
| 1 | 诊断 (optimize 模式独占) | 读 `references/diagnose.md` |
| 2 | 提案 (列变更, 不写盘) | 读 `references/propose.md` |
| 3 | 审批 (AskUserQuestion 强制) | 读 `references/approve.md` |
| 4 | 执行 (一次写盘 + 同步 manifest 引用) | 读 `references/execute.md` |

不命中: 仅询问 spec 含义 / 想查 spec / 让 spec 新增一条 → 走 trellis 自带 `trellis-update-spec`, 不加载本 skill。

## 参考集 (按需读)

| 文件 | 何时读 |
| --- | --- |
| `references/diagnose.md` | optimize 模式阶段 1 |
| `references/propose.md` | 任何模式阶段 2 (init 用模板提案, optimize 用诊断结果, sediment 用本任务学习) |
| `references/approve.md` | 阶段 3, 设计 AskUserQuestion 问句前 |
| `references/execute.md` | 阶段 4, 写盘 + 同步 |
| `references/rewrite-style.md` | 任何写 spec 条款时 (命令式范本) |
| `references/init-mode.md` | init 模式独占 (首版模板) |
| `references/sediment-mode.md` | sediment 模式独占 (任务学习 → spec 增量) |
| `references/selfcheck.md` | 阶段 4 完成后自检 |

## 引用

- spec 入口: 读 `.trellis/spec/` 目录 (执行时按 trellis 实际结构识别)
- 命令式范本: 项目根 CLAUDE.md (若有)
- task manifest 读取顺序: 见 trellis workflow 文档相关章节
- 相关 skill: `trellisx-orchestrate` (planning 阶段编排; sediment 模式由 orchestrate Phase 3 触发本 skill)
