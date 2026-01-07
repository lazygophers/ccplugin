# 插件开发最佳实践

Claude Code 插件开发的最佳实践和建议。

## 目录

1. [设计原则](#设计原则)
2. [命名规范](#命名规范)
3. [代码质量](#代码质量)
4. [文档规范](#文档规范)
5. [测试策略](#测试策略)
6. [版本管理](#版本管理)
7. [性能优化](#性能优化)
8. [安全考虑](#安全考虑)

## 设计原则

### 单一职责

每个插件应该专注于一个特定领域或功能。

**好的例子**：
- `code-formatter` - 专注于代码格式化
- `git-helper` - 专注于 Git 操作
- `test-runner` - 专注于测试运行

**不好的例子**：
- `awesome-toolkit` - 包含太多不相关功能

### 清晰命名

插件、组件的名称应该清晰描述其功能。

**推荐**：
```
code-formatter          # 清楚说明是代码格式化
security-scanner        # 清楚说明是安全扫描
api-client-generator    # 清楚说明是 API 客户端生成
```

**避免**：
```
awesome-tool            # 不清楚具体功能
helper                  # 过于通用
utils                   # 过于通用
```

### 最小依赖

尽量减少外部依赖，保持插件简单。

**推荐**：
- 使用内置工具
- 避免复杂的外部脚本
- 提供可选功能

### 用户友好

设计易于使用和理解的插件。

**推荐**：
- 清晰的错误消息
- 提供使用示例
- 包含帮助文档

## 命名规范

### 插件名称

使用 **kebab-case**（小写字母和连字符）：

```
✅ my-awesome-plugin
✅ code-formatter
✅ api-client-generator

❌ MyAwesomePlugin        (PascalCase)
❌ my_awesome_plugin      (snake_case)
❌ myAwesomePlugin        (camelCase)
```

### 技能名称

使用 **小写字母、数字和连字符**：

```
✅ code-reviewer
✅ security-auditor
✅ performance-optimizer

❌ CodeReviewer
❌ code_reviewer
❌ codeReviewer
```

### 代理名称

使用 **小写字母和连字符**：

```
✅ plugin-developer
✅ marketplace-manager
✅ security-expert

❌ pluginDeveloper
❌ plugin_developer
❌ PluginDeveloper
```

### 命令名称

使用 **小写字母和连字符**，简洁描述性：

```
✅ format-code
✅ run-tests
✅ deploy-app

❌ formatTheCode
❌ format_code
❌ FormatCode
```

## 代码质量

### 清晰结构

保持目录结构清晰一致：

```
plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/
├── agents/
├── skills/
└── README.md
```

### 避免重复

遵循 DRY（Don't Repeat Yourself）原则：

**不好**：
```markdown
<!-- command1.md -->
执行命令A
执行命令B
执行命令C

<!-- command2.md -->
执行命令A
执行命令B
执行命令C
```

**好**：
```markdown
<!-- common.md -->
公共命令：A、B、C

<!-- command1.md -->
包含公共命令 + 特定操作X

<!-- command2.md -->
包含公共命令 + 特定操作Y
```

### 错误处理

提供清晰的错误消息和恢复建议：

```markdown
---
description: 执行部署
allowed-tools: Bash
---
# deploy

部署应用到服务器。

## 错误处理

如果部署失败，检查：
1. 服务器连接
2. 权限配置
3. 环境变量

## 恢复步骤
1. 检查错误日志
2. 修复问题
3. 重新部署
```

## 文档规范

### README.md

每个插件都应该有完整的 README：

```markdown
# Plugin Name

> 简短描述

## 功能
- 功能1
- 功能2

## 安装
\`\`\`bash
/plugin install plugin-name
\`\`\`

## 使用
\`\`\`bash
/command-name
\`\`\`

## 配置
说明配置选项

## 示例
提供使用示例

## 问题
常见问题解答
```

### 代码注释

只在必要时添加注释：

**需要注释**：
- 复杂逻辑
- 非显而易见的决策
- 工作原因和限制

**不需要注释**：
- 显而易见的代码
- 重复代码内容

## 测试策略

### 测试层次

1. **格式验证**
   ```bash
   /plugin-validate ./plugin-path
   ```

2. **本地测试**
   ```bash
   /plugin install ./plugin-path
   /plugin-test ./plugin-path
   ```

3. **功能测试**
   - 测试所有命令
   - 测试所有技能
   - 测试所有代理

### 测试清单

- [ ] plugin.json 格式正确
- [ ] 目录结构符合规范
- [ ] 命名规范符合
- [ ] 所有命令可执行
- [ ] 所有技能可激活
- [ ] 所有代理可调用
- [ ] 功能完整无占位符
- [ ] 文档完整

## 版本管理

### 语义化版本

使用 `MAJOR.MINOR.PATCH` 格式：

- **MAJOR**: 破坏性变更
- **MINOR**: 新功能，向后兼容
- **PATCH**: Bug 修复，向后兼容

**示例**：
```
1.0.0 → 1.0.1  # Bug 修复
1.0.1 → 1.1.0  # 新增功能
1.1.0 → 2.0.0  # 破坏性变更
```

### CHANGELOG.md

维护详细的变更日志：

```markdown
## [1.1.0] - 2025-01-06

### Added
- 新功能 X
- 新命令 Y

### Changed
- 改进功能 Z

### Fixed
- 修复 bug A
- 修复 bug B
```

### 版本升级

**升级前检查**：
- 破坏性变更是否必要
- 是否有迁移路径
- 是否更新文档

**升级后验证**：
- 功能是否正常
- 性能是否可接受
- 兼容性是否保持

## 性能优化

### 避免阻塞

避免长时间运行的阻塞操作：

**不好**：
```markdown
---
allowed-tools: Bash(*)
---
# command
执行耗时 5 分钟的操作
```

**好**：
```markdown
---
allowed-tools: Bash(async-task)
---
# command
启动异步任务，立即返回
```

### 缓存结果

缓存计算结果避免重复：

**不好**：
```markdown
每次都重新计算
```

**好**：
```markdown
检查缓存，如果存在则使用缓存
```

### 批量操作

批量处理提高效率：

**不好**：
```markdown
逐个处理文件
```

**好**：
```markdown
批量处理所有文件
```

## 安全考虑

### 输入验证

验证所有用户输入：

```markdown
## 参数验证

- 检查参数格式
- 验证参数范围
- 清理特殊字符
```

### 权限控制

使用合适的权限模式：

```markdown
---
permissionMode: default  # 询问用户
---
```

### 敏感信息

避免存储敏感信息：

**不好**：
```markdown
---
description: 使用 API 密钥
---
在 plugin.json 中存储密钥
```

**好**：
```markdown
---
description: 使用环境变量
---
从环境变量读取密钥
```

### 代码执行

谨慎执行代码：

```markdown
## 安全检查

- 验证命令来源
- 检查参数安全性
- 限制执行范围
```

## 社区最佳实践

### 贡献指南

提供清晰的贡献指南：

```markdown
## 贡献

欢迎贡献！请遵循：

1. Fork 项目
2. 创建分支
3. 提交更改
4. 创建 PR
```

### 许可证

选择合适的许可证：

- MIT: 宽松，推荐
- Apache 2.0: 专利保护
- GPL: 强制开源衍生作品

### 代码审查

进行代码审查：

- 检查代码质量
- 验证功能正确
- 确保文档完整

## 常见陷阱

### 避免过度设计

**不好**：
```
创建复杂的抽象层
过度工程化
```

**好**：
```
保持简单
直接实现
```

### 避免硬编码

**不好**：
```markdown
固定路径: /usr/local/bin
```

**好**：
```markdown
使用环境变量或配置
```

### 避免假设

**不好**：
```markdown
假设用户使用特定工具
```

**好**：
```markdown
检查工具可用性
提供备选方案
```

## 参考资源

- [plugin-development skill](../.claude/skills/plugin-development/SKILL.md)
- [plugin-review skill](../.claude/skills/plugin-review/SKILL.md)
- [官方最佳实践](https://code.claude.com/docs/en/best-practices.md)
