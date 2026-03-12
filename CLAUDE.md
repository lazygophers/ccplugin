- 所有的变更都需要自动提交到暂存区

## 代码质量检查规范

对于 commands、skills、agents、agent.md 的优化、简化，必须通过以下命令检查 AI 是否可以正确理解识别，是否符合预期：

```bash
claude --settings ~/.claude/settings.glm-4.5-flash.json -p "<待测试的内容>" --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result' | tr -d '\n'
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

- **项目结构和开发规范**：参见 `.claude/skills/plugin-skills/`
- **项目概览和架构**：参见 `README.md` 和 `AGENTS.md`
- **插件开发指南**：参见 `docs/plugin-development.md`
- **质量检查工具**：参见 `.claude/skills/plugin-skills/quality-check/`