---
name: ask-ui
description: 把 Agent 工作流中彼此独立的问题渲染成本地交互式表单，标注推荐答案，为每个问题收集可选补充说明，将回答保存为可移植 JSON，并把提交结果直接返回给等待中的 Agent 命令。适用于 grill-me、grill-with-docs、头脑风暴、需求澄清、配置、规划，以及任何需要用户确认或问题收集的工作流；当一轮包含超过两个问题时，必须显式调用 Ask UI。用户在一轮 Ask UI 进行中说「已提交」「提交好了」「答完了」时，也走本 skill 的手动恢复路径。
---

# Ask UI

把 Ask UI 当作展示与持久化适配器使用。问题的生成和推理仍留在调用方工作流里。

## 判断是否使用 UI

当前一轮包含至少两个用户当下就能回答的独立问题时，使用 UI。有依赖关系的问题留到后续轮次。只有一个问题时直接在对话里问。

对 `grill-me`、`grill-with-docs`、头脑风暴，或其他确认与问题收集类工作流，只要一轮超过两个问题，一律使用 UI。

若本地服务或浏览器无法启动，回退到调用方工作流的常规文本格式。

## 提问并等待回答

1. 把包含本 `SKILL.md` 的目录解析为 `ASK_UI_SKILL_DIR`。
2. 创建 JSON 前先读 [references/schema.md](references/schema.md)。
3. 创建 QuestionSet JSON 文件。新任务省略 `sessionId`；后续轮次复用当前活跃的 `sessionId` 并设置 `basedOnRound`。
   一并写上上下文字段，让用户不看对话也能判断在问什么：Session 级 `projectName` / `sessionSummary` / `sessionBackground`，Round 级 `purpose`，需要单独交代前情的题写 `background`。
   选择题没有「其他」选项。预设选项之外的答案由每题的补充说明承载，所以选项只列真正互斥的几种，不要凑「其他」。
4. 运行前台命令，并保持该工具调用一直活跃直到它退出：

   ```text
   node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs ask --input <questions.json>
   ```

5. 该命令把就绪信息、`ask-ui-session: <id>` 标记和本地 URL 写入 stderr，打开表单并等待。不要结束 Agent 轮次，也不要让用户回复「已提交」。
6. 用户提交后，解析 stdout 输出的那一个 JSON 结果，立即继续原工作流。
7. 若还需要更多独立问题，用同一个 `sessionId` 再次调用 `ask`，并把 `basedOnRound` 设为返回的轮次号。没有更多问题时，结束该 Session。

### 命令被放到后台或中断时

`ask` 会一直阻塞到用户提交，容易被 harness 转到后台。转后台之后 stdout 和 stderr 混在同一个任务输出文件里，**直接解析那个文件必然失败**。

**绝不要求用户回复「已提交」来推进 `ask`。** 用户填完表单、页面自行关闭，`ask` 进程随即退出，harness 会把后台任务完成通知推给你——那就是结果就绪的信号，不需要用户再说一遍。用户被要求汇报自己刚做完的事，是这条流程唯一不该出现的状态。

转后台后按这个顺序判断：

1. 命令还在跑 → 结束本轮，等 harness 的任务完成通知。不要 `sleep` 轮询，不要催用户。
2. 收到完成通知，或输出里出现 `ask-ui-submitted: <id> round <n>` → 结果已就绪。
3. 拿 stderr 里的 `ask-ui-session: <id>` 取结果：

   ```text
   node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs resume --session <sessionId>
   ```

`resume` 返回 `status: "submitted"` 时其中就是完整答案；返回 `{"status":"waiting"}` 说明进程还没退出，回到第 1 步继续等。不要去 `tail` 任务输出、不要手动拼 `.ask-ui/` 下的文件路径。

每一轮都会打开浏览器：页面在提交后自行关闭，所以下一轮必须重新打开。同一 Session 的各轮复用常驻服务和稳定 URL。

仅当浏览器打开由外部单独管理时才用 `--no-open`。仅当必须固定 localhost 端口时才用 `--port <number>`。

## 手动回退与恢复

这是最后手段，只在 `ask` 确实用不了时才走——它是唯一需要用户回复「已提交」的路径。`ask` 被转到后台**不算**用不了，那种情况按上一节等通知。

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

重复的「已提交」消息不得创建重复轮次。只有在成功读到一个 `submitted` 轮次之后，才可以创建新轮次。

## 保持 Session 连续性

- 一个任务对应一个 Session。
- 每批问题对应一个 Round。
- 同一任务的所有轮次复用同一个 `sessionId`。
- 绝不覆盖已提交的问题或答案。
- 更正和补充确认放进新的 Round。
- 只有新任务、任务已完成、或用户明确要求重启时，才开新 Session。

## 可选的主动唤醒

Ask UI 为 Claude Code 和 Codex App Server 支持可选的唤醒元数据。把它当增强项，不是必需项。

- 只有在用户同意后才启用自动唤醒。
- Claude Code 需要一个已记录的 session id。
- Codex 需要宿主提供的 thread id。绝不猜测 Codex thread id。
- 适配器失败时，保住答案并回到手动「已提交」流程。
- 直连 `ask` 模式永远不触发唤醒适配器，因为等待中的进程本身就是返回通道。

## 常用命令

```text
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs ask --input <questions.json>
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs create --input <questions.json>
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs status --session <sessionId>
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs serve
node <ASK_UI_SKILL_DIR>/scripts/ask-ui.mjs complete --session <sessionId>
node <ASK_UI_SKILL_DIR>/scripts/self-test.mjs
```
