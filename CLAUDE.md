# CCPlugin Market - Claude Code 项目指导

## 项目概述

CCPlugin Market 是一个 Claude Code 插件市场仓库，为开发者提供高质量插件和开发模板。

## 开发规范

### 编程语言规范（强制）

**优先级**：
1. **Python（首选）** - 用于复杂逻辑、数据处理、API 调用
2. **Bash（次选）** - 用于系统操作、文件处理、快速脚本
3. **Markdown/JSON（必需）** - 用于配置和定义

**Python 执行规范（强制）**：

**⚠️ 必须使用 uv 管理和执行 Python**

- ✅ **使用 uv**：`uv run script.py` 或 `uv pip install ...`
- ❌ **禁止直接执行**：`python3 script.py` 或 `python script.py`

**原因**：
- uv 提供快速的依赖管理和虚拟环境
- 确保依赖隔离和版本一致性
- 避免全局 Python 环境污染

**正确用法**：
```bash
# 执行 Python 脚本
uv run scripts/my_script.py

# 安装依赖
uv pip install requests

# 同步依赖
uv sync
```

**错误用法**：
```bash
# ❌ 不要这样
python3 scripts/my_script.py
python scripts/my_script.py
./scripts/my_script.py
```

**语言选择原则**：
- 复杂逻辑、数据处理 → Python（使用 uv）
- 系统操作、文件处理、Hooks → Bash
- 配置文件、命令定义 → Markdown + JSON

**禁止使用**：
- 编译型语言（Go、Rust、C++等）- 除非有特殊需求并预先编译好二进制文件
- 需要复杂环境配置的语言
- 直接执行 Python（不使用 uv）

**示例**：
```python
# Python - 复杂逻辑
import sys
import json

def process_data(data):
    # 复杂处理逻辑
    return result

if __name__ == "__main__":
    process_data(sys.stdin.read())
```

```bash
#!/bin/bash
# Bash - 系统操作
for file in "$@"; do
    cp "$file" "$file.backup"
done
```

**目录结构**：
```
plugin/
├── scripts/
│   ├── process.py         # Python: 复杂逻辑
│   ├── format.sh          # Bash: 系统操作
│   └── check.sh           # Bash: 快速检查
├── commands/
│   └── my-command.md      # Markdown: 命令定义
└── .claude-plugin/
    └── plugin.json        # JSON: 配置
```

**参考文档**：
- [支持的语言](docs/supported-languages.md) - 完整语言列表
- [编译型语言指南](docs/compiled-languages-guide.md) - 如需使用编译型语言

### 插件开发规范

**强制要求**：
1. 每个插件必须有 `.claude-plugin/plugin.json` 清单文件
2. `commands/`、`agents/`、`skills/` 必须在插件根目录
3. 所有命令、代理、技能必须有清晰的描述
4. 插件名称使用 kebab-case（如 `my-awesome-plugin`）
5. 版本号遵循语义化版本规范（Semantic Versioning）

**目录结构**：
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json         # 必需：插件清单
├── commands/               # 可选：自定义命令
├── agents/                 # 可选：子代理
├── skills/                 # 可选：技能
├── hooks/                  # 可选：钩子配置
└── README.md               # 推荐：插件文档
```

### plugin.json 格式

```json
{
  "name": "plugin-name",           // 必需：kebab-case
  "version": "1.0.0",              // 推荐：语义化版本
  "description": "插件描述",        // 必需：清晰说明插件用途
  "author": {                      // 推荐：作者信息
    "name": "作者名",
    "email": "email@example.com",
    "url": "https://github.com/author"
  },
  "keywords": ["tag1", "tag2"],    // 推荐：便于发现
  "commands": "./commands/",       // 可选：命令路径
  "agents": "./agents/",           // 可选：代理路径
  "skills": "./skills/"            // 可选：技能路径
}
```

### Skills 规范

**目录结构**：
```
skills/
└── skill-name/
    └── SKILL.md          # 必需，大写
```

**SKILL.md 格式**：
```yaml
---
name: skill-name
description: 清晰描述技能用途和使用时机
auto-activate: always:true  # 可选
allowed-tools: Read, Grep   # 可选
---
# 技能名称

## 使用场景
描述何时自动激活此技能。

## 指导原则
提供详细的执行指导。
```

### Commands 规范

**格式**：
```markdown
---
description: 简洁的命令描述
argument-hint: [args]       # 可选
allowed-tools: Bash(*)      # 可选
---
# 命令名称

详细的执行指令。
```

**参数处理**：
- `$ARGUMENTS` - 捕获所有参数
- `$1`, `$2` - 位置参数

### Agents 规范

**格式**：
```markdown
---
name: agent-name
description: 代理用途描述
tools: Read, Write, Bash     # 可选
model: sonnet                # 可选
permissionMode: default      # 可选
---
代理的系统提示词和详细指令。
```

## 开发工作流

### 创建新插件

1. **复制模板**：
   ```bash
   cp -r plugins/template my-new-plugin
   ```

2. **修改 plugin.json**：
   - 更新 name、description、author
   - 添加相关 keywords

3. **实现功能**：
   - 在 `commands/` 添加自定义命令
   - 在 `agents/` 添加子代理
   - 在 `skills/` 添加技能

4. **测试插件**：
   ```bash
   /plugin install ./my-new-plugin
   ```

5. **提交市场**：
   - 在 `marketplace.json` 添加条目
   - 提交 PR

### 任务管理

使用 TodoWrite 管理开发任务：

```markdown
- [ ] 探索需求和规范
- [ ] 设计目录结构
- [ ] 实现 commands
- [ ] 实现 agents
- [ ] 实现 skills
- [ ] 编写文档
- [ ] 测试验证
```

## 质量标准

**提交前检查清单**：
- [ ] plugin.json 格式正确且完整
- [ ] 所有命令/代理/技能有清晰描述
- [ ] 遵循命名规范（kebab-case）
- [ ] 版本号符合语义化规范
- [ ] README.md 文档完整
- [ ] 在 marketplace.json 中添加条目

## 常用工具

- **codanna-cc**: 代码探索和依赖分析
- **TodoWrite**: 任务管理
- **Edit/Write**: 文件编辑（优先 Edit）

## Skills（自动激活技能）

本项目提供以下技能，开发插件时会自动激活提供指导：

### 开发技能

| 技能 | 文件 | 用途 |
|------|------|------|
| `plugin-development` | [.claude/skills/plugin-development/SKILL.md](.claude/skills/plugin-development/SKILL.md) | 插件开发指导，包含 plugin.json 格式、组件规范和最佳实践 |
| `plugin-review` | [.claude/skills/plugin-review/SKILL.md](.claude/skills/plugin-review/SKILL.md) | 插件审查指导，包含完整审查清单和质量标准 |
| `plugin-publishing` | [.claude/skills/plugin-publishing/SKILL.md](.claude/skills/plugin-publishing/SKILL.md) | 插件发布指导，包含版本管理和发布流程 |
| `plugin-testing` | [.claude/skills/plugin-testing/SKILL.md](.claude/skills/plugin-testing/SKILL.md) | 插件测试指导，包含测试策略和验证方法 |

### 管理技能

| 技能 | 文件 | 用途 |
|------|------|------|
| `marketplace-management` | [.claude/skills/marketplace-management/SKILL.md](.claude/skills/marketplace-management/SKILL.md) | 市场管理指导，包含 marketplace.json 配置和插件管理 |
| `hooks-guide` | [.claude/skills/hooks-guide/SKILL.md](.claude/skills/hooks-guide/SKILL.md) | Hooks 指导，包含事件配置和最佳实践 |

### 技能使用

这些技能会在相关开发工作中自动激活，提供：
- 规范检查和验证
- 开发指导和最佳实践
- 常见问题解答
- 参考资源链接

## Commands（项目命令）

本项目提供以下命令用于插件开发：

| 命令 | 文件 | 用途 |
|------|------|------|
| `plugin-create` | [.claude/commands/plugin-create.md](.claude/commands/plugin-create.md) | 创建新插件 |
| `plugin-validate` | [.claude/commands/plugin-validate.md](.claude/commands/plugin-validate.md) | 验证插件格式和结构 |
| `plugin-test` | [.claude/commands/plugin-test.md](.claude/commands/plugin-test.md) | 测试插件功能 |
| `marketplace-init` | [.claude/commands/marketplace-init.md](.claude/commands/marketplace-init.md) | 初始化新市场 |

## Agents（子代理）

本项目提供以下子代理用于专业任务：

| 代理 | 文件 | 用途 |
|------|------|------|
| `plugin-developer` | [.claude/agents/plugin-developer.md](.claude/agents/plugin-developer.md) | 插件开发专家，专注于开发新插件 |
| `plugin-reviewer` | [.claude/agents/plugin-reviewer.md](.claude/agents/plugin-reviewer.md) | 插件审查专家，专注于审查插件质量 |
| `marketplace-manager` | [.claude/agents/marketplace-manager.md](.claude/agents/marketplace-manager.md) | 市场管理专家，专注于维护市场配置 |

## 参考资源

### 项目文档

- [插件开发指南](docs/plugin-development.md) - 完整的插件开发教程
- [API 参考](docs/api-reference.md) - 完整的 API 参考
- [最佳实践](docs/best-practices.md) - 开发最佳实践

### 官方文档

- [插件开发](https://code.claude.com/docs/en/plugins.md) - 官方插件开发文档
- [插件市场](https://code.claude.com/docs/en/plugin-marketplaces.md) - 官方插件市场规范
- [插件参考](https://code.claude.com/docs/en/plugins-reference.md) - 官方插件 API 参考
- [Skills 指南](https://code.claude.com/docs/en/skills.md) - 官方 Skills 指南
- [斜杠命令](https://code.claude.com/docs/en/slash-commands.md) - 官方命令指南
- [子代理](https://code.claude.com/docs/en/sub-agents.md) - 官方子代理指南
- [Hooks 指南](https://code.claude.com/docs/en/hooks-guide.md) - 官方 Hooks 指南

### 项目 Skills

所有技能位于 [.claude/skills/](.claude/skills/) 目录，包含：
- [plugin-development](.claude/skills/plugin-development/SKILL.md) - 插件开发
- [plugin-review](.claude/skills/plugin-review/SKILL.md) - 插件审查
- [plugin-publishing](.claude/skills/plugin-publishing/SKILL.md) - 插件发布
- [plugin-testing](.claude/skills/plugin-testing/SKILL.md) - 插件测试
- [marketplace-management](.claude/skills/marketplace-management/SKILL.md) - 市场管理
- [hooks-guide](.claude/skills/hooks-guide/SKILL.md) - Hooks 指南
