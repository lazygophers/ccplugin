# 命令 Frontmatter

## 标准格式

```yaml
---
name: command-name
description: 简短描述

# 可选字段
arguments: [...]
options: [...]
examples: [...]
---

# 命令标题

命令内容...
```

## 字段详解

### name（必需）

命令标识符：

```yaml
---
name: add          # ✅ 正确
name: add-task     # ✅ 正确
name: AddTask      # ❌ 大写
name: add_task     # ❌ 下划线
---
```

**要求：**
- 小写字母+连字符
- 最多 64 字符
- 唯一性（在插件内）

### description（必需）

简短描述：

```yaml
---
description: 添加新任务到项目
description: "Execute the validation script"  # 可用引号
---
```

**要求：**
- 1-2 句话
- 包含功能关键词
- 最多 1024 字符

### arguments（可选）

位置参数定义：

```yaml
---
arguments:
  - name: task
    description: 要添加的任务描述
    required: true

  - name: priority
    description: 任务优先级
    required: false
    default: medium
---
```

**参数属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | string | 参数名 |
| `description` | string | 参数描述 |
| `required` | boolean | 是否必需 |
| `default` | any | 默认值 |
| `enum` | array | 允许值 |

### options（可选）

选项参数定义：

```yaml
---
options:
  - name: verbose
    short: -v
    description: 详细输出模式
    is_flag: true

  - name: format
    short: -f
    description: 输出格式
    default: json
    enum: [json, yaml, text]
---
```

**选项属性：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | string | 长选项名 |
| `short` | string | 短选项（单个字符） |
| `description` | string | 选项描述 |
| `is_flag` | boolean | 是否为标志位 |
| `default` | any | 默认值 |
| `enum` | array | 允许值 |

### examples（可选）

使用示例：

```yaml
---
examples:
  - "/task add \"Complete feature X\""
  - "/task add \"Fix bug\" --priority high"
  - "/task add \"Update docs\" --dry-run"
---
```

## 完整示例

```yaml
---
name: greet
description: 向用户发送问候消息
arguments:
  - name: name
    description: 要问候的用户名
    required: true
  - name: times
    description: 问候次数
    required: false
    default: 1
    enum: [1, 2, 3]
options:
  - name: formal
    short: -f
    description: 使用正式问候语
    is_flag: false
    default: false
  - name: emoji
    short: -e
    description: 添加表情符号
    is_flag: true
examples:
  - "/greet Alice"
  - "/greet Bob --formal"
  - "/greet Carol -e"
---

# 向用户发送问候

向指定用户发送一条或多条问候消息。

## 使用说明

- `name`: 必需参数，指定要问候的用户
- `times`: 可选参数，指定问候次数（1-3次）
- `--formal` / `-f`: 使用正式问候语
- `--emoji` / `-e`: 添加表情符号

## 示例

```
/greet Alice              # 普通问候
/greet Alice --formal    # 正式问候
/greet Bob -e            # 带表情
/greet Carol 3            # 三次问候
```
```
