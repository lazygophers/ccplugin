# 执行载体铁律

本文件只定义 Agent 载体规则。flow 执行过程、状态推进、阶段跳转、失败扭转统一见 [flow-loop.md](flow-loop.md)。

## 铁律

- 「派 agent」= 真实 `Agent` tool_use，不是叙述。无 tool_use 禁说已派。
- main 默认禁写源码；改源码 exec 派 `skein-executor`，验证派 `skein-checker`，收尾派 `skein-finisher`。
- 载体一律具名 subagent，禁 teammate / agent-team，禁 `SendMessage` 派 teammate，禁 `team_name`。
- `skein` CLI 由 main 同步跑；create/confirm/subtask/finish/archive 是任务记录管理，不派 agent。
- 看板由脚本自动刷；AI 禁直接编辑 task.md/task.html。
- 用户交互决策由 main 用 `AskUserQuestion` 处理；subagent 缺信息回传 `需要: <问题>`。
- 文案/格式类变更先给样例确认；逻辑/bug 修复不受此限。
- check/finish dispatch 必须 6 字段自包含：目标 / 已知 / 工作目录与范围 / 输出格式 / 验收标准 / 失败处理。
- exec 派 `skein-executor` 是例外：只给 tid、sid、工作目录，executor 自读 `subtask show`。
- subagent 完成或阻塞，main 立即回传摘要。
- 并发多个 flow 请求不得互相覆盖；先登记 durable task，再串行处理需要用户交互的 planning。

## 派发调用形式

三阶段用 built-in `Agent`，`subagent_type` 必须带插件前缀：

| 用途 | `subagent_type` |
|---|---|
| exec | `skein:skein-executor` |
| check | `skein:skein-checker` |
| finish | `skein:skein-finisher` |
| planning 调研 | `skein:skein-researcher` |
| sediment / maintain | `skein:skein-specer` |

```text
Agent(
  subagent_type = "skein:skein-executor",
  description   = "exec s3 认证中间件",
  prompt        = "<tid + sid + 工作目录>"
)
```

禁用：

- `team_name=...`
- `SendMessage(to=...)` 派 teammate
- 裸名 `subagent_type="skein-executor"`
- 文字宣称派发但无真实 tool_use

## dispatch 字段

除 exec 例外外，prompt 必须自包含：

1. 目标
2. 已知：含 `Active task: <id>` 与工作目录
3. 工作目录与范围
4. 输出格式
5. 验收标准
6. 失败处理

exec 只传 tid/sid/工作目录；其余字段由 `skein-executor` 自读 subtask 详情。
