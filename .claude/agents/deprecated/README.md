# 已废弃的 Agents（Deprecated）

本目录包含已废弃的 8 个旧 agents，它们已被合并到新的 `plugin-dev-advisor.md`。

## 废弃原因

**2026 架构优化**：
- 旧架构职责过细（8个agents都是插件开发相关）
- 新架构统一为1个agent（plugin-dev-advisor）
- 职责更清晰，0%重叠

## 旧 Agents 列表

| 旧 Agent | 职责 | 新位置 |
|---------|------|--------|
| agent.md | Agent开发 | → plugin-dev-advisor（§ Agent 开发） |
| command.md | Command开发 | ❌ Commands已废弃（迁移到Skills） |
| hook.md | Hook开发 | → plugin-dev-advisor（§ Hook 开发） |
| lsp.md | LSP集成 | → plugin-dev-advisor（§ LSP 集成） |
| mcp.md | MCP集成 | → plugin-dev-advisor（§ MCP 集成） |
| plugin.md | 插件开发 | → plugin-dev-advisor（§ 插件结构设计） |
| script.md | Script开发 | → plugin-dev-advisor（§ Script 开发） |
| skill.md | Skill开发 | → plugin-dev-advisor（§ Skill 开发） |

## 迁移指南

### 如何使用新 Agent

**旧方式**（细分agents）：
```
用户："开发一个agent"
→ 触发 Agents(agent)
```

**新方式**（统一agent）：
```
用户："开发一个agent"
→ 触发 Agents(plugin-dev-advisor)
→ 调用 Skills(plugin-skills/plugin-agent-development)
```

### 详细内容保留位置

所有详细开发指南保留在 `.claude/skills/plugin-skills/` 目录中：

- **Agent开发** → `plugin-skills/plugin-agent-development/`
- **Skill开发** → `plugin-skills/plugin-skill-development/`
- **Hook开发** → `plugin-skills/plugin-hook-development/`
- **MCP集成** → `plugin-skills/plugin-mcp-development/`
- **LSP集成** → `plugin-skills/plugin-lsp-development/`
- **Script开发** → `plugin-skills/plugin-script-development/`
- **质量检查** → `plugin-skills/quality-check/`

## 废弃时间

- **废弃日期**：2026-03-20
- **版本**：v0.0.181

## 参考

详细的 2026 架构设计请参考：
- `.claude/architecture-analysis.md`
- `.claude/agents-architecture-design.md`
- `plugins/tools/deepresearch/`（2026架构参考）
