# 命令定义

## 什么是命令

命令是**以 `/` 开头的可执行功能入口**，用于快速触发特定操作。

### 与 Agent/Skill 的区别

| 组件 | 用途 | 触发方式 | 特点 |
|------|------|----------|------|
| **Command** | 执行操作 | `/command` | 即时执行，有副作用 |
| **Agent** | 执行任务 | `@agent` | 自主决策，多步执行 |
| **Skill** | 行为指导 | 自动匹配 | 影响后续行为 |

## 命令使用场景

### 场景 1：任务管理

```markdown
# /task add "New task"
# /task list
# /task complete 123
```

### 场景 2：版本控制

```markdown
# /commit "feat: message"
# /push origin main
# /create-pr
```

### 场景 3：代码操作

```markdown
# /semantic search "query"
# /git ignore
# /format python
```

## 命令文件格式

### 最小格式

```yaml
---
name: command-name
description: 简短描述
---

# 命令标题

命令说明...
```

### 完整格式

```yaml
---
name: command-name
description: 简短描述（1-2句话）

arguments:
  - name: arg1
    description: 参数描述
    required: true

options:
  - name: verbose
    short: -v
    description: 详细输出
    is_flag: true

examples:
  - "/command arg1"
  - "/command arg1 --verbose"
---

# 命令标题

详细说明...

## 用法

```
/command arg1
/command arg1 --verbose
```
```

## 命令执行流程

```
1. 用户输入 /command arg
   ↓
2. 读取 commands/command.md
   ↓
3. 解析 frontmatter
   ↓
4. 提取指令内容
   ↓
5. Claude 执行指令
   ↓
6. 返回结果
```
