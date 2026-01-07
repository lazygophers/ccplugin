---
description: 测试插件功能，包括本地安装、命令执行和功能验证
argument-hint: <plugin-path>
allowed-tools: Bash, Read
---

# plugin-test

测试 Claude Code 插件。

## 使用方法

/plugin-test <plugin-path>

## 参数

- `plugin-path`: 插件路径（本地路径）

## 测试项目

### 1. 本地安装测试

```bash
# 尝试本地安装
/plugin install <plugin-path>

# 检查安装结果
/plugin list | grep <plugin-name>
```

### 2. 命令测试

```bash
# 列出可用命令
/help

# 测试每个命令
# 验证参数处理
# 验证输出格式
```

### 3. 技能测试

```bash
# 触发技能条件
# 观察技能是否激活
# 验证技能指导
```

### 4. 代理测试

```bash
# 调用代理
# 验证工具使用
# 验证执行结果
```

## 测试流程

1. **安装前准备**
   - 验证插件格式
   - 检查依赖

2. **本地安装**
   - 执行安装命令
   - 检查安装状态
   - 记录安装日志

3. **功能测试**
   - 测试所有命令
   - 测试所有技能
   - 测试所有代理

4. **卸载清理**
   - 执行卸载
   - 验证清理完成

## 输出格式

```
## Plugin Test Report: plugin-name

### Installation
✓ Plugin installed successfully
✓ No errors during installation

### Commands Test
✓ command1: PASSED
✓ command2: PASSED
⚠️  command3: PASSED (with warnings)

### Skills Test
✓ skill1: Activates correctly
✓ skill2: Provides guidance

### Agents Test
✓ agent1: Executes correctly
✓ agent2: Uses correct tools

### Summary
- Total Tests: 8
- Passed: 7
- Warnings: 1
- Failed: 0
- Status: PASSED
```

## 示例

测试本地插件：

```bash
plugin-test ./plugins/my-plugin
```

## 注意事项

- 测试会修改本地插件状态
- 测试完成后会自动卸载
- 确保没有同名插件已安装
- 记录详细日志用于调试

## 自动化测试

可以结合 CI/CD 使用：

```bash
#!/bin/bash
# 自动化测试脚本

./.claude/commands/plugin-validate ./plugins/my-plugin
./.claude/commands/plugin-test ./plugins/my-plugin
```
