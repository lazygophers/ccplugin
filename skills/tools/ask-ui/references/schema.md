# Ask UI JSON 协议

## QuestionSet（问题集）

使用 UTF-8 编码的 JSON。除非另有说明，此处未列出的字段一律忽略。

```json
{
  "schemaVersion": "1.0",
  "sessionId": "optional-existing-session-id",
  "projectName": "personal-workbench",
  "sessionTitle": "个人工作台需求确认收集",
  "sessionSummary": "收集个人工作台的目标、模块和交互需求",
  "sessionBackground": "已有一版命令行工具，这次要把它做成可视化工作台，先定首页与首期模块。",
  "roundNumber": 1,
  "title": "基础需求确认",
  "purpose": "确认工作台的核心目标",
  "basedOnRound": null,
  "wake": {
    "mode": "manual",
    "provider": null,
    "sessionRef": null,
    "cwd": null
  },
  "questions": []
}
```

省略时，CLI 会自动生成 `sessionId` 和 `roundNumber`。后续轮次复用同一个 `sessionId`。

上下文字段（都是选填，用于让用户理解「这是在问什么项目、为什么问」）：

| 字段 | 层级 | 省略时的行为 | 界面位置 |
|---|---|---|---|
| `projectName` | Session | 取工作目录名 | 页头徽标 |
| `sessionSummary` | Session | 显示默认提示语 | 页头副标题 |
| `sessionBackground` | Session | 整块不渲染 | 左栏「本次背景」 |
| `purpose` | Round | 不渲染 | 左栏「第 N 轮」块 |
| `background` | Question | 不渲染 | 题卡内「背景 ·」行 |

同一 Session 的后续轮次可以省略 Session 级字段，首轮写入的值会保留。

`recommendedOptionIds`、`recommendedDraft`、`recommendationReason` 只做视觉提示——选项上加「推荐」徽标、文本题填成 placeholder、附一条推荐理由横幅。**它们不会预选任何答案**：一道题只有在用户真的点过、选过或输入过之后才算已答，未作答的必填题会挡住提交。

### 单选

```json
{
  "id": "q1",
  "type": "single",
  "title": "首页结构",
  "description": "选择一种主要组织方式。",
  "background": "现在的命令行版本只有一个列表视图，用户反馈找不到当天该做什么。",
  "required": true,
  "options": [
    {
      "id": "dashboard",
      "label": "仪表盘",
      "description": "集中展示核心状态"
    }
  ],
  "recommendedOptionIds": ["dashboard"],
  "recommendationReason": "更适合快速查看整体状态"
}
```

### 多选

```json
{
  "id": "q2",
  "type": "multiple",
  "title": "首期模块",
  "description": "选择首期必须具备的模块。",
  "required": true,
  "minSelections": 1,
  "maxSelections": 3,
  "options": [
    { "id": "tasks", "label": "任务", "description": "待办与进度" },
    { "id": "notes", "label": "笔记", "description": "知识沉淀" }
  ],
  "recommendedOptionIds": ["tasks"],
  "recommendationReason": "任务是工作台的主入口"
}
```

### 自由文本

```json
{
  "id": "q3",
  "type": "text",
  "title": "成功标准",
  "description": "描述上线后的成功标准。",
  "required": true,
  "recommendedDraft": "每天可以在一个页面完成工作安排和回顾。",
  "recommendationReason": "可直接观察和验证",
  "multiline": true,
  "maxLength": 2000
}
```

## AnswerSet（答案集）

```json
{
  "schemaVersion": "1.0",
  "submissionId": "submit-generated-id",
  "sessionId": "personal-workbench-a7k2",
  "roundNumber": 1,
  "submittedAt": "2026-08-10T15:30:00.000Z",
  "answers": [
    {
      "questionId": "q1",
      "selectedOptionIds": ["dashboard"],
      "customText": "",
      "supplementaryText": "希望首页优先展示今天的任务。"
    },
    {
      "questionId": "q3",
      "selectedOptionIds": [],
      "customText": "每天使用至少两次。",
      "supplementaryText": ""
    }
  ]
}
```

`answers.json` 提交后即不可变。需要更正时创建新的 Round。

每个答案都包含一个可选的 `supplementaryText` 字符串，长度上限 2000 字符。它同时承担两个作用：补充上下文，以及在预设选项都不合适时直接写自由答案——所以选择题不再提供「其他」选项。

`customText` 只对文本题有效，是该题的主回答。选择题的 `customText` 非空会被判为非法。

## 状态

Session：`active`、`completed`、`cancelled`。

Round：`waiting_for_user`、`submitted`、`processed`。
