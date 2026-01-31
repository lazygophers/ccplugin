# Plugin Template

> 插件开发模板 - 快速创建新插件

## 编程语言规范

本市场插件开发遵循以下语言优先级：

1. **Python（首选）** - 复杂逻辑、数据处理、API 调用
2. **Bash（次选）** - 系统操作、文件处理、快速脚本
3. **Markdown/JSON（必需）** - 配置文件、命令定义

**语言选择原则**：
- 复杂逻辑、数据处理 → Python
- 系统操作、文件处理、Hooks → Bash
- 配置文件、命令定义 → Markdown + JSON

## 说明

这是一个插件开发模板，用于快速创建新的 Claude Code 插件。

## 使用方法

### 复制模板

```bash
# 复制整个模板目录
cp -r plugins/template my-new-plugin

# 进入新插件目录
cd my-new-plugin
```

### 修改配置

编辑 `.claude-plugin/plugin.json`：

```json
{
  "name": "my-new-plugin",      // 修改插件名称
  "version": "1.0.0",
  "description": "我的插件描述",  // 修改描述
  "author": {                    // 修改作者信息
    "name": "YOUR_NAME",
    "email": "your.email@example.com",
    "url": "https://github.com/yourusername"
  }
}
```

### 添加组件

#### 添加命令

在 `commands/` 目录创建 `.md` 文件：

```markdown
---
description: 命令描述
allowed-tools: Read, Write, Bash
---
# 命令名称

命令详细说明。
```

#### 添加代理

在 `agents/` 目录创建 `.md` 文件：

```markdown
---
name: agent-name
description: 代理描述
tools: Read, Write, Bash
---
代理系统提示词。
```

#### 添加技能

在 `skills/` 创建目录和 `SKILL.md`：

```markdown
---
name: skill-name-skills
description: 技能描述
auto-activate: always:true
---
# 技能名称

技能使用说明。
```

### 测试插件

```bash
# 验证插件
/plugin-validate ./my-new-plugin

# 本地安装测试
/plugin install ./my-new-plugin

# 测试功能
/plugin-test ./my-new-plugin
```

## 目录结构

```
my-new-plugin/
├── .claude-plugin/
│   └── plugin.json         # 插件清单（必需修改）
├── scripts/                # 脚本目录（可选）
│   ├── example.py          # Python 示例脚本
│   └── example.sh          # Bash 示例脚本
├── commands/               # 命令目录
├── agents/                 # 代理目录
├── skills/                 # 技能目录
└── README.md               # 插件文档（必需修改）
```

## 示例脚本

模板包含两个示例脚本供参考：

### Python 示例 (`scripts/example.py`)

```bash
# 运行示例
./scripts/example.py input.json
./scripts/example.py - < input.json
```

用于：数据处理、API 调用、复杂逻辑

### Bash 示例 (`scripts/example.sh`)

```bash
# 运行示例
./scripts/example.sh process file.txt
./scripts/example.sh check /path/to/check
./scripts/example.sh status
```

用于：系统操作、文件处理、快速脚本

可以删除或修改这些示例脚本。

## 检查清单

发布前确保：

- [ ] 修改 `plugin.json` 中的 name、description、author
- [ ] 添加至少一个命令/代理/技能
- [ ] 编写 README.md
- [ ] 本地测试通过
- [ ] 命名使用 kebab-case
- [ ] 验证格式正确

## 下一步

1. 完善插件功能
2. 添加测试
3. 编写文档
4. 发布到市场

## 参考资源

- [插件开发指南](../../docs/plugin-development.md)
- [plugin-development skill](../../.claude/skills/plugin-development/SKILL.md)
- [官方文档](https://code.claude.com/docs/en/plugins.md)
