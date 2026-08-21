---
name: ask-ui
description: 把 Agent 工作流中彼此独立的问题渲染成本地交互式表单，标注推荐答案，为每个问题收集可选补充说明，将回答保存为可移植 JSON，并把提交结果直接返回给等待中的 Agent 命令。适用于 grill-me、grill-with-docs、头脑风暴、需求澄清、配置、规划，以及任何需要用户确认或问题收集的工作流；当一轮包含超过两个问题时，必须显式调用 Ask UI。用户在一轮 Ask UI 进行中说「已提交」「提交好了」「答完了」时，也走本 skill 的手动恢复路径。English triggers: "ask user form", "interactive questions", "question form".
---

# Ask UI

把 Ask UI 当作展示与持久化适配器使用。问题的生成和推理仍留在调用方工作流里。

## 总览：三条路径，只走一条

| 路径 | 何时走 | 答案怎么回来 |
|---|---|---|
| **标准路径 `ask`** | 默认。后台运行，阻塞到用户提交 | 进程退出，harness 推完成通知，读 stdout 文件 |
| **故障恢复 `resume`** | 仅「故障速查」表列出的情况 | `status: "submitted"` 里就是完整答案 |
| **手动回退 `create`** | `ask` 确实用不了的最后手段 | 用户回复「已提交」后跑 `resume` |

选错路径的代价都在后文用 🔴 标出。先读总览再往下走，不要跳进某条路径的细节里出不来。

## 永不变量

无论走到哪条路径，以下红线一次都不能破：

- 🔴 绝不要求用户回复「已提交」来推进 `ask`——后台任务的完成通知就是唤醒信号。
- 🔴 绝不覆盖已提交的问题或答案——更正和补充一律开新 Round。
- 🔴 绝不用 `nohup ... &` 之类手写后台——用 harness 自己的后台机制。
- 🔴 绝不 `sleep` 轮询、催用户。
- 🔴 绝不 `tail` harness 任务输出或手拼 `.ask-ui/` 下的文件路径——读 `<run>.stdout.json`，或跑 `resume`。

## 判断是否使用 UI

🔴 **CHECKPOINT**：当前一轮包含至少两个用户当下就能回答的独立问题时，必须使用 UI。有依赖关系的问题留到后续轮次。只有一个问题时直接在对话里问；唯一的例外是更正或补充已提交的答案——哪怕只有一题也走新 Round 表单，因为对话里口头确认不落盘、不进 Round 链，后续 `basedOnRound` 轮次读不到它。

对 `grill-me`、`grill-with-docs`、头脑风暴，或其他确认与问题收集类工作流，只要一轮超过两个问题，一律使用 UI。

### 回退顺序

按顺序往下退，退到能用的第一档为止：

1. **Ask UI**（本 skill）——默认。
2. **`AskUserQuestion`**——本 skill 用不了时改用它。用不了的情形有两种：harness 没有可执行命令的工具（Bash 或等价物），或服务/浏览器确实起不动。
3. **对话里的编号文本问题**——只有在 `AskUserQuestion` 也拿不到时才允许。

退档时说清真实原因，别把「没有 Bash 工具」写成「服务起不来」——前者换任何语言重写都没用，后者才是环境问题。用 `ToolSearch` 确认过工具确实不存在，再下结论。

## 标准路径：`ask` 七步

1. 把包含本 `SKILL.md` 的目录解析为 `ASK_UI_SKILL_DIR`。
2. 创建 JSON 前先读 [references/schema.md](references/schema.md)。
3. 创建 QuestionSet JSON 文件。新任务省略 `sessionId`；后续轮次复用当前活跃的 `sessionId` 并设置 `basedOnRound`。
   一并写上上下文字段，让用户不看对话就能判断在问什么：Session 级 `projectName` / `sessionSummary` / `sessionBackground`，Round 级 `purpose`，需要单独交代前情的题写 `background`。
   选择题没有「其他」选项。预设选项之外的答案由每题的补充说明承载，所以选项只列真正互斥的几种，不要凑「其他」。选择题至少要 2 个选项，脚本会直接报错 `第 X 题是选择题，至少要有两个选项` 并退出——只有一个候选的确认题改成 `type: "text"`，或者干脆在对话里问。
   流程、时序、架构这类讲不清的东西，在 `sessionBackground` 或问题的 `description` / `background` 里写 ` ```mermaid ` 代码块，会渲染成跟随主题的图。
4. **在后台运行命令，并把 stdout 和 stderr 分开重定向到两个文件**：

   ```text
   node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs ask --input <questions.json> > <run>.stdout.json 2> <run>.stderr.log
   ```

   用 harness 的后台机制启动（Claude Code 里是 Bash 工具的 `run_in_background: true`）。

5. 🛑 **STOP：启动后立刻结束本轮，什么都不用等。**`ask` 没有超时，会一直阻塞到用户提交；用户提交后进程退出，harness 主动把任务完成通知推给你，那就是唤醒信号。
6. 收到完成通知后，直接读 `<run>.stdout.json`——它是一整行 JSON，解析后继续原工作流。stderr 文件只用于排查，正常路径不必看。
7. 若还需要更多独立问题，用同一个 `sessionId` 再次调用 `ask`，并把 `basedOnRound` 设为返回的轮次号。没有更多问题时，结束该 Session。

### 为什么必须分流重定向

后台任务的 stdout 和 stderr 会混进 harness 的同一个任务输出文件，混在一起的内容 `JSON.parse` 必然失败——这是过去要人工 `resume` 兜底的唯一原因。用 `>` 和 `2>` 分开写到两个文件后，stdout 文件就是纯净的结果 JSON，任务输出文件里只剩 `[exited with code 0]`，整条链路不再需要任何人工确认。

### 服务与浏览器生命周期

- 每一轮都会打开浏览器：页面在提交后自行关闭，所以下一轮必须重新打开。同一 Session 的各轮复用常驻服务和稳定 URL。
- 常驻服务不需要手动清理：只要还有轮次等着人回答就一直跑，全部答完且 30 分钟无人访问后自行退出，数据目录被删则立即退出。`complete` 或 `cancel` 结束最后一个会话时会当场停掉它。`ASK_UI_IDLE_TIMEOUT_MINUTES` 可改这个空闲时长。
- 仅当浏览器打开由外部单独管理时才用 `--no-open`。仅当必须固定 localhost 端口时才用 `--port <number>`。

## 故障速查：出什么事，做什么

```text
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs resume --session <sessionId>
```

🔴 只有下表列出的情况才需要 `resume`。正常路径永远是读 `<run>.stdout.json`，不要把 `resume` 当常规动作。

`sessionId` 从 stderr 文件里的 `ask-ui-session: <id>` 标记取；stderr 里还有一行 `ask-ui-submitted: <id> round <n>`，是提交完成的备用信号。`resume` 返回 `status: "submitted"` 时其中就是完整答案。

| 触发条件 | 一线修复 | 仍失败的兜底 |
|---|---|---|
| 后台任务被杀、崩溃，或退出码非 0 | 取 `sessionId` 后跑 `resume` | 跑不带 `--session` 的 `resume`，按话题、工作区和提交时间选会话 |
| `<run>.stdout.json` 为空或不是合法 JSON | 同上，用 `resume` 重取结果 | 会话确实不存在时据实说明答案已丢，用同一批问题开新 Session |
| 换了新的 Agent 会话，拿不到原来的后台任务 | 从对话里最近的 `ask-ui-session` 标记取 id 后 `resume` | 标记也丢了就跑不带 `--session` 的 `resume` 列候选 |
| `resume` 返回 `{"status":"waiting"}` | 用户还没提交：什么都不做，结束本轮等通知 | 🔴 不重开表单、不重发问题、不催用户 |
| 本地浏览器连不上临时服务 | 走 `create` 分离式流程（见「手动回退与恢复」） | 仍连不上才退到 `AskUserQuestion` |
| harness 没有 Bash 或等价的执行工具 | 用 `ToolSearch` 确认工具确实不存在，退到 `AskUserQuestion` | `AskUserQuestion` 也拿不到时才用对话里的编号文本问题 |
| 唤醒适配器失败 | 保住答案，回到手动「已提交」流程 | 答案已落盘，用 `resume` 重取 |

## 手动回退与恢复

🔴 **CHECKPOINT：这是最后手段，只在 `ask` 确实用不了时才走**——它是唯一需要用户回复「已提交」的路径。`ask` 在后台运行**不算**用不了，那是标准路径，按上面等通知即可。

出现以下情况时走分离式（detached）流程：前台工具调用无法保持活跃、本地浏览器连不上临时服务、或需要恢复一个被中断的直连轮次：

```text
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs create --input <questions.json>
```

解析返回的 JSON。在对话中同时给出它的 URL 和一个可见标记：

   ```text
   ask-ui-session: <sessionId>
   ```

告诉用户提交表单后只回复「已提交」。`create` 命令会启动或复用一个分离式 localhost 服务并立即返回。

当用户说「已提交」「提交好了」「答完了」时：

1. 从对话中最近一个 `ask-ui-session` 标记恢复 `sessionId`。
2. 运行：

   ```text
   node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs resume --session <sessionId>
   ```

3. 若结果为 `submitted`，用其中的问题和答案继续原工作流。
4. 若还需要更多独立问题，优先回到前台 `ask` 命令，用同一 `sessionId` 并把 `basedOnRound` 设为刚处理的轮次。只有在仍然无法直连等待时才再次使用 `create`。
5. 若没有更多问题，运行：

   ```text
   node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs complete --session <sessionId>
   ```

若对话中拿不到该标记，运行不带 `--session` 的 `resume`。返回多个候选时，依据当前话题、工作区、标题和提交时间推断最匹配的一个。只有在匹配确实无法判定时才去问用户。

🔴 重复的「已提交」消息不得创建重复轮次。只有在成功读到一个 `submitted` 轮次之后，才可以创建新轮次。

## 保持 Session 连续性

- 一个任务对应一个 Session。
- 每批问题对应一个 Round。
- 同一任务的所有轮次复用同一个 `sessionId`。
- 更正和补充确认放进新的 Round。
- 只有新任务、任务已完成、原 Session 已不可恢复、或用户明确要求重启时，才开新 Session。

## 可选的主动唤醒

Ask UI 为 Claude Code 和 Codex App Server 支持可选的唤醒元数据。把它当增强项，不是必需项。

- 只有在用户同意后才启用自动唤醒。
- Claude Code 需要一个已记录的 session id。
- Codex 需要宿主提供的 thread id。绝不猜测 Codex thread id。
- 适配器失败时，保住答案并回到手动「已提交」流程。
- 直连 `ask` 模式永远不触发唤醒适配器，因为等待中的进程本身就是返回通道。

## 反模式：这些事一次都不要做

每次准备发命令或回话之前，对照一遍。

| 🔴 不要做 | 为什么 | 改成 |
|---|---|---|
| 用 `nohup ... &` 之类手写后台 | harness 收不到退出事件，整条链路退回人工追问 | 用 harness 自己的后台机制 |
| stdout 和 stderr 合并重定向 | 两股输出混在一起，`JSON.parse` 必然失败 | `> <run>.stdout.json 2> <run>.stderr.log` |
| `sleep` 轮询、催用户、让用户回复「已提交」 | 后台任务的完成通知就是唤醒信号，等它即可 | 启动后立刻结束本轮 |
| `tail` harness 任务输出，或手拼 `.ask-ui/` 路径 | 绕过了协议，拿到的可能是半截文件 | 读 `<run>.stdout.json`，或跑 `resume` |
| 给选择题加「其他」选项 | 预设外的答案由每题的补充说明承载 | 选项只列真正互斥的几种 |
| 覆盖已提交的问题或答案 | `answers.json` 提交后不可变 | 更正和补充一律开新 Round |
| 把「没有 Bash 工具」说成「服务起不来」 | 归因错了，用户会去修一个不存在的环境问题 | 说清是工具缺失还是服务故障 |
| 猜 Codex thread id | 猜错会把唤醒发给别的会话 | thread id 只能由宿主提供，拿不到就走手动流程 |

## 常用命令

```text
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs ask --input <questions.json>    # 标准路径
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs create --input <questions.json> # 手动回退
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs resume --session <sessionId>    # 故障恢复
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs status --session <sessionId>    # 查会话状态
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs serve                           # 常驻服务（ask/create 自动管理，一般不单跑）
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs complete --session <sessionId>  # 正常结束 Session
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs cancel --session <sessionId>    # 作废 Session（问题问错了、任务取消）
node <ASK_UI_SKILL_DIR>/scripts/self-test.mjs                              # 自检，改完 skill 或排查环境时跑
```
