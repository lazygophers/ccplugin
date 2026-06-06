---
name: llms-generate
description: |
  llms.txt 生成流程 — 项目扫描策略、配置管理、文件生成步骤。
  Agent 按需 Read 子文件获取详细流程。Triggers on "生成 llms.txt", "create llms.txt",
  "llms.txt 生成", "update llms.txt".
disable-model-invocation: true
allowed-tools: Read Glob Grep
---

# llms.txt 生成

扫描项目文件，提取元数据，按 llms.txt 标准生成文件。

## 触发场景

- 用户请求生成 `llms.txt`
- 用户请求更新已有的 `llms.txt`
- 用户修改 `.llms.json` 后请求重新生成

## 生成流程

1. **检测现有配置** — 查找 `.llms.json`，有则读取作为基础
2. **扫描项目** — 识别项目类型、文档目录、配置文件（详见 scanning.md）
3. **提取元数据** — 项目名称、描述、文档/示例/可选文件列表
4. **按规范生成** — 遵循 format.md 格式规则输出 `llms.txt`
5. **保存配置** — 同步更新 `.llms.json`
6. **可选：生成变体** — `llms-ctx.txt` / `llms-ctx-full.txt`（参见 llms-spec references/ctx-variants.md）

## References（按需加载）

| 文件 | 用途 |
|---|---|
| [`references/scanning.md`](references/scanning.md) | 项目扫描策略 — 配置文件识别、文档目录发现、元数据提取 |
| [`references/config.md`](references/config.md) | `.llms.json` 配置格式 — 字段定义、链接配置、增量更新 |

## 不做

- 不验证文件合规性（由 llms-validator agent 负责）
- 不删除用户手动维护的文件
