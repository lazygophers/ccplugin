---
name: mermaid
description: Mermaid 图表规范：流程图、序列图、类图、ER图等。绘制 Mermaid 图表时必须加载。
---

# Mermaid 图表规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | Markdown 格式规范 |

## 流程图

```mermaid
flowchart TD
    A[开始] --> B{判断}
    B -->|是| C[处理]
    B -->|否| D[结束]
    C --> D
```

```markdown
flowchart TD
    A[开始] --> B{判断}
    B -->|是| C[处理]
    B -->|否| D[结束]
    C --> D
```

## 序列图

```mermaid
sequenceDiagram
    participant A as 客户端
    participant B as 服务器
    A->>B: 请求
    B-->>A: 响应
```

```markdown
sequenceDiagram
    participant A as 客户端
    participant B as 服务器
    A->>B: 请求
    B-->>A: 响应
```

## 类图

```mermaid
classDiagram
    class User {
        +String name
        +String email
        +login()
    }
```

```markdown
classDiagram
    class User {
        +String name
        +String email
        +login()
    }
```

## ER 图

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    USER {
        int id
        string name
    }
    ORDER {
        int id
        string status
    }
```

## 状态图

```mermaid
stateDiagram-v2
    [*] --> 待处理
    待处理 --> 处理中
    处理中 --> 已完成
    已完成 --> [*]
```

## 检查清单

- [ ] 使用正确的图表类型
- [ ] 节点命名清晰
- [ ] 连接关系正确
- [ ] 添加必要的标签
