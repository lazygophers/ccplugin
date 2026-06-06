# 代理系统

## llms-generator

生成或更新符合 llmstxt.org 标准的 `llms.txt` 文件。

**关联 Skills**：
- `llms-spec` — 规范知识
- `llms-generate` — 生成流程

**工作流程**：检测配置 → 扫描项目 → 生成文件 → 保存同步

**触发**：`generate llms.txt`、`create llms.txt`、`update llms.txt`

## llms-validator

验证 `llms.txt` 是否符合 llmstxt.org 标准。

**关联 Skills**：
- `llms-spec` — 规范知识（validation.md）

**工作流程**：读取文件 → 结构检查 → 链接校验 → 质量评估 → 输出报告

**触发**：`validate llms.txt`、`check llms.txt`、`验证 llms.txt`
