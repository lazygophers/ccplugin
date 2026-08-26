# Ask UI JSON 协议

## QuestionSet（问题集）

使用 UTF-8 编码的 JSON。除非另有说明，此处未列出的字段一律忽略。

```json
{"schemaVersion":"1.0","sessionId":"optional-existing-session-id","projectName":"personal-workbench","sessionTitle":"个人工作台需求确认收集","sessionSummary":"收集个人工作台的目标、模块和交互需求","sessionBackground":"已有一版命令行工具，这次要把它做成可视化工作台，先定首页与首期模块。","roundNumber":1,"title":"基础需求确认","purpose":"确认工作台的核心目标","basedOnRound":null,"wake":{"mode":"manual","provider":null,"sessionRef":null,"cwd":null},"questions":[]}
```

省略时，CLI 会自动生成 `sessionId` 和 `roundNumber`。后续轮次复用同一个 `sessionId`。

上下文字段（都是选填，用于让用户理解「这是在问什么项目、为什么问」）：

| 字段 | 层级 | 省略时的行为 | 界面位置 |
|---|---|---|---|
| `projectName` | Session | 取工作目录名 | 页头徽标 |
| `sessionSummary` | Session | 显示默认提示语 | 页头副标题 |
| `sessionBackground` | Session | 整块不渲染 | 左栏「本次背景」，支持 Markdown + Mermaid |
| `purpose` | Round | 不渲染 | 左栏「第 N 轮」块 |
| `background` | Question | 不渲染 | 题卡内「背景 ·」块，支持 Markdown + Mermaid |

同一 Session 的后续轮次可以省略 Session 级字段，首轮写入的值会保留。

`sessionId` 会拼进文件路径，要求至少 3 个字符。问题和选项的 `id` 只是 JSON 内部引用键：字母或数字开头，其余可用字母、数字和 `.` `_` `-`，最长 128 个字符，`q1`、`mr` 这种短名合法；省略时自动生成。一次提交里所有不合法的 id 会一起报出来，不用逐个试。

## Question（问题）

每道题三件事：**问什么**（`text`）、**给哪些选项**（`options`）、**怎么答**（`type`）。

```json
{"id":"primary_goal","type":"single","title":"首版目标","text":"## 首版最重要的目标是什么？\n\n请选择一个**最优先验证**的方向。","background":"用户反馈最集中的一条是「打开之后不知道今天该做什么」。","required":true,"options":[{"id":"daily_focus","text":"每日聚焦","description":"集中展示今天最该处理的事项。","recommended":true,"reason":"首版先解决高频、明确的每日决策问题。"},{"id":"knowledge_hub","text":"知识聚合","description":"统一查找笔记、文档与上下文。"}]}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `type` | 是 | `single`（单选）/ `multiple`（多选）/ `text`（自由文本）。**没有默认值，漏写直接报错。** |
| `text` | 是 | 问题正文，问题本身和它的描述都写在这里。支持 Markdown + Mermaid。 |
| `title` | 否 | 左栏导航用的短标题。省略时取 `text` 的首个非空行——正文以 Markdown 标题或表格开头时，请显式写 `title`。 |
| `background` | 否 | 单独交代这题的前情。支持 Markdown + Mermaid。 |
| `required` | 否 | 默认 `true`。 |
| `showWhen` | 否 | 条件题：只有前面某题答成指定样子，这题才出现。见「条件题」。 |
| `options` | 选择题必填 | 见下。至少 2 个，`text` 类型不写。 |

### 选项

**每个选项都必须是 JSON 对象，不接受字符串。**

| 字段 | 必填 | 说明 |
|---|---|---|
| `text` | 是 | 选项文本。 |
| `id` | 否 | 省略时按序号自动生成。 |
| `description` | 否 | 选项下方的说明行，支持 Markdown（不渲染 Mermaid：一选项一张图会挤得没法比较）。 |
| `recommended` | 否 | `true` 时挂「推荐」徽标。 |
| `reason` | 否 | 推荐原因，显示在该选项下方。**只有 `recommended: true` 才能写，否则报错。** |

选择题至少要 2 个选项，脚本会直接报错 `第 X 题是选择题，至少要有两个选项` 并退出——只有一个候选的确认题改成 `type: "text"`，或者干脆在对话里问。

单选题最多认一个推荐项，多写的会被丢掉徽标。

选择题没有「其他」选项。预设之外的答案由每题的补充说明承载，所以选项只列真正互斥的几种，不要凑「其他」。

推荐标记只做视觉提示：加徽标、附一条推荐原因。**它们不会预选任何答案**——一道题只有在用户真的点过、选过或输入过之后才算已答，未作答的必填题会挡住提交。

### 单选

```json
{"id":"q1","type":"single","text":"首页结构\n\n选择一种主要组织方式。","options":[{"id":"dashboard","text":"仪表盘","description":"集中展示核心状态","recommended":true,"reason":"更适合快速查看整体状态"},{"id":"list","text":"列表","description":"按时间排下来"}]}
```

单选可以反悔：再点一次已选中的选项就清空，回到未作答状态。

### 多选

```json
{"id":"q2","type":"multiple","text":"首期模块\n\n选择首期必须具备的模块。","required":true,"minSelections":1,"maxSelections":3,"options":[{"id":"tasks","text":"任务","description":"待办与进度","recommended":true,"reason":"任务是工作台的主入口"},{"id":"notes","text":"笔记","description":"知识沉淀"}]}
```

`minSelections` 默认为 `required ? 1 : 0`，`maxSelections` 默认为选项总数。

### 自由文本

```json
{"id":"q3","type":"text","text":"成功标准\n\n描述上线后的成功标准。","required":true,"recommendedDraft":"每天可以在一个页面完成工作安排和回顾。","recommendationReason":"可直接观察和验证","multiline":true,"maxLength":2000}
```

`recommendedDraft` 填成输入框的 placeholder，`recommendationReason` 显示为一条推荐理由横幅。两者同样不会预填答案。

文本题写 `"required": false` 就是选填：留空也能提交，答案里是空字符串。可选参数、可选备注这类问题这样写，别用必填逼用户编内容。

## 条件题（分支）

`showWhen` 让一道题只在前面某题答成指定样子时才出现。用户在页面上选完，后续题**当场增量出现或消失**——只增删这几张卡，页面不重建，其余题的输入、滚动位置、已渲染的图表都不受影响。

```json
{"id":"q2","type":"text","text":"迁移窗口","showWhen":{"questionId":"q1","optionIds":["migrate"]}}
```

一个 `showWhen` 只盯**一道**题，命中任一 `optionIds` 即显示。分支树靠链式依赖搭：`q3` 依赖 `q2`、`q2` 依赖 `q1`；父题不可见时子题一并不可见。

| 触发源题型 | 可用的匹配方式 | 写法 |
|---|---|---|
| `single` / `multiple` | `optionIds` | `{"questionId":"q1","optionIds":["a","b"]}`——多选题取交集，勾中任一即命中 |
| `text` | `answered` | `{"questionId":"q1","answered":true}`——输入框非空 |
| `text` | `contains` | `{"questionId":"q1","contains":["超时","timeout"]}`——命中任一关键词，忽略大小写 |
| `text` | `matches` | `{"questionId":"q1","matches":"^ERR-\\d+$"}`——JS 正则，无 flags，要忽略大小写就写 `[Tt]` 或改用 `contains` |

硬规则，违反会在建 Session 时一次报全：

- `questionId` 只能指向**排在它前面**的题。顺序即依赖序，所以不存在环。
- 四种匹配方式**只能写一种**。
- 匹配方式要配得上被指向那道题的类型（选择题只能 `optionIds`，文本题只能另外三种）。
- `optionIds` 里的选项 id 必须真实存在。

匹配只看主回答：选择题看选中的选项，文本题看输入框。**补充说明不触发分支**——否则用户写完一句备注会突然冒出新题。

隐藏题的语义：

- 不校验 `required` / `minSelections`，隐藏的必填题挡不住提交。
- 不进 `answers.json`；它们的 id 集中列在 `hiddenQuestionIds` 里。
- 用户来回切分支时，已填的内容留在页面上，切回来不用重答，但只要提交时是隐藏的就不会提交。

## 页面的答题动线

- 打开页面、切换轮次后，视口停在**第一道未答题**上。
- 答完一道**单选**题，页面自动移到下一道未答题；多选和文本题不自动前进，用户还要继续选、继续写。
- 触发分支的单选题选完后，新出现的条件题就是下一道未答题，用户被直接送到它上面。

## 富文本：Markdown 与 Mermaid

`sessionBackground`、问题的 `text` 和 `background` 同时支持 Markdown 和 Mermaid；选项的 `description` 只支持 Markdown。

Markdown 按 GFM 渲染：标题、粗体、斜体、行内代码、代码块、有序/无序列表、链接、引用、分隔线、表格。换行按原样换行（`breaks: true`），不用为了断行补两个空格。渲染结果经 DOMPurify 净化，脚本和事件属性会被剥掉。

代码块按围栏上标注的语言高亮（` ```ts `、` ```python `、` ```sql ` 等，highlight.js 的语言名）。不标语言、或标了它不认识的名字，就保持素色。配色跟随所在底板，不会在黄色左栏里蹦出一块深色代码。

图表写成 ` ```mermaid ` 代码块嵌在文本里，其余文字照常显示：

```json
{"id":"q-flow","type":"single","text":"选哪条链路\n\n两条路线的差异：\n\n```mermaid\nflowchart TD\n  S[启动] --> D{有缓存?}\n  D -->|有| H[直接渲染]\n  D -->|无| N[下载后渲染]\n```\n\n右边那条首次会慢。","options":[{"id":"opt-a","text":"方案甲"},{"id":"opt-b","text":"方案乙"}]}
```

图表配色跟随界面的明暗主题。**渲染出来的图表和表格都可以点击放大**，进入全屏预览后可滚轮缩放、拖拽平移，`Esc` 或点击空白处关闭。

渲染组件（Mermaid 3.4MB、marked、DOMPurify、highlight.js）不进仓库：只有页面真的用到时才下载，缓存在 `~/.agents/ask-ui/vendor/`，此后所有项目共用同一份，离线可用（`ASK_UI_VENDOR_DIR` 可改缓存位置）。下载不到时正文退回纯文本显示、图表位置显示错误原因和原始图表源码，都不影响答题和提交。

## AnswerSet（答案集）

```json
{"schemaVersion":"1.0","submissionId":"submit-generated-id","sessionId":"personal-workbench-a7k2","roundNumber":1,"submittedAt":"2026-08-10T15:30:00.000Z","hiddenQuestionIds":[],"answers":[{"questionId":"q1","selectedOptionIds":["dashboard"],"customText":"","supplementaryText":"希望首页优先展示今天的任务。"},{"questionId":"q3","selectedOptionIds":[],"customText":"每天使用至少两次。","supplementaryText":""}]}
```

`answers.json` 提交后即不可变。需要更正时创建新的 Round。

`answers` 只包含提交时可见的题，条件没满足的题的 id 列在 `hiddenQuestionIds` 里——少了几条答案是分支没走到，不是用户漏答。

每个答案都包含一个可选的 `supplementaryText` 字符串，长度上限 2000 字符。它同时承担两个作用：补充上下文，以及在预设选项都不合适时直接写自由答案——所以选择题不再提供「其他」选项。

`customText` 只对文本题有效，是该题的主回答。选择题的 `customText` 非空会被判为非法。

## 状态

Session：`active`、`completed`、`cancelled`。

Round：`waiting_for_user`、`submitted`、`processed`。

## 服务生命周期

常驻服务由 `ask` 和 `create` 自动拉起，也自动退出，不需要手动管理进程：

- 只要还有任何 `active` 会话包含 `waiting_for_user` 轮次，服务一直运行。
- 全部答完后，再有 30 分钟无 HTTP 请求即退出。`ASK_UI_IDLE_TIMEOUT_MINUTES` 或 `serve --idle-timeout <分钟>` 可改这个时长。
- 数据目录被删除时立即退出。
- `complete` 和 `cancel` 会在没有任何轮次等待作答时当场停掉服务，返回值里的 `serverStopped` 表示是否真的停了。
