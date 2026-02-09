# 钩子输出

## 退出代码

钩子通过退出代码表示执行结果：

| 退出代码 | 含义 | 行为 |
|----------|------|------|
| `0` | 成功 | 继续执行 |
| `2` | 阻止操作 | 阻止当前操作 |
| 其他 | 非阻塞错误 | 记录错误，继续执行 |

### 成功（退出码 0）

```bash
#!/bin/bash
# 钩子执行成功
exit 0
```

### 阻止操作（退出码 2）

```bash
#!/bin/bash
# 检测到危险操作，阻止执行
if echo "$1" | grep -q "rm -rf"; then
    echo "危险命令被阻止"
    exit 2
fi
exit 0
```

### 非阻塞错误（其他退出码）

```bash
#!/bin/bash
# 非阻塞错误，警告但继续
echo "Warning: Something went wrong"
exit 1
```

## JSON 输出

部分钩子类型支持 JSON 输出以控制行为：

```json
{
  "action": "continue"
}
```

### 决策输出格式

| 字段 | 类型 | 说明 |
|------|------|------|
| `action` | string | `continue` 或 `block` |

```json
{
  "action": "continue"
}
```

```json
{
  "action": "block",
  "reason": "Operation blocked by security check"
}
```

## 变量插值

### PreToolUse 变量

| 变量 | 说明 |
|------|------|
| `${tool_name}` | 工具名称 |
| `${pending_command}` | 待执行的 Bash 命令 |
| `${pending_path}` | Write/Read/Edit 的文件路径 |
| `${pending_content}` | 待写入的内容 |
| `${pending_content_length}` | 内容长度 |

### PostToolUse 变量

| 变量 | 说明 |
|------|------|
| `${tool_name}` | 工具名称 |
| `${status}` | 执行状态 |
| `${output}` | 工具输出 |

### Bash 脚本示例

```bash
#!/bin/bash
# 从 stdin 读取 JSON 输入
INPUT=$(cat)
EVENT=$(echo "$INPUT" | jq -r '.hook_event_name')
TOOL=$(echo "$INPUT" | jq -r '.tool_name')

echo "Event: $EVENT, Tool: $TOOL"
```

### Python 脚本示例

```python
#!/usr/bin/env python3
import json
import sys

data = json.load(sys.stdin)
event_name = data.get("hook_event_name", "")
tool_name = data.get("tool_name", "")

print(f"Event: {event_name}, Tool: {tool_name}")
