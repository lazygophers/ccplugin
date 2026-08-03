# config.yaml 自定义 hooks

`.skein/config.yaml` 可选的 `hooks` 键, 让用户在 SKEIN 状态迁移的关键节点插入自定义 shell 命令
(lint / 通知 / 埋点等)。两类钩子共用同一执行器 (`hooklib._run_hooks`):

| 类型 | 触发点 | 配置路径 |
| --- | --- | --- |
| 阶段钩子 | `skein` 的 9 个状态迁移命令 (create/confirm/start/check/finish/archive/subtask.start/done/fail) 前后 | `hooks.<阶段名>.<before\|after>` |
| agent 钩子 | agent 生命周期起止 (由 agent 工作流自己在 dispatch 时调用) | `hooks.agent.<agent名\|"*">.<start\|stop>` |

`hooks` 键整体可选 —— 不配则零开销 (不解析、不构造 env、不 fork 子进程), 详见 [§ 零开销路径](#零开销路径)。

## 1. 配置 schema

```yaml
hooks:
  # 阶段钩子: key 直接是 STAGE_NAMES 里的合法阶段名 (见下表), hooks 下无中间层
  check:
    before:
      - command: "npm run lint"        # 必填, shell 字符串
        timeout: 120                   # 秒, 缺省 60
        continue_on_error: false       # 缺省: before=false / after=true
    after:
      - command: "echo checked"
  subtask.done:
    after:
      - command: "curl -s https://example.com/notify -d stage=done"

  # agent 钩子: key 是 agent 名 (如 skein-executor) 或通配 "*" (须加引号, 见解析器 ceiling)
  agent:
    skein-executor:
      start:
        - command: "echo agent start"
      stop:
        - command: "echo agent stop"
    "*":
      start:
        - command: "git status --short"   # 对所有 agent 都跑, 具名先跑通配后跑
```

单条钩子字典字段:

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `command` | 是 | shell 字符串 (`shell=True` 执行, 见 [§ 信任模型](#信任模型)) |
| `timeout` | 否 | 秒, 缺省 60 |
| `cwd` | 否 | 缺省: `worktree` 已配则用 worktree, 否则 repo 根 |
| `continue_on_error` | 否 | 缺省 `before`=false / `after`=true (agent 钩子恒等效 true, 见 [§ 阻断语义表](#阻断语义表)) |

## 2. 阶段名全表

`hooks.<name>` 的 `<name>` 仅接受以下 10 个 (常量 `STAGE_NAMES`, `scripts/skeinlib/hooks/runner.py`):

```
create  confirm  start  exec  check  finish  archive
subtask.start  subtask.done  subtask.fail
```

拼错的阶段名不会静默失效 —— 读配置时 stderr 告警并列出以上合法值清单, `skein doctor` 判为 `✗` error
(拼错等于钩子无声失效, 是最难查的一类故障)。告警而非阻断是刻意的: 读配置在钩子热路径上, 一个笔误不该让
每条 skein 命令都退非零。同款校验也覆盖未知 scope、未知条目字段、`timeout` 非正整数等结构错。

## 3. env 变量表

每条钩子命令的子进程 env, 在继承自 `os.environ` 的基础上, 额外注入 9 个变量:

| 变量 | 含义 | 阶段钩子取值 | agent 钩子取值 |
| --- | --- | --- | --- |
| `SKEIN_SCOPE` | 触发域 | 阶段名 (如 `check`) | `agent` |
| `SKEIN_WHEN` | 触发时机 | `before` / `after` | `start` / `stop` |
| `SKEIN_AGENT` | agent 名 | 空 | dispatch 传入的 agent 名 |
| `SKEIN_TID` | task id | 当前 task | dispatch 传入 |
| `SKEIN_SID` | subtask id | subtask 阶段才有, 否则空 | dispatch 传入 |
| `SKEIN_TASK_DIR` | `.skein/task/<tid>` 路径 | 有 | 空 |
| `SKEIN_WORKTREE` | task worktree 路径 | 有 (未启用 worktree 则空) | 空 |
| `SKEIN_REPO_ROOT` | 仓库根 | 有 | 有 |
| `SKEIN_IN_HOOK` | 递归护栏标记, 恒 `"1"` | 有 | 有 |

### 为何用 env 而非模板插值

设计上明确**禁止**把 `tid`/`sid` 等值拼进 `command` 字符串模板 (如 `"echo {{tid}}"` 再做字符串替换)。
env 注入是唯一路径 —— **不拼字符串就没有注入面**: 模板插值一旦引入, `tid`/`sid` 只要来源不受控
(如从外部输入生成的 task id 含 shell 元字符), 拼接就等于命令注入。用户脚本要用这些值, 在 shell 里
直接读 `$SKEIN_TID` 一样顺手, 且值经 env 传递不经过 shell 解析层, 天然无拼接风险。

## 4. 阻断语义表

| 场景 | 失败行为 | 理由 |
| --- | --- | --- |
| 阶段 `before` | **阻断该阶段** (raise `SystemExit`, 阶段动作不发生) | 这才让 hook 成为真质量门 —— `check.before` 跑 lint 失败却照样进 check 等于没门 |
| 阶段 `after` | 只告警, 阶段结果不变 | 阶段已完成, 回滚代价大于收益 |
| agent `start`/`stop` | **一律只告警不阻断**, 即便钩子显式写 `continue_on_error: false` 也不例外 | 用户钩子挂了不该让 subtask 失败; 要卡质量在 `check.before` 卡, 那里失败信息直给 |

`continue_on_error` 覆盖规则:

- 阶段 `before` 缺省 `false` (失败即阻断); 显式 `continue_on_error: true` → 该条失败仅告警, 后续钩子照跑, 阶段不被阻断。
- 阶段 `after` 缺省 `true` (失败仅告警, 后续钩子照跑); 显式 `continue_on_error: false` → 该条失败即停, 后续钩子不再执行 (但阶段结果依然不受影响, 仍只告警)。
- agent `start`/`stop` 无论 `continue_on_error` 写什么, 失败都只告警不阻断 —— 但**仍遵守"失败即停"**: 同批后续钩子不再执行 (除非该条自身 `continue_on_error: true`)。

列表内执行**严格串行**, 一条失败(非零退出/超时)即停, 除非该条自身豁免 (`continue_on_error: true`)。

### ⚠️ 钩子里禁调 skein 的写命令 (会撞工作区写锁)

阶段钩子在**触发它的那个命令仍持有 `.skein` 工作区写锁时**执行 (`fcntl.flock` 排他锁, 见 core 规则「工作区级 fcntl.flock 排他锁」)。所以钩子里调任何 skein **写**命令 (`create` / `start` / `check` / `finish` / `subtask add` / `config set` …) 会在锁上等到超时:

```yaml
hooks:
  create:
    after:
      - type: command
        command: "skein subtask add ..."   # ❌ 挂 10 秒后超时失败
```

**`SKEIN_IN_HOOK` 防不住这个** —— 它只防「钩子触发钩子」的无限递归, 不防「钩子撞自己上游持有的锁」。两个问题不同源。

安全的做法:

| 想干什么 | 怎么写 |
|---|---|
| 查状态 | ✅ 只读命令可以: `skein list` / `subtask list` / `current` / `contract` (不取写锁) |
| 改 task 状态 | ❌ 别在阶段钩子里做。改用 `subtask.done` 之类**更靠后的阶段钩子**, 或让钩子只落个标记文件, 由后续流程消费 |
| agent 钩子 | ✅ 不受此限 —— `agent-start` / `agent-stop` 不取工作区写锁 |

症状识别: 钩子无输出、恰好卡到 timeout 才失败 → 先怀疑锁, 而不是钩子命令本身写错了。

## 5. 信任模型

| 输入来源 | 信任级别 | 命令构造 |
| --- | --- | --- |
| http exec 端点 (`POST /__skein__/exec` 等) | 网络输入, **不可信** | argv 白名单枚举 (见 core 规则「exec 端点白名单 argv 命令构造」) |
| **`config.yaml` 的 `hooks`** | 用户手写本地文件, **可信** | `shell=True` |

`.skein/config.yaml` 是用户在自己机器上手写的本地文件, 信任级别等同用户直接在终端敲命令
(与 Claude Code 自身 `settings.json` 的 hooks 执行模型一致)。两者信任边界不同, 故本特性用
`shell=True` 执行钩子命令, **不违反**「exec 端点禁 shell 注入」那条 core 规则 —— 那条规则约束的
是网络输入 (http 端点收到的 body), 本特性的输入源从未经过网络。

**正因如此**: `hooks` 键在写端点侧被**显式拒写** —— 引擎的 `CFG_REMOTE_DENY = ("hooks",)`,
`POST /__skein__/config` 命中该元组的键一律跳过, 保留盘上原值。

⚠️ 这里曾靠「`hooks` 不进 `CONFIG_DEFAULTS`, 于是回填时天然被忽略」来防护。那条路已经作废:
`CONFIG_DEFAULTS` 现在**含完整 hooks 骨架** (全部 scope × 时机都列出, 执行列表为空), 于是
「不在默认字典里」这个结构性保护消失了, 必须靠 `CFG_REMOTE_DENY` 这条显式排除撑住。
**改 `CONFIG_DEFAULTS` 或改写端点回填逻辑时须重新验证这条**, 漏了就是**远程可写 shell 命令 = RCE**,
这是本特性唯一的真实安全风险点。

已实测: 向该端点 POST 带 `hooks.agent."*".start[0].command = "touch pwned"` 的 body, 返回 200,
但落盘 `config.yaml` 的 hooks 段逐字未变, `pwned` 文件未生成 (回归测试
`tests/test_board.py::test_serve_config_post`)。

## 6. `_yaml_load` 解析器 ceiling

`config.yaml` 用仓库自研的 mini YAML 解析器 (`_yaml_load`) 读, 不依赖 `PyYAML`。
支持的子集刚好覆盖 `hooks` 结构需要的形状, **不支持的语法直接报错并指出行号**, 不静默降级
(静默降级 = 用户配置无声失效, 是最难查的一类故障)。

支持:

| 语法 | 例 |
| --- | --- |
| 2 空格缩进嵌套 dict | `hooks:\n  agent:\n    skein-executor:\n      start: echo hi` |
| `- ` 开头的 list of dict | `before:\n  - command: echo one\n  - command: echo two` |
| 标量 (字符串/整数/布尔/负数) | `timeout: 120` / `continue_on_error: false` |
| `#` 行内注释 (引号内的 `#` 不截断) | `command: "echo #1"  # 备注` |
| 带引号的键 (通配符 `"*"` 必须加引号) | `"*":\n  stop: echo bye` |

不支持 (报错含行号, 不静默降级):

| 语法 | 报错关键字 |
| --- | --- |
| 锚点 `&anchor` / 引用 `*ref` | `锚点/引用` |
| 多行标量 (`\|` / `>`) | `多行标量` |
| 流式语法 (`{a: 1}` / `[1, 2]`) | `流式语法` |
| 多文档标记 (`---`) | `多文档` |
| tab 缩进 | `tab 缩进` |
| 未闭合引号 | `未闭合引号` |

回归测试见 `scripts/tests/test_yaml_load.py`。

## 7. agent frontmatter 的 hooks 声明当前被 plugin 限制忽略

官方文档明确: **plugin subagents 的 frontmatter `hooks` 字段会被静默忽略** (连带 `mcpServers` /
`permissionMode`)。这些字段只在**放进 `.claude/agents/` 的项目级/用户级 agent** 才生效, 插件市场
分发的 subagent (本仓 `plugins/tools/skein/agents/*.md`) 不在此列。

因此 agent 生命周期钩子**不走** harness 的 `SubagentStart`/`SubagentStop` 事件 —— `agents/*.md` 里
**禁再写 frontmatter `hooks:` 块** (写了不报错也不生效, 是纯误导; skein-researcher / skein-clean 曾
这么写, 钩子一次没跑过)。当前唯一生效路径是: agent 工作流自己在关键节点显式调用 `skein-hooks agent-start --agent <name> --tid <tid> --sid <sid>` /
`agent-stop`(dispatch 参数式子命令, 不读 stdin JSON), 内部再读 `config.yaml` 的 `hooks.agent.*` 决定
要不要真的跑。开工钩子固定占工作流 §0, 收工钩子并进最后一步的收尾动作里 (不另立小节 —— 收尾
和收工是同一件事, 拆两节等于同一动作说两遍)。代价: agent 崩溃时 `agent-stop` 不会被调用, stop 钩子不跑 —— 接受此代价, 用
`.audit-log` + `skein doctor` 兜底探测 (见下节)。

## 8. doctor: 探测「配了但从未触发」

`hooks.agent.*` 钩子靠 agent 自己在工作流里调用, 不像阶段钩子那样有 CLI 命令的强制执行路径 ——
agent 漏调是真实风险, 且不会报任何错误 (钩子没跑就是没跑, 无异常可抛)。

`skein doctor` 加了一条体检: 若 `config.yaml` 配了 `hooks.agent.*` 但 `.skein/spec/.audit-log`
里从未出现过 `action=agent-hook` 的记录, 报警告 (⚠, 不影响 exit code):

```
⚠ 配了 hooks.agent.* 但 .audit-log 从未出现 action=agent-hook — agent 钩子疑似从未触发
  (agent-start/agent-stop 靠 agent 自己在工作流里调, 漏跑不报错)
```

审计行格式 (`_write_audit`): `iso_ts|agent-hook|agent.<name>|<when>->(N hooks)|tid=<tid> sid=<sid>`,
只在钩子**真正被执行**时才写 (无匹配钩子的 no-op 不写), 所以这条检查是「agent 钩子是否曾真实生效」
的唯一发现手段。

## 零开销路径

`hooks` 键缺失或非 dict 时: `hooklib._run_hooks` 探一次 `ctx["hooks"]` 是否为空列表, 是则立即
返回, 不解析深层结构、不构造 env dict、不 `fork` 子进程。`agent-start`/`agent-stop` 同理 —— 无
配置时是 no-op, 不给 agent 增加实质负担。
