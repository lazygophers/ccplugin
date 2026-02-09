---
name: command-template
description: 命令模板 - 演示 Command 的标准格式和用法
---

# Command Template

## 快速参考

| 字段 | 说明 |
|------|------|
| `name` | 命令名（小写+连字符） |
| `description` | 简短描述 |
| `arguments` | 位置参数（可选） |
| `options` | 选项参数（可选） |

## Frontmatter 完整格式

```yaml
---
name: command-name
description: 简短描述（1-2句话）

# 可选字段
arguments:
  - name: arg1
    description: 参数描述
    required: true
    enum: [val1, val2]

options:
  - name: verbose
    short: -v
    description: 详细输出
    is_flag: true

examples:
  - "/plugin command arg1"
  - "/plugin command arg1 --verbose"
---

# 命令标题

命令详细说明。

**用法**：
```
/plugin-name command-name
```
```

## 完整示例

```markdown
---
name: greet
description: 向用户发送问候
arguments:
  - name: name
    description: 要问候的用户名
    required: true
options:
  - name: formal
    short: -f
    description: 使用正式问候语
    is_flag: true
---

# 向用户发送问候

向指定用户发送问候消息。

**用法**：
```
/template greet Alice           # 简单问候
/template greet Alice --formal  # 正式问候
```
```

## 注意事项

1. **命令名使用 kebab-case**：`show-version`
2. **描述简洁明确**：1-2 句话
3. **提供使用示例**：让用户快速上手
4. **参数验证**：使用类型检查

## 相关资源

- [Commands Skill](../../.claude/skills/commands/SKILL.md)
- [scripts/main.py](../../scripts/main.py)
