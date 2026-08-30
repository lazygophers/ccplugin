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

- `git/` — git 相关 skill 模板
- `project/` — 项目级 skill 模板
- `tools/` — 交互工具 skill（`ask-ui`）

### 顶层关键文件

- `AGENTS.md` 是指向本文件的软链接（与 `CLAUDE.md` 同源）
- `README.md` / `docs/plugin-development.md` — 概览与插件开发指南
- `pyproject.toml` + `uv.lock` — Python 3.11+ 依赖锁定（`uv` 管理）

## 代码质量检查规范

对于 commands、skills、agents、agent.md 的优化、简化，必须通过以下命令检查 AI 是否可以正确理解识别，是否符合预期：

```bash
cat <待测文件> | claude -p --bare "<问题>" --output-format stream-json 2>/dev/null \
  | jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

### 使用说明：

1. 待测内容走 stdin 管道，**禁用 `claude -p "$(cat ...)"` 插值** —— YAML frontmatter 的 `---` 会被解析成 CLI 选项，报 `error: unknown option '---'`
2. `--bare` 必带 —— 否则 hook 注入劫持 prompt，或非 Anthropic 路由模型报 `API Error 400`
3. `2>/dev/null` 必带 —— 否则 stderr 的 connector 警告混进 jq，报 `Invalid numeric literal`
4. `<问题>` 问该文件的触发场景与主流程；返回需非空且切题，跑题或空返回属端点抖动，重跑而非当结论
5. predictability 验法：同一 prompt 连跑 3 次，主流程描述一致才算过
6. macOS 无 `timeout` 命令，别包 `timeout`，超时靠调用方自身机制

### 适用范围：

- Commands 文件的优化
- Skills 文件的优化
- Agents 文件的优化
- agent.md 文件的优化和简化

## Agent skills

### Issue tracker

Issues live as markdown files under `.scratch/<feature>/` in this repo; GitHub Issues is not used. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles keep their default names, recorded as a `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` at the root plus `docs/adr/`. See `docs/agents/domain.md`.

## 相关文档

项目的详细开发规范和指导已分散到更合适的位置：

- **项目概览和架构**：参见 `README.md` 和 `AGENTS.md`
- **插件开发指南**：参见 `docs/plugin-development.md`
- **质量检查工具**：见上文「代码质量检查规范」章节
