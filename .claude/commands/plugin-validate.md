---
description: 验证插件结构、格式和命名规范是否符合 Claude Code 插件标准
argument-hint: [plugin-path]
allowed-tools: Bash, Read, Grep, Glob, jq
---

# plugin-validate

验证 Claude Code 插件。

## 使用方法

/plugin-validate [plugin-path]

## 参数

- `plugin-path`: 插件路径（默认为当前目录）

## 验证项目

### P0（必须通过）

1. **plugin.json 验证**
   - [ ] 文件存在：`.claude-plugin/plugin.json`
   - [ ] JSON 格式正确
   - [ ] `name` 字段存在且非空
   - [ ] `description` 字段存在且非空

2. **目录结构验证**
   - [ ] `.claude-plugin/` 目录存在
   - [ ] `commands/` 在根目录（不在 .claude-plugin 内）
   - [ ] `agents/` 在根目录（不在 .claude-plugin 内）
   - [ ] `skills/` 在根目录（不在 .claude-plugin 内）

3. **Skills 验证**
   - [ ] SKILL.md 文件名大写
   - [ ] frontmatter 包含 name 和 description
   - [ ] name 格式正确（小写、数字、连字符）

4. **命名规范验证**
   - [ ] 插件名称使用 kebab-case
   - [ ] 技能名称使用小写、数字、连字符
   - [ ] 代理名称使用小写和连字符

### P1（推荐通过）

1. **推荐字段**
   - [ ] `version` 遵循语义化版本
   - [ ] `author` 信息完整
   - [ ] `keywords` 便于发现

2. **文档完整性**
   - [ ] README.md 存在
   - [ ] CHANGELOG.md 存在
   - [ ] LICENSE 存在

## 执行流程

1. 检查 plugin.json 格式
2. 验证目录结构
3. 检查命名规范
4. 验证 skills 格式
5. 检查文档完整性
6. 生成验证报告

## 输出格式

```
## Plugin Validation Report: plugin-name

### P0 (Critical) - Must Pass
✓ plugin.json exists and is valid
✓ Directory structure is correct
✓ Skills format is correct
✓ Naming conventions followed

### P1 (Recommended) - Should Pass
⚠️  Missing: version field
⚠️  Missing: README.md

### Summary
- P0 Issues: 0
- P1 Issues: 2
- Status: PASSED (with warnings)
```

## 示例

验证当前目录的插件：

```bash
plugin-validate
```

验证指定路径的插件：

```bash
plugin-validate ./plugins/my-plugin
```

## 退出码

- 0: 所有 P0 项目通过
- 1: 有 P0 项目未通过
- 2: 验证过程出错

## 注意事项

- 确保 jq 已安装（用于 JSON 验证）
- 路径可以是相对或绝对路径
- 验证失败会给出具体原因
