---
name: plugin-review
description: Claude Code 插件代码审查技能。当审查插件代码、检查 plugin.json 格式、验证目录结构、检查命名规范或评估插件质量时自动激活。提供完整的插件审查清单和质量标准。
auto-activate: always:true
allowed-tools: Read, Grep, Glob, Bash, TodoWrite
---

# Claude Code 插件审查

## 审查清单

### 1. plugin.json 审查（P0）

**必需字段**：
- [ ] `name` 存在且符合 kebab-case 规范
- [ ] `description` 清晰描述插件用途
- [ ] 格式正确（JSON 语法无误）

**推荐字段**：
- [ ] `version` 遵循语义化版本
- [ ] `author` 包含 name/email/url
- [ ] `keywords` 便于插件发现
- [ ] `homepage` 和 `repository` 链接

**路径配置**：
- [ ] `commands`、`agents`、`skills` 路径正确
- [ ] 相对路径使用 `./` 前缀

### 2. 目录结构审查（P0）

**强制结构**：
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json         # 必需
├── commands/               # 根目录，非 .claude-plugin 内
├── agents/                 # 根目录，非 .claude-plugin 内
├── skills/                 # 根目录，非 .claude-plugin 内
│   └── skill-name/
│       └── SKILL.md        # 大写
└── README.md               # 推荐
```

**检查要点**：
- [ ] `.claude-plugin/plugin.json` 存在
- [ ] `commands/`、`agents/`、`skills/` 在根目录
- [ ] 没有 `commands/`、`agents/`、`skills/` 在 `.claude-plugin/` 内
- [ ] skills 中的文件名为 `SKILL.md`（大写）

### 3. Skills 审查（P0）

**SKILL.md 格式**：
```yaml
---
name: skill-name
description: 清晰描述
auto-activate: always:true  # 如需自动激活
allowed-tools: Read, Grep   # 如需限制工具
model: sonnet               # 如需指定模型
---
```

**检查要点**：
- [ ] 每个 skill 有 `SKILL.md`（大写）
- [ ] frontmatter 包含 `name` 和 `description`
- [ ] `name` 使用小写、数字、连字符
- [ ] `description` 清晰说明用途和使用时机
- [ ] 如需自动激活，设置 `auto-activate`
- [ ] 文档内容清晰、完整

### 4. Commands 审查（P0）

**命令格式**：
```markdown
---
description: 简洁描述
argument-hint: [args]       # 如需参数
allowed-tools: Bash(*)      # 如需限制工具
---
# 命令名称

详细指令。
```

**检查要点**：
- [ ] 每个 command 有清晰的 `description`
- [ ] 如需参数，提供 `argument-hint`
- [ ] 如限制工具，设置 `allowed-tools`
- [ ] 命令名称简洁描述性
- [ ] 文档包含使用示例

### 5. Agents 审查（P0）

**代理格式**：
```markdown
---
name: agent-name
description: 代理用途
tools: Read, Write, Bash     # 如需限制工具
model: sonnet                # 如需指定模型
permissionMode: default      # 如需特殊权限
skills: skill1, skill2       # 如需自动加载技能
---
代理系统提示词。
```

**检查要点**：
- [ ] 每个 agent 有唯一的 `name`
- [ ] `description` 清晰说明用途
- [ ] 如限制工具，设置 `tools`
- [ ] 系统提示词清晰、完整
- [ ] 配置字段格式正确

### 6. 命名规范审查（P1）

**检查要点**：
- [ ] 插件名称使用 kebab-case（如 `my-awesome-plugin`）
- [ ] 技能名称使用小写、数字、连字符（如 `code-reviewer`）
- [ ] 代理名称使用小写和连字符（如 `security-auditor`）
- [ ] 命令名称简洁描述性（如 `format-code`）
- [ ] 无下划线、驼峰命名

### 7. 文档完整性审查（P1）

**检查要点**：
- [ ] 根目录有 README.md
- [ ] README.md 包含：简介、安装、使用、示例
- [ ] 复杂插件有 CHANGELOG.md
- [ ] 有 LICENSE 文件
- [ ] 代码注释清晰（必要时）

### 8. 质量标准审查（P1）

**检查要点**：
- [ ] 功能完整，无 TODO/FIXME 占位符
- [ ] 代码遵循 DRY 原则
- [ ] 错误处理完善
- [ ] 无明显 bug 或逻辑错误
- [ ] 性能合理，无明显瓶颈

### 9. 集成审查（P2）

**检查要点**：
- [ ] 与市场其他插件兼容
- [ ] 不破坏现有功能
- [ ] 依赖合理且最小化
- [ ] 配置灵活可定制

## 审查流程

### 自动检查

使用以下命令自动检查插件：

```bash
# 检查 plugin.json 格式
cat .claude-plugin/plugin.json | jq .

# 检查目录结构
find . -type f -name "SKILL.md"
find . -type f -name "*.md" | grep -E "(commands|agents)/"

# 检查命名规范
ls -la .claude-plugin/
ls -la commands/ agents/ skills/
```

### 手动审查

1. 阅读 `plugin.json`，验证所有字段
2. 检查目录结构，确保组件位置正确
3. 审查每个 SKILL.md、命令、代理的格式
4. 验证命名规范
5. 检查文档完整性
6. 评估代码质量

### 审查报告

审查完成后生成报告：

```markdown
## 插件审查报告：plugin-name

### 通过项目
- ✅ plugin.json 格式正确
- ✅ 目录结构符合规范

### 问题列表
- ❌ skills/xxx/skill.md 应改为 SKILL.md
- ⚠️  建议添加 keywords

### 总体评估
- P0 问题：0 个
- P1 问题：1 个
- P2 问题：2 个
- 建议：修复后通过
```

## 常见问题

**Q: plugin.json 放在哪里？**
A: 放在 `.claude-plugin/plugin.json`，不是根目录。

**Q: commands/agents/skills 可以放在 .claude-plugin/ 内吗？**
A: 不可以，必须在插件根目录。

**Q: SKILL.md 必须大写吗？**
A: 是的，文件名必须是大写的 `SKILL.md`。

**Q: 如何验证插件？**
A: 使用 `/plugin install ./plugin-path` 本地安装测试。

## 质量标准

### 通过标准

- ✅ 所有 P0 项目通过
- ✅ P1 问题少于 3 个
- ✅ 无明显 bug 或安全问题

### 不通过标准

- ❌ 任何 P0 问题未解决
- ❌ plugin.json 格式错误
- ❌ 目录结构不符合规范

## 参考资源

- [官方插件规范](https://code.claude.com/docs/en/plugins.md)
- [插件市场规范](https://code.claude.com/docs/en/plugin-marketplaces.md)
- [项目 CLAUDE.md](../CLAUDE.md)
- [plugin-development skill](../.claude/skills/plugin-development/SKILL.md)
