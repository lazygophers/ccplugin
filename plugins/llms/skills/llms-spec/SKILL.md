---
name: llms-spec
description: |
  llms.txt 规范知识库 — 文件格式、验证规则、真实案例、上下文变体、工具集成。
  Agent 按需 Read 子文件获取完整规范细节。Triggers on "llms.txt 规范", "llms.txt format",
  "llms.txt 标准", "llms.txt specification".
disable-model-invocation: true
allowed-tools: Read Glob Grep
---

# llms.txt 规范

llms.txt 是为 LLM 优化的项目文档标准，提供简洁结构化信息帮助 LLM 快速理解项目。

## 触发场景

- Agent 需要了解 llms.txt 文件格式规范
- 验证 llms.txt 是否符合标准
- 生成 llms.txt 时需要格式参考
- 查询 llms.txt 变体或工具集成

## 核心要点

- H1 标题是唯一必需部分
- blockquote 摘要提供项目概述
- H2 部分用于文件列表分组
- `## Optional` 有特殊语义（短上下文可跳过）
- 链接格式：`[name](url): description`
- 规范地址：<https://llmstxt.org/>，作者 Jeremy Howard (AnswerDotAI)

## References（按需加载）

| 文件 | 用途 |
|---|---|
| [`references/format.md`](references/format.md) | 文件格式完整规范 — 各部分规则、链接格式、顺序约束 |
| [`references/validation.md`](references/validation.md) | 验证规则清单 — 结构检查、链接校验、内容质量判定 |
| [`references/examples.md`](references/examples.md) | 真实项目案例 — FastHTML 等，含完整 llms.txt 示例 |
| [`references/ctx-variants.md`](references/ctx-variants.md) | 上下文变体 — llms-ctx.txt / llms-ctx-full.txt 格式与生成 |
| [`references/integrations.md`](references/integrations.md) | 工具与集成 — llms-txt Python 库、JS 实现、VitePress/Docusaurus 插件 |

## 不做

- 不生成文件（由 llms-generate skill 负责）
- 不修改 vault 或项目文件
- 不自动加载；这是 reference-only skill，由 agent 按需 Read，避免规范细节常驻上下文
