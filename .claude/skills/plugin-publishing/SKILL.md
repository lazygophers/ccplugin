---
name: plugin-publishing
description: Claude Code 插件发布技能。当需要发布插件到市场、更新 marketplace.json、版本管理或提交 PR 时自动激活。提供完整的发布流程、版本管理和清单更新指导。
auto-activate: always:true
allowed-tools: Read, Write, Edit, Bash, TodoWrite
---

# Claude Code 插件发布

## 发布流程

### 1. 发布前检查

**必查项**（P0）：
- [ ] plugin.json 格式正确且完整
- [ ] 目录结构符合规范
- [ ] 所有组件（commands/agents/skills）格式正确
- [ ] 命名规范（kebab-case）
- [ ] 功能完整，无占位符
- [ ] 本地测试通过

**推荐项**（P1）：
- [ ] README.md 文档完整
- [ ] keywords 便于发现
- [ ] CHANGELOG.md 更新
- [ ] 版本号符合语义化规范

### 2. 版本管理

**语义化版本**：`MAJOR.MINOR.PATCH`

- **MAJOR**：破坏性变更
  - 修改 plugin.json 结构
  - 删除重要功能
  - 变更命令/代理/技能接口

- **MINOR**：新功能
  - 添加新命令
  - 添加新代理
  - 添加新技能

- **PATCH**：Bug 修复
  - 修复 bug
  - 改进文档
  - 优化性能

**版本示例**：
```
1.0.0 → 1.0.1  # Bug 修复
1.0.1 → 1.1.0  # 新增功能
1.1.0 → 2.0.0  # 破坏性变更
```

### 3. 更新 marketplace.json

在 `.claude-plugin/marketplace.json` 中添加插件条目：

```json
{
  "name": "ccplugin-market",
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./plugins/plugin-name",
      "description": "插件描述",
      "version": "1.0.0",
      "author": {
        "name": "作者名"
      },
      "keywords": ["keyword1", "keyword2"]
    }
  ]
}
```

**字段说明**：
- `name`: 插件名称（kebab-case）
- `source`: 插件路径（相对路径或 GitHub 仓库）
- `description`: 简洁描述
- `version`: 当前版本号
- `author`: 作者信息
- `keywords`: 标签数组（可选）

### 4. 更新 CHANGELOG.md

```markdown
## [1.0.0] - 2025-01-06

### Added
- 初始发布
- 实现核心功能

### Changed
- 改进性能

### Fixed
- 修复 bug
```

### 5. 提交更改

```bash
# 添加所有更改
git add .

# 提交（使用规范的消息格式）
git commit -m "feat(plugin): 添加新插件 plugin-name v1.0.0"

# 推送
git push origin branch-name
```

**提交消息格式**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例**：
```
feat(plugin): 添加代码质量检查插件

- 实现代码审查命令
- 添加安全扫描代理
- 提供性能分析技能

Closes #123
```

### 6. 创建 Pull Request

**PR 标题**：
```
feat(plugin): 添加 plugin-name 插件
```

**PR 描述**：
```markdown
## 插件名称
plugin-name

## 插件描述
简要描述插件功能和用途。

## 更新内容
- 添加 plugin.json 配置
- 实现 commands/
- 实现 agents/
- 实现 skills/

## 测试
- [ ] 本地测试通过
- [ ] 格式验证通过
- [ ] 文档完整

## 相关 Issue
Closes #123

## 截图/演示
（如有）
```

## 发布检查清单

### Pre-Release（发布前）

- [ ] 代码审查通过
- [ ] 所有测试通过
- [ ] 文档完整更新
- [ ] 版本号正确更新
- [ ] CHANGELOG.md 更新
- [ ] marketplace.json 更新

### Release（发布）

- [ ] 创建 Git 标签：
  ```bash
  git tag -a v1.0.0 -m "Release plugin-name v1.0.0"
  git push origin v1.0.0
  ```

- [ ] 创建 GitHub Release
- [ ] 发布到市场

### Post-Release（发布后）

- [ ] 通知用户
- [ ] 收集反馈
- [ ] 监控问题

## 插件来源配置

### 本地路径

```json
{
  "name": "my-plugin",
  "source": "./plugins/my-plugin"
}
```

### GitHub 仓库

```json
{
  "name": "my-plugin",
  "source": {
    "source": "github",
    "repo": "username/plugin-repo"
  }
}
```

### Git 仓库

```json
{
  "name": "my-plugin",
  "source": "https://github.com/username/plugin-repo.git"
}
```

## 版本发布示例

### 初始发布（1.0.0）

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "初始版本",
  "author": {"name": "Author"}
}
```

### 补丁发布（1.0.1）

```json
{
  "name": "my-plugin",
  "version": "1.0.1",
  "description": "修复 bug",
  "author": {"name": "Author"}
}
```

### 次版本发布（1.1.0）

```json
{
  "name": "my-plugin",
  "version": "1.1.0",
  "description": "新增功能",
  "author": {"name": "Author"}
}
```

### 主版本发布（2.0.0）

```json
{
  "name": "my-plugin",
  "version": "2.0.0",
  "description": "破坏性变更",
  "author": {"name": "Author"}
}
```

## 回滚流程

如果发布后发现问题：

1. **立即回滚**：
   ```bash
   # 删除远程标签
   git push origin :refs/tags/v1.0.0

   # 删除本地标签
   git tag -d v1.0.0
   ```

2. **修复问题**：
   - 修复 bug
   - 更新版本号
   - 重新发布

3. **通知用户**：
   - 说明问题
   - 提供解决方案

## 常见问题

**Q: 如何确定版本号？**
A: 根据变更类型：破坏性→MAJOR，新功能→MINOR，修复→PATCH。

**Q: marketplace.json 放在哪里？**
A: 放在市场仓库的 `.claude-plugin/marketplace.json`。

**Q: 如何更新已发布的插件？**
A: 修改插件后，更新 marketplace.json 中的版本号，重新发布。

**Q: 删除插件怎么办？**
A: 在 marketplace.json 中移除条目，创建 PR。

## 参考资源

- [语义化版本](https://semver.org/)
- [提交消息规范](https://www.conventionalcommits.org/)
- [官方插件发布指南](https://code.claude.com/docs/en/plugin-marketplaces.md)
- [项目 CLAUDE.md](../CLAUDE.md)
