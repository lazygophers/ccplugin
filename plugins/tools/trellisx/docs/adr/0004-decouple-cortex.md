# ADR 0004 · trellisx 解耦 cortex (tool 中立)

- 状态: Accepted (2026-06-29)
- 分支: F (cortex 全移除 + Stop 两闸)
- 相关 commit: 778cb188

## 背景 (Context)

trellisx 流程原内置 cortex 落档:
- task-lifecycle 全景 mermaid 含 CORTEX 节点
- 阶段表含 "cortex 落档" 行
- 阶段间硬规含 "cortex 落档前禁 stop"
- guard 提醒含 cortex

cortex 是用户级知识库工具 (双层 vault + 5 级记忆)。将特定知识库工具硬绑进 trellisx 流程, 降低插件可移植性 (用户可能用 Obsidian / Logseq / 其他知识库, 或不用)。

## 决策 (Decision)

**trellisx 插件解耦 cortex**: trellisx 内置 cortex 全删 (全景图 / 阶段表 / 硬规 / guard 提醒)。插件 **tool 中立**, 不绑特定知识库工具。

**边界**: 全局 `~/.claude/CLAUDE.md` 的 "非平凡发现落 cortex" 规则 **不动** (那是用户层规则, 非 trellisx 层)。用户层 cortex 规则继续全局生效, 与 trellisx 解耦不冲突。

## 后果 (Consequences)

- ✅ 插件可移植性↑ (不绑特定知识库, 跨用户/跨工具栈通用)
- ✅ tool 中立 (符合 runtime 中立原则: 不绑 Claude Code, 也不绑 cortex)
- ✅ 用户层知识库规则仍生效 (全局 CLAUDE.md 管, 非插件管)
- ⚠️ trellisx 不强制沉淀 (依赖用户全局规则或自觉)

## 备选 (Alternatives)

| 方案 | 否决理由 |
| --- | --- |
| 保留 cortex 绑定 (原设计) | 降低可移植性; 强制特定知识库; 用户用其他工具时流程失效 |
| 绑定抽象知识库接口 | 过度设计; trellisx 职责是任务编排, 非知识库路由 |

## 关联

- 同批 Stop 闸调整: 删 "活动 task 未完成" 闸 (用户: 不应禁 stop), 见 concepts §5 / architecture §4
