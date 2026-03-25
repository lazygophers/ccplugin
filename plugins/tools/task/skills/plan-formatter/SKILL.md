---
description: 计划文档格式化规范 - 将JSON转换为标准Markdown
model: haiku
context: fork
user-invocable: false
---

# Skills(task:plan-formatter) - 计划文档格式化规范

<scope>

当需要将 planner 的 JSON 输出转换为标准 Markdown 计划文档时使用此 skill。适用于 Loop 的 Planning 阶段生成计划文档、任何需要输出 .md 计划文档的场景。

**强制使用**：所有生成计划文档的地方必须通过此 skill，禁止直接拼接 Markdown 字符串。

</scope>

<template_reference>

标准模板：template.md（同目录下）

**关键约束**：
- Mermaid 图：单行文本，禁止 `\n` 换行符
- 状态描述：≤20 字符
- 表格格式：必须包含所有列
- frontmatter：必须包含所有字段

</template_reference>

<invocation>

## 模式 1：直接写文件（推荐）

**适用场景**：Loop 计划生成、大型计划（>10个任务）、需要减少 context 消耗

**优点**：
- Context 消耗减少 95-99%（从 KB 级降至 bytes 级）
- 支持大型计划（>20个任务）不会触发 context 溢出
- 简化调用代码（无需手动 Write）

```python
formatter_result = Agent(
    agent="task:plan-formatter",
    description="格式化计划为标准 Markdown 并写入文件",
    prompt=f"""将以下 JSON 转换为标准 Markdown 计划文档：

{json.dumps(planner_result, ensure_ascii=False, indent=2)}

YAML Frontmatter（必须放在文档开头）：
{frontmatter}

要求：
1. 严格遵循 template.md 格式
2. Mermaid 图单行文本，无 \\n
3. 包含完整的任务清单表格

文件路径：{plan_md_path}
请直接写入文件并返回元数据。
"""
)

# 返回格式
print(f"计划已生成：{formatter_result['file_path']}")
print(f"{formatter_result['summary']}")  # 例如："生成计划：3个任务，2个依赖关系"
```

**返回值结构**：
```json
{
  "status": "completed",
  "file_path": "/absolute/path/to/plan.md",
  "summary": "生成计划：3个任务，2个依赖关系",
  "task_count": 3,
  "estimated_duration": "2小时"
}
```

---

## 模式 2：返回文本（向后兼容）

**适用场景**：需要进一步处理文档内容、测试环境、小型计划（<5个任务）

```python
formatted_plan = Agent(
    agent="task:plan-formatter",
    prompt=f"""将以下 JSON 转换为标准 Markdown 计划文档：

{json.dumps(planner_result, ensure_ascii=False, indent=2)}

要求：
1. 严格遵循 template.md 格式
2. Mermaid 图单行文本，无 \\n
3. 包含完整的 YAML frontmatter
"""
)

# 返回完整 Markdown 文本（字符串）
Write(plan_md_path, formatted_plan)
```

---

**禁止操作**：
```python
# ❌ 禁止直接拼接 Markdown
markdown = f"## 任务编排\n```mermaid\n{code}\n```"
```

**选择建议**：
- 默认使用**模式 1**（直接写文件），除非有特殊需求
- 如果不确定，优先选择模式 1

</invocation>

<references>

- [标准模板](template.md)
- Agent: task:plan-formatter

</references>
