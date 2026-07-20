- 所有的变更都需要自动提交到暂存区

## 项目结构

本项目是 **Claude Code 插件 + skills 集合**，由两类内容组成：

### 市场插件 `plugins/tools/`

发布到 Claude Code 插件市场的正式插件，共 7 个：

- `cortex` — 记忆/认知层
- `deepresearch` — 深度研究
- `notify` — 通知
- `novelist` — 小说创作
- `skein` — 任务编排/拆分（subtask 生命周期）
- `trellisx` — 与 `skein` 并存的任务管理实现，两者分工互补
- `version` — 版本管理

### skill 开发模板 `skills/`

非市场插件，是 skill 本身的开发模板与方法论目录：

- `skill-dev/` — skill / subagent 开发方法论（流程 A 创建 / 流程 B 优化）
- `git/` — git 相关 skill 模板
- `code-quality/` — 代码质量 skill 模板
- `project/` — 项目级 skill 模板

### 顶层关键文件

- `AGENTS.md` 是指向本文件的软链接（与 `CLAUDE.md` 同源）
- `README.md` / `docs/plugin-development.md` — 概览与插件开发指南
- `pyproject.toml` + `uv.lock` — Python 3.11+ 依赖锁定（`uv` 管理）

## 代码质量检查规范

对于 commands、skills、agents、agent.md 的优化、简化，必须通过以下命令检查 AI 是否可以正确理解识别，是否符合预期：

```bash
claude -p "<待测试的内容>" --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

### 使用说明：

1. 将 `<待测试的内容>` 替换为实际的测试内容
2. 该命令会返回 AI 对内容的理解和识别结果
3. 只有当返回结果符合预期时，才认为优化/简化是有效的
4. 需要确保返回结果非空且有意义

### 适用范围：

- Commands 文件的优化
- Skills 文件的优化
- Agents 文件的优化
- agent.md 文件的优化和简化

## 相关文档

项目的详细开发规范和指导已分散到更合适的位置：

- **skill / subagent 开发方法论**：参见 `skills/skill-dev/`（流程 A 创建 / 流程 B 优化）
- **项目概览和架构**：参见 `README.md` 和 `AGENTS.md`
- **插件开发指南**：参见 `docs/plugin-development.md`
- **质量检查工具**：见上文「代码质量检查规范」章节
