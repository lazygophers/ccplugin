# ADR 0003 · main 写源码默认禁 (opt-out)

- 状态: Accepted (2026-06-29)
- 分支: E (执行载体 4 层)
- 相关 commit: 778cb188

## 背景 (Context)

main 直做层是否允许写源码? 文档自相矛盾:
- `layer-selection.md`: "main 直做, 实施类必在 worktree 内写" → 允许
- `trellisx-flow SKILL.md`: "main 禁亲改源码" → 绝对禁

矛盾需消解。

## 决策 (Decision)

**main 写源码默认禁, opt-out 例外**:
- 默认: 实质工作 (写源码) **优先派 subagent**
- 例外 (特别情况, 必在 task worktree 内):
  - ≤ 3 文件微改 (已知 file:line, 单点)
  - subagent 难处理的上下文密集决策 (需继承完整对话上下文)
  - 用户显式要求 main 直接做

opt-out 设计: main 直做仍是合法层 (用于只读探索 + 例外实施), 但实施类默认走 subagent。

## 后果 (Consequences)

- ✅ 隔离强制 (实质工作默认 subagent, 隔离 context window)
- ✅ main 直做层保留 (只读探索 + 例外, 不僵化)
- ✅ worktree 约束统一 (任何 main 写必在 task worktree 内)
- ⚠️ "main 直做 ≤3文件" 决策表行退化为只读探索 + 例外实施

## 备选 (Alternatives)

| 方案 | 否决理由 |
| --- | --- |
| 绝对禁 main 写源码 (flow 旧版) | 失去 main 直做灵活性; 单点微改也强制 subagent, 过重 |
| 自由写 (layer-selection 旧版) | 弱化隔离; 实质工作不强制 subagent, 违背执行载体闭环 |

## 边界澄清

- main 在**主工作区**禁写源码 (无论例外与否)
- main 在 **task worktree 内** 可写 (默认仍优先派 subagent, 例外才直接做)
- `--no-worktree` 不豁免 main 写约束 (subagent 改主工作区, main 仍禁)
