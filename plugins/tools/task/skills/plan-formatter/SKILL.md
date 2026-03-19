---
agent: task:plan-formatter
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

调用 plan-formatter agent：

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
```

**禁止操作**：
```python
# ❌ 禁止直接拼接 Markdown
markdown = f"## 任务编排\n```mermaid\n{code}\n```"
```

</invocation>

<references>

- [标准模板](template.md)
- Agent: task:plan-formatter

</references>
