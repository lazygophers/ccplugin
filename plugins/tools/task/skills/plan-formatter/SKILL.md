---
description: 计划文档格式化规范 - 将JSON转换为标准Markdown
model: haiku
context: fork
user-invocable: false
---

# Skills(task:plan-formatter) - 计划文档格式化规范

<scope>

将 planner 的 JSON 输出转换为标准 Markdown 计划文档。**强制使用**：所有生成计划文档必须通过此 skill，禁止直接拼接 Markdown。

</scope>

<template_reference>

模板：[template.md](template.md)。约束：Mermaid 单行文本(禁止`\n`)、状态≤20字符、表格必须完整、frontmatter 必须完整。

</template_reference>

<invocation>

**模式 1（推荐）：直接写文件**

调用：`Agent(agent="task:plan-formatter", prompt="将JSON转为Markdown计划文档：\n{planner_result_json}\nfrontmatter：{frontmatter}\n要求：1.遵循template.md 2.Mermaid无\\n 3.完整任务表格\n文件路径：{plan_md_path}\n直接写入文件并返回元数据。")`

返回：`{status, file_path, summary, task_count, estimated_duration}`

**模式 2：返回文本**（小型计划/测试用）

同上但不指定文件路径，返回完整 Markdown 文本，调用方自行 `Write(plan_md_path, result)`

**禁止**直接拼接 Markdown 字符串。默认使用模式 1。

</invocation>

<references>

- [标准模板](template.md)

</references>
