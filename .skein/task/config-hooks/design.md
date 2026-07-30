# config.yaml 自定义 hooks (阶段钩子 + agent start/stop) — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 测试接缝 (seam)
check 阶段验证的是`行为对不对`而非`跑没跑起来`, 全靠这里选对接缝。三条规则:
1. 优先复用现有接缝, 不新建
2. 取最高接缝 (越靠外部行为越好)
3. 越少越好, 理想 = 1 个

- [x] **唯一接缝 = CLI 命令边界** —— 经真实 `skein.py` / `hooks.py` 子进程跑, 断言退出码 + stdout/stderr + **钩子副作用** (钩子命令 `touch` 一个标记文件, 断言该文件存在/不存在)。
  - 复用 `tests/conftest.py` 既有 `skein_cli` / `ws` fixture, 不新建 fixture
  - 「钩子真的跑了吗」这个问题只能从外部观测 —— 标记文件是最高、最不依赖实现的接缝; 断言内部方法被调用会锁死实现
  - 唯一例外: `_yaml_load` 单独测 (纯函数, 直调即最高接缝), 因为它是唯一高风险项, 要能独立回归

## 1. 为什么走 dispatch 参数而非 harness hook

用户明确排除改 `plugin.json` 与投影 agent 文件。而官方文档明确: **plugin subagents 的 frontmatter `hooks` 字段被静默忽略**（连带 `mcpServers` / `permissionMode`）。所以 harness 的 `SubagentStart`/`SubagentStop` 这条路在本约束下不可用。

走 dispatch 参数反而解掉了 harness 路径的核心硬伤:

| | harness hook | **dispatch 参数** |
|---|---|---|
| plugin subagent 限制 | 被忽略 | 不受影响 |
| 拿到 tid/sid | ❌ harness 不知道 skein 的概念 | ✅ dispatch 本就给 tid+sid+工作目录 |
| start 落点 | 只能用 `PreToolUse` 模拟 | ✅ 真·开工第一步 |
| 可靠性 | harness 保证 | 靠 agent 执行 — 与「自跑 `subtask done/fail`」同级, 那条一直有效 |

代价: agent 崩溃时 stop 钩子不跑。接受 —— 用 `.audit-log` + `doctor` 检查兜底。

## 2. 数据流

```
main 派 agent (dispatch: tid + sid + 工作目录)
      ↓
agent step 0:  hooks.py agent-start --agent <name> --tid <tid> --sid <sid>
      ↓                ↓ 读 config.yaml 的 hooks.agent.<name>.start (+ "*")
   [干活]               ↓ 注入 env → 串行执行
      ↓
agent 收尾:    subtask done|fail  →  hooks.py agent-stop --agent ... --tid ... --sid ...

skein.py 状态迁移命令 (create/confirm/start/check/finish/archive/subtask.*)
      ↓ before → [阶段动作] → after
   同一个 _run_hooks() 执行器
```

## 3. 关键取舍

| 取舍 | 决定 | 理由 |
|---|---|---|
| 配置载体 | **升级 `_yaml_load`**, 不另开 `hooks.json` | core 规则「配置真值来源唯一」; 两个配置源必然漂移 |
| 解析器覆盖面 | 明确子集, **不支持的语法报错指行号** | 静默降级 = 配置无声失效, 是最难查的一类故障 |
| 上下文传递 | **env 注入**, 禁模板插值 | 不拼字符串就没有注入面; shell 里 `$SKEIN_TID` 一样顺手 |
| `before` 失败 | **阻断阶段** | 这才让 hook 成为真质量门 — `check.before` 跑 lint 失败却照样进 check 等于没门 |
| `after` 失败 | 只告警 | 阶段已完成, 回滚代价大于收益 |
| **agent 钩子失败** | **一律只告警不阻断** | 用户钩子挂了不该让 subtask 失败; 要卡质量在 `check.before` 卡, 那里失败信息直给 |
| 列表内执行 | 严格串行, 失败即停 | 并行钩子的调试成本远大于收益 |
| 具名 vs 通配 | **具名先跑, `"*"` 后跑** | 具体优先于通配, 与 CSS / Cursor rules 的直觉一致 |
| shell 执行 | `shell=True` | config.yaml 是用户手写本地文件, 信任级别等同用户敲命令 (与 Claude Code 自身 hooks 一致) |
| agent frontmatter | **不写 `hooks:` 字段** | 被 harness 忽略, 写了是误导后人的死配置 |

## 4. 信任模型 (必须进文档)

| 输入来源 | 信任级别 | 命令构造 |
|---|---|---|
| http exec 端点 | 网络输入, **不可信** | argv 白名单 (既有 core 规则) |
| **config.yaml hooks** | 用户手写本地文件, **可信** | `shell=True` |

两者信任边界不同, 故本设计用 shell 不违反那条 core 规则。

⚠️ **但正因如此**: 既有 core 规则「配置写端点防注入 (仅认 CONFIG_DEFAULTS 键)」现在不够了 —— `hooks` 一旦进 `CONFIG_DEFAULTS` 就会被该端点接受, 于是**远程可写 shell 命令 = RCE**。必须在端点侧硬排除 `hooks` 键。这是本方案唯一的真实安全风险点, 不是可选项。

## 5. 零开销路径

`hooks` 键缺失时: 探一次顶层键 → 立即返回。不解析深层、不构造 env、不 fork。
`agent-start`/`agent-stop` 同理 —— 无配置时是 no-op, 不给 agent 增加实质负担。

## 6. Recursion Guard

执行器给子进程设 `SKEIN_IN_HOOK=1`; `_run_hooks()` 入口检测到该变量即跳过。
这样钩子里可以放心调 `skein list` 查状态, 而 `skein` 内部的状态迁移不会再触发一层钩子。
与 skein 现有 agent 递归护栏同思路。

## 7. 已知风险

| 风险 | 缓解 |
|---|---|
| **自研 YAML 解析器出 bug** (唯一高风险项) | 明确子集 + 报错指行号 + 独立测试文件 + 往返一致性断言 |
| `hooks` 键被 http 端点远程写入 → RCE | 端点侧硬排除, 见 §4 |
| agent 漏跑钩子 | 写进 Checkpoints 与 `subtask done/fail` 同级; `.audit-log` 记录 + `doctor` 报「配了但从未触发」 |
| agent 崩溃 → stop 钩子不跑 | 接受 (harness hook 才能覆盖, 但那要改 plugin.json, 已排除); `doctor` 兜底 |
| before 钩子挂住卡死流程 | timeout 默认 60s + `[hook scope.when#N]` 前缀定位 + `continue_on_error` 逃生阀 |
| 阶段名拼错导致钩子无声失效 | 非法阶段名报错并列出合法值清单 |
