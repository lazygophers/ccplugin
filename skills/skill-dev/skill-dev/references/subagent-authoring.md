# subagent 编写要点 + 流派分歧

> subagent frontmatter / body 设计点 + skill 流派取舍。主入口 SKILL.md。

## subagent 编写要点

subagent ≠ skill：独立 context + 自定义 system prompt + 特定工具 + 独立权限。

```yaml
---
name: code-reviewer
description: Reviews code for quality and best practices. Use proactively after code changes.
tools: Read, Glob, Grep, Bash       # 不列则继承全部
model: sonnet                        # sonnet/opus/haiku/fable/inherit
---
<body = system prompt>
```

**关键设计点**：

- **body 就是 system prompt**：subagent 只收 body + 环境细节，**不继承完整 CC system prompt**。关键约定必须在 body 内显式写。
- **🛑 错误处理约定**（致命遗漏补全）：body 须指示 Claude 工具失败时（Bash 超时 / Read 文件不存在 / MCP 掉线）**显式标注 `[工具失败: <原因>]` 而非把错误输出当结果返回**。否则主对话会把 subagent 的错误摘要当有效数据消费——静默降级，且直到出事才发现不了。
- **工具继承例外**（即使列了也不给）：AskUserQuestion / EnterPlanMode / ExitPlanMode(非 plan) / ScheduleWakeup / WaitForMcpServers。
- **Explore / Plan 跳过 CLAUDE.md + git status**：其他 subagent 都加载。若规则必须到达（如「忽略 vendor/」），须在委派 prompt 里重述。
- **skills 字段**：注入完整 skill 内容（非仅 description）。不能 preload `disable-model-invocation: true` 的 skill。
- **memory 字段**：`user`/`project`/`local`，跨会话学习。`project` 可版本控制共享，推荐默认。
- **PreToolUse hook 条件验证**：需细于 tools 字段的控制时用（例只允许 SELECT 的 db agent，hook grep 写操作 exit 2 阻断）。
- **嵌套**：subagent 可 spawn 自己的 subagent，深度限 5 层。fork 不能再生 fork。
- **fork vs named**：fork 继承整段对话（省重新解释），named 从定义文件起步（隔离干净）。

**选 subagent vs 主对话 vs skill**：

- 主对话：频繁往返、多阶段共享 context、快速小改、延迟敏感
- subagent：产出冗余、需工具限制、自包含回摘要
- skill：可复用 prompt，主对话 context 内跑；`context: fork` 可在 skill 内嵌 subagent

## 流派分歧（取舍非二选一）

### 常驻 vs 按需

| 类型 | 适合 | 代表 |
|------|------|------|
| 常驻（CLAUDE.md / AGENTS.md） | 全局约定、编码标准、安全硬规 | 规则遵守一致性高，持续耗 token |
| 按需（Skills） | 工作流、领域知识、可复用流程 | token 省、上下文洁净，依赖触发 |

→ 硬规进 CLAUDE.md，流程进 skill。

### 显式 vs 隐式触发

- Claude skill = 显式（description 是发现入口，让 Claude 判何时用）
- Cursor rule = 隐式（文件 glob 命中即强制生效）

→ 本 skill 是显式（`disable-model-invocation: true`）。

### runtime 中立

好的 agent 配置应平台中立：SKILL.md 不写死「在 Claude Code 里」（除非用 CC 扩展字段如 `context: fork`）。badge 用 `Agent Skills Standard` 而非钉死单一 runtime。
