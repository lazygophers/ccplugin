---
description: 显示插件状态和配置信息
argument-hint: [verbose]
allowed-tools: Read, Bash
---

# status

显示插件状态和配置信息。

## 使用方法

/status [verbose]

## 参数

- `verbose`: 显示详细信息（可选）

## 执行步骤

1. 读取 plugin.json
2. 解析配置信息
3. 显示状态摘要
4. 如有 verbose，显示详细信息

## 输出格式

```
## Plugin Status: example-plugin

### Basic Info
- Name: example-plugin
- Version: 1.0.0
- Description: 示例插件

### Components
- Commands: 2
- Agents: 1
- Skills: 1

### Configuration
- File: .claude-plugin/plugin.json
- Status: ✓ Valid
```

## 示例

基本状态：
```bash
/status
```

详细状态：
```bash
/status verbose
```
