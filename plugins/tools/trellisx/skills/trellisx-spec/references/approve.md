# Spec 审批 (阶段 3)

强制走 `AskUserQuestion` 工具。**不接受**纯文本"可以"/"OK"。用户未明确批准 → 立即停。

## 问句模板

### 单一批准 (变更 ≤ 3 项)

```
question: "以下 N 项 spec 变更是否批准?"
options:
  - label: "全部批准"
    description: "立即执行所有变更"
  - label: "取消"
    description: "不做任何改动"
```

### 选择性批准 (变更 ≥ 4 项)

```
question: "N 项 spec 变更如下, 如何处理?"
options:
  - label: "全部批准"
    description: "执行全部 N 项"
  - label: "按编号选择"
    description: "我会列编号让你选具体哪些"
  - label: "取消"
    description: "不做任何改动"
```

若用户选"按编号选择", 再发一个 multiSelect = true 的 AskUserQuestion:

```
question: "选择要执行的变更 (可多选):"
multiSelect: true
options:
  - label: "#1 REWRITE guides/code-reuse-thinking-guide.md"
    description: "5 条 MUST 替代描述式"
  - label: "#2 DELETE guides/legacy-x.md"
    description: "0 引用 + 内容过时"
  - label: "#3 MERGE cross-layer + code-reuse → core-contracts.md"
    description: "去除重复, 合并为单文件"
  ...
```

## 高风险变更必须二次确认

满足任一即需追加一个"确认破坏"问句:

- 删除被 ≥ 1 task manifest 引用的文件
- 重写涉及 ≥ 100 行的文件
- 删除整个目录
- supersedes 链中已有 ≥ 2 个旧文件

```
question: "变更 #X 高风险 (<原因>), 仍然执行?"
options:
  - label: "是, 继续"
    description: "我已知风险, 继续执行"
  - label: "否, 跳过此项"
    description: "本项不做, 其他正常"
```

## 编号映射表

发问句前主会话先展示一次编号 ↔ 变更映射 (人类可读):

```
#1 [REWRITE] guides/code-reuse-thinking-guide.md
    旧: "建议在重用前考虑..." (35% 命令式)
    新: 5 条 MUST 清单 (100% 命令式)
    影响: 被 2 task 引用 — task-a, task-b

#2 [DELETE] guides/legacy-x.md
    理由: 0 引用 + 内容过时

#3 [MERGE] cross-layer-thinking-guide.md + code-reuse-thinking-guide.md → core-contracts.md
    理由: 80% 内容重复
    影响: 7 task manifest 引用需更新
```

## 拒绝路径

| 用户选 | 行动 |
| --- | --- |
| 全部批准 | 进入阶段 4 全量执行 |
| 按编号选择 + 多选 | 进入阶段 4 仅执行选中项 |
| 取消 / 否 | 立即停, 报告"0 变更" |
| 用户给文本反馈但未走选项 | 重新发 AskUserQuestion, **不**按文本自行决定 |

## 实施约束

- AskUserQuestion 不可并发, 一次只问一个问题
- 单问句 ≤ 4 选项 ("Other" 由工具自动加)
- 编号映射表附在问题文字之前, 不放进选项 description (description 太长会截断)
- 用户驳回不重提相同提案; 若想改方案 → 回阶段 2 重新出提案再问

## 写盘前最后检查

用户批准后, 阶段 4 写盘前必须最后跑一次:

```bash
git status .trellis/spec/  # 必须 clean, 否则其他人或 hook 正在改 spec, 等
```

非 clean → 报告"spec 目录有未提交改动, 等清干净再执行", 不写盘。
