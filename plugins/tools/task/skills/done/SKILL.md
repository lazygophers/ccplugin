---
description: 任务终结。所有验收通过后触发，汇总执行结果、生成完成报告、提取经验教训写入 lessons.json
memory: project
color: green
model: haiku
permissionMode: bypassPermissions
background: false
user-invocable: false
effort: low
context: fork
agent: task:done
---

# Done Skill

任务终结，总结执行结果并整理经验。

## 执行流程

### 步骤 1：收集执行结果

优先使用 flow 传入的 verify_result 和 plan 数据（避免重复读取文件）。

如果 verify_result 包含通过状态，直接复用其 evidence_summary、quality_score 和 score_breakdown。

如果是非正常完成（放弃等），从各阶段数据文件汇总（读取 index.json、align.json、task.json、context.json）。

### 步骤 2：生成完成报告

向用户输出简洁的完成报告（≤20 行），包含：

```
[flow·{task_id}·done] 任务完成

## 结果
- 目标：{task_goal}
- 状态：{成功/部分成功/失败}
- 子任务：{completed}/{total} 完成

## 变更文件
- {file_1}：{变更摘要}

## 验证
- {criteria_1}：✓ 通过

## 经验（如有）
- {lesson_1}
```

> 不重复已有的 verify 证据。

### 步骤 3：提取经验教训

从执行结果中提取非显而易见的经验，写入 `.lazygophers/lessons.json`（项目级，跨任务共享）。

只记录有价值的经验。"代码需要通过 lint" 不值得记录；"项目的 ruff 配置禁用了 E501 所以长行不算违规" 值得记录。

每条经验结构：

```json
{
  "task_id": "任务ID",
  "task_type": "bug-fix|new-feature|refactor|...",
  "outcome": "success|partial|failed",
  "timestamp": "ISO8601",
  "modules": ["涉及的模块路径"],
  "keywords": ["任务关键词，用于语义匹配"],
  "lessons": [
    {
      "category": "pattern|pitfall|toolchain|style",
      "description": "具体经验描述",
      "applies_to": "适用的模块/技术/场景"
    }
  ],
  "adjust_history": [
    {"attempt": 1, "failure_type": "test-failure", "resolution": "自动修复"}
  ]
}
```

`modules` 和 `keywords` 用于 plan 阶段检索相关经验。

简单任务无经验可提取时，跳过写入。

## 检查清单

- [ ] 执行结果已汇总（优先复用 verify 结果）
- [ ] 完成报告已按格式输出给用户
- [ ] 经验教训已按结构保存（仅非显而易见的）
- [ ] adjust_history 已记录（如有调整循环）
