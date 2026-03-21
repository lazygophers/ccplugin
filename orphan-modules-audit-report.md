# 孤儿模块审计报告

**审计时间**: 2026-03-21
**审计范围**: .claude/agents/, .claude/skills/, 所有 plugin.json
**报告版本**: v1.0

---

## 执行摘要

本次审计对比了 plugin.json 注册与实际文件，识别出 3 个未被任何插件注册的 agents 和 18 个未注册的 skills。所有模块已分类为"项目级辅助工具"或"待评估"，过期文档已移至 archive/ 目录。

### 关键发现

- **未注册 Agents**: 3 个（项目级辅助）
- **未注册 Skills**: 18 个（项目级辅助）
- **清理文档**: 2 个（已归档）
- **注册缺失**: 0 个（所有插件注册正确）

---

## 1. Agents 审计结果

### 1.1 已注册 Agents（插件内）

通过扫描所有 plugin.json，发现以下插件注册了 agents：

| 插件 | 已注册 Agents 数量 | 注册列表 |
|------|-------------------|----------|
| tools/codex | 1 | codex.md |
| tools/deepresearch | 4 | architecture-advisor.md, code-analyst.md, project-assessor.md, research-strategist.md |
| tools/task | 6 | adjuster.md, finalizer.md, plan-formatter.md, planner.md, prompt-optimizer.md, verifier.md |
| template | 1 | agent-template.md |
| languages/python | 4 | debug.md, dev.md, perf.md, test.md |
| languages/golang | 4 | debug.md, dev.md, perf.md, test.md |
| languages/typescript | 4 | debug.md, dev.md, perf.md, test.md |
| languages/rust | 4 | debug.md, dev.md, perf.md, test.md |
| languages/java | 4 | debug.md, dev.md, perf.md, test.md |
| languages/flutter | 4 | debug.md, dev.md, perf.md, test.md |
| languages/cpp | 4 | debug.md, dev.md, perf.md, test.md |
| languages/csharp | 4 | debug.md, dev.md, perf.md, test.md |
| languages/javascript | 4 | debug.md, dev.md, perf.md, test.md |
| languages/c | 4 | debug.md, dev.md, perf.md, test.md |
| novels/* | 18 | 各类小说写作辅助 agents |
| llms | 1 | llms-generator.md |

**总计**: 71 个插件内注册的 agents

### 1.2 项目级 Agents（.claude/agents/）

发现 3 个位于 `.claude/agents/` 目录的未注册 agents：

| Agent 文件 | 分类 | 说明 | 建议 |
|-----------|------|------|------|
| architect.md | 项目级辅助 | 系统架构设计专家，用于 CCPlugin 项目本身的架构审查 | 保留 |
| code-reviewer.md | 项目级辅助 | 代码审查专家，用于 CCPlugin 项目的代码质量控制 | 保留 |
| plugin-dev-advisor.md | 项目级辅助 | 插件开发顾问，用于辅助 CCPlugin 插件开发 | 保留 |

**结论**: 这 3 个 agents 是项目级辅助工具，不应注册到任何插件，保留在 `.claude/agents/` 目录。

---

## 2. Skills 审计结果

### 2.1 已注册 Skills（插件内）

通过扫描所有 plugin.json，发现以下插件注册了 skills：

| 插件 | 已注册 Skills 数量 | 注册方式 |
|------|-------------------|----------|
| languages/python | 6 | 目录注册：async, core, error, testing, types, web |
| languages/golang | 9 | 目录注册：concurrency, core, error, libs, lint, naming, structure, testing, tooling |
| languages/markdown | 2 | 目录注册：core, mermaid |
| languages/typescript | 6 | 目录注册：async, core, nodejs, react, security, types |
| languages/rust | 5 | 目录注册：async, core, macros, memory, unsafe |
| languages/java | 5 | 目录注册：concurrency, core, error, performance, spring |
| languages/flutter | 6 | 目录注册：android, core, ios, state, ui, web |
| languages/cpp | 6 | 目录注册：concurrency, core, memory, performance, template, tooling |
| languages/naming | 1 | 目录注册：core |
| languages/csharp | 6 | 目录注册：async, core, data, desktop, linq, web |
| languages/javascript | 5 | 目录注册：async, core, react, security, vue |
| languages/c | 6 | 目录注册：concurrency, core, embedded, error, memory, posix |

**总计**: 63 个插件内注册的 skills

### 2.2 项目级 Skills（.claude/skills/）

发现 18 个位于 `.claude/skills/` 目录的 SKILL.md 文件：

| Skill 路径 | 分类 | 说明 | 建议 |
|-----------|------|------|------|
| architecture-review/SKILL.md | 项目级辅助 | 系统架构审查技能，用于 CCPlugin 项目架构评审 | 保留 |
| code-review/SKILL.md | 项目级辅助 | 代码审查技能，用于 CCPlugin 项目代码质量控制 | 保留 |
| documentation/SKILL.md | 项目级辅助 | 文档生成技能，用于 CCPlugin 项目文档维护 | 保留 |
| git-workflow/SKILL.md | 项目级辅助 | Git 工作流技能，用于 CCPlugin 项目版本控制 | 保留 |
| new-plugin/SKILL.md | 项目级辅助 | 新插件创建技能，用于 CCPlugin 插件开发 | 保留 |
| performance-optimization/SKILL.md | 项目级辅助 | 性能优化技能，用于 CCPlugin 项目性能分析 | 保留 |
| plugin-skills/plugin-agent-development/SKILL.md | 项目级辅助 | Agent 开发规范，用于 CCPlugin 插件 agent 开发 | 保留 |
| plugin-skills/plugin-development/SKILL.md | 项目级辅助 | 插件开发规范，用于 CCPlugin 插件开发 | 保留 |
| plugin-skills/plugin-hook-development/SKILL.md | 项目级辅助 | Hook 开发规范，用于 CCPlugin 插件 hook 开发 | 保留 |
| plugin-skills/plugin-lsp-development/SKILL.md | 项目级辅助 | LSP 开发规范，用于 CCPlugin 插件 LSP 开发 | 保留 |
| plugin-skills/plugin-mcp-development/SKILL.md | 项目级辅助 | MCP 开发规范，用于 CCPlugin 插件 MCP 开发 | 保留 |
| plugin-skills/plugin-script-development/SKILL.md | 项目级辅助 | Script 开发规范，用于 CCPlugin 插件脚本开发 | 保留 |
| plugin-skills/plugin-skill-development/SKILL.md | 项目级辅助 | Skill 开发规范，用于 CCPlugin 插件 skill 开发 | 保留 |
| plugin-skills/quality-check/SKILL.md | 项目级辅助 | 质量检查技能，用于 CCPlugin 插件质量保证 | 保留 |
| plugin-skills/SKILL.md | 项目级辅助 | 插件技能索引，用于 CCPlugin 插件开发导航 | 保留 |
| refactoring/SKILL.md | 项目级辅助 | 重构技能，用于 CCPlugin 项目代码重构 | 保留 |
| security-audit/SKILL.md | 项目级辅助 | 安全审计技能，用于 CCPlugin 项目安全检查 | 保留 |
| testing/SKILL.md | 项目级辅助 | 测试技能，用于 CCPlugin 项目测试策略 | 保留 |

**结论**: 这 18 个 skills 是项目级辅助工具，用于 CCPlugin 项目本身的开发和维护，不应注册到任何插件，保留在 `.claude/skills/` 目录。

### 2.3 支持文档

除 SKILL.md 外，还发现以下支持文档（非 SKILL 定义）：

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| architecture-review/examples.md | 示例文档 | 架构审查示例 |
| code-review/examples.md | 示例文档 | 代码审查示例 |
| git-workflow/examples.md | 示例文档 | Git 工作流示例 |
| plugin-skills/definition.md | 规范文档 | 插件定义规范 |
| plugin-skills/local-config.md | 规范文档 | 本地配置规范 |
| plugin-skills/manifest.md | 规范文档 | 清单文件规范 |
| plugin-skills/structure.md | 规范文档 | 插件结构规范 |

这些文档为项目级 skills 提供支持，建议保留。

---

## 3. 插件注册完整性检查

### 3.1 注册一致性验证

对所有插件的 plugin.json 进行注册验证，检查是否存在以下问题：
- 注册了不存在的 agent/skill
- 存在 agent/skill 但未注册

**验证结果**: ✅ **全部通过**

所有插件的 agents 和 skills 注册均与实际文件匹配，无缺失或冗余注册。

### 3.2 特殊说明

**tools/task 插件**之前存在 `plan-formatter.md` 未注册问题，但根据 `consistency-check-report.md`（已归档），该问题应该已在后续版本中修复。当前扫描显示 plan-formatter.md 已正确注册。

---

## 4. 过期文档清理结果

### 4.1 已归档文档

以下文档已移至 `/Users/luoxin/persons/lyxamour/ccplugin/archive/task-plugin-docs/2026-03-21/`：

| 原路径 | 归档原因 | 归档位置 |
|--------|---------|---------|
| plugins/tools/task/consistency-check-report.md | 一次性审计报告，已完成使命 | archive/task-plugin-docs/2026-03-21/ |
| plugins/tools/task/docs/fix-duplicate-confirmation.md | 历史问题修复记录，功能已上线 | archive/task-plugin-docs/2026-03-21/ |

### 4.2 归档说明

这两份文档记录了 task 插件的历史问题和修复过程，具有一定的参考价值，因此移至 archive/ 而非删除。建议定期清理 archive/ 目录中 6 个月以上的文档。

---

## 5. 分类决策矩阵

### 5.1 项目级 vs 插件级判断标准

| 维度 | 项目级辅助 | 插件级注册 |
|------|-----------|-----------|
| **目标用户** | CCPlugin 项目开发团队 | Claude 终端用户 |
| **功能范围** | CCPlugin 项目开发、维护、质量控制 | 特定领域功能增强 |
| **存放位置** | `.claude/` 目录 | `plugins/*/` 目录 |
| **是否注册** | 否（全局可用） | 是（按需加载） |
| **示例** | architect, code-reviewer, plugin-dev-advisor | language agents, novel agents |

### 5.2 归档 vs 保留判断标准

| 维度 | 归档至 archive/ | 保留 |
|------|---------------|------|
| **时效性** | 一次性报告、历史记录 | 持续维护的文档 |
| **引用频率** | 低频参考 | 高频使用 |
| **实验性** | 已废弃的实验性功能 | 稳定功能 |
| **示例** | consistency-check-report.md | README.md, SKILL.md |

---

## 6. 推荐操作

### 6.1 无需操作

以下模块经审计确认为正常状态，无需调整：

1. ✅ `.claude/agents/` 的 3 个 agents - 项目级辅助工具
2. ✅ `.claude/skills/` 的 18 个 skills - 项目级辅助工具
3. ✅ 所有插件的 plugin.json 注册 - 完整且正确

### 6.2 已完成清理

以下过期文档已移至 archive/：

1. ✅ consistency-check-report.md - 一次性审计报告
2. ✅ fix-duplicate-confirmation.md - 历史问题修复记录

### 6.3 定期维护建议

1. **每季度审计**: 执行孤儿模块扫描，确保注册一致性
2. **archive/ 清理**: 每半年清理 6 个月以上的归档文档
3. **文档更新**: 及时更新 README.md 反映最新的项目结构

---

## 7. 审计工具

本次审计使用以下命令：

```bash
# 扫描所有 plugin.json
find plugins -name "plugin.json" -type f

# 提取注册的 agents 和 skills
cat plugin.json | jq -r '.agents[]?, .skills[]?'

# 扫描 .claude 目录
find .claude/agents -name "*.md"
find .claude/skills -name "SKILL.md"

# 归档过期文档
mkdir -p archive/task-plugin-docs/2026-03-21
mv consistency-check-report.md archive/task-plugin-docs/2026-03-21/
```

---

## 8. 附录

### 8.1 项目级 Agents 详情

#### architect.md
- **功能**: 系统架构设计与评审
- **使用场景**: CCPlugin 项目重大架构变更
- **依赖 Skills**: architecture-review

#### code-reviewer.md
- **功能**: 代码质量审查
- **使用场景**: CCPlugin 项目代码审查
- **依赖 Skills**: code-review

#### plugin-dev-advisor.md
- **功能**: 插件开发咨询与指导
- **使用场景**: 新插件开发、插件问题排查
- **依赖 Skills**: plugin-skills/*

### 8.2 项目级 Skills 分类

#### 开发规范类（9个）
- plugin-skills/plugin-development/SKILL.md
- plugin-skills/plugin-agent-development/SKILL.md
- plugin-skills/plugin-skill-development/SKILL.md
- plugin-skills/plugin-script-development/SKILL.md
- plugin-skills/plugin-hook-development/SKILL.md
- plugin-skills/plugin-lsp-development/SKILL.md
- plugin-skills/plugin-mcp-development/SKILL.md
- plugin-skills/quality-check/SKILL.md
- plugin-skills/SKILL.md

#### 工程实践类（6个）
- architecture-review/SKILL.md
- code-review/SKILL.md
- refactoring/SKILL.md
- testing/SKILL.md
- performance-optimization/SKILL.md
- security-audit/SKILL.md

#### 项目工具类（3个）
- documentation/SKILL.md
- git-workflow/SKILL.md
- new-plugin/SKILL.md

---

**审计执行人**: Claude Code Agent
**下次审计建议**: 2026-06-21（3个月后）
**报告存档路径**: /Users/luoxin/persons/lyxamour/ccplugin/orphan-modules-audit-report.md
