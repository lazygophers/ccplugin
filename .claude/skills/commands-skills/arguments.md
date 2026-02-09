# 命令参数处理

## 参数类型

### 位置参数

按顺序传递的参数：

```yaml
arguments:
  - name: name
    description: 用户名
    required: true
  - name: age
    description: 年龄
    required: false
    default: 18
```

**使用：**
```
/user add Alice 25
/user add Bob       # age 使用默认值 18
```

### 选项参数

以 `--` 或 `-` 开头的参数：

```yaml
options:
  - name: verbose
    short: -v
    description: 详细输出
    is_flag: true
  - name: format
    short: -f
    description: 输出格式
    default: json
```

**使用：**
```
/command --verbose
/command -v
/command --format yaml
/command -f yaml
```

## 参数验证

### 枚举限制

```yaml
arguments:
  - name: priority
    description: 任务优先级
    required: true
    enum: [low, medium, high, critical]

options:
  - name: level
    description: 日志级别
    required: false
    default: info
    enum: [debug, info, warn, error]
```

### 类型检查

```yaml
arguments:
  - name: count
    description: 数量（正整数）
    required: true

  - name: path
    description: 文件路径
    required: true
```

## 必填参数

### 必需参数

```yaml
arguments:
  - name: task
    description: 任务描述
    required: true
    # 必须提供，无默认值
```

### 可选参数

```yaml
arguments:
  - name: priority
    description: 优先级
    required: false
    default: medium
    # 可省略，使用默认值
```

## 特殊参数模式

### 可变参数

```yaml
arguments:
  - name: tags
    description: 标签列表
    required: false
    # 多个值用空格分隔
```

使用：
```
/task add "Task" tag1 tag2 tag3
```

### 路径参数

```yaml
arguments:
  - name: path
    description: 文件或目录路径
    required: true
```

### JSON 参数

```yaml
arguments:
  - name: data
    description: JSON 格式数据
    required: true
```

使用：
```
/api create '{"name": "test"}'
```

## 参数处理指南

1. **明确标记必填参数**
2. **提供合理的默认值**
3. **使用枚举限制取值范围**
4. **清晰的参数描述**
5. **保持参数数量适中**（建议不超过 5 个）
