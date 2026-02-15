---
name: mermaid-sequence
description: Mermaid 时序图语法规范，包括参与者、消息、激活框、循环、分支和并行等完整语法
---

# Mermaid 时序图 (Sequence Diagram)

时序图用于展示对象之间的交互顺序，特别适合描述系统间的消息传递流程。

## 基本语法

```mermaid
sequenceDiagram
    Alice ->> Bob: Hello
    Bob -->> Alice: Hi
```

### 消息类型

| 语法 | 类型 | 说明 |
| --- | --- | --- |
| `->` | 实线无箭头 | 同步消息 |
| `->>` | 实线箭头 | 同步请求 |
| `-->>` | 虚线箭头 | 返回消息 |
| `--x` | 虚线叉号 | 失败消息 |
| `-)` | 实线开放箭头 | 异步消息 |

## 参与者

### 定义参与者

```mermaid
sequenceDiagram
    participant A as Alice
    participant B as Bob
    A ->> B: Hello
```

### 参与者别名

```mermaid
sequenceDiagram
    participant A as 应用服务器
    participant D as 数据库
    A ->> D: 查询数据
    D -->> A: 返回结果
```

### 参与者顺序

使用 `participant` 显式声明可以控制顺序：

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant Database
```

## 激活框

### 基本用法

```mermaid
sequenceDiagram
    Alice ->> Bob: Hello
    activate Bob
    Bob -->> Alice: Hi
    deactivate Bob
```

### 简写

```mermaid
sequenceDiagram
    Alice ->>+ Bob: Hello
    Bob -->>- Alice: Hi
```

### 嵌套激活

```mermaid
sequenceDiagram
    A ->>+ B: 请求
    B ->>+ C: 转发
    C -->>- B: 响应
    B -->>- A: 返回
```

## 注解

### 添加注解

```mermaid
sequenceDiagram
    participant A
    Note over A: 这是参与者的注解
    Note right of A: 右侧注解
    Note left of A: 左侧注解
```

### 跨参与者注解

```mermaid
sequenceDiagram
    Alice ->> Bob: Hello
    Note over Alice, Bob: 双方之间的注解
```

## 循环

```mermaid
sequenceDiagram
    loop 每分钟
        Alice ->> Bob: 你好吗?
        Bob -->> Alice: 很好!
    end
```

## 条件分支

### ALT 分支

```mermaid
sequenceDiagram
    alt 成功
        Alice ->> Bob: 确认
    else 失败
        Alice ->> Bob: 取消
    end
```

### OPT 可选

```mermaid
sequenceDiagram
    opt 额外验证
        Alice ->> Bob: 验证请求
        Bob -->> Alice: 验证结果
    end
```

## 并行

```mermaid
sequenceDiagram
    par 并行操作
        Alice ->> Bob: 操作A
    and
        Alice ->> Carol: 操作B
    end
```

## 分组

### RECT 背景色

```mermaid
sequenceDiagram
    rect rgb(200, 220, 240)
        Alice ->> Bob: 请求
        Bob -->> Alice: 响应
    end
```

### 背景色带透明度

```mermaid
sequenceDiagram
    rect rgba(0, 255, 0, 0.1)
        Alice ->> Bob: 绿色背景区域
    end
```

## 延迟

```mermaid
sequenceDiagram
    Alice ->> Bob: 发送消息
    ...
    Bob -->> Alice: 延迟响应
```

## 参与者创建与销毁

```mermaid
sequenceDiagram
    participant A
    create participant B
    A ->> B: 创建
    destroy B
    A ->> B: 销毁前最后消息
```

## 链接

```mermaid
sequenceDiagram
    participant A
    link A: 文档 @ https://example.com/doc
    link A: API @ https://example.com/api
```

## 高级特性

### 自动编号

```mermaid
sequenceDiagram
    autonumber
    Alice ->> Bob: 第一条消息
    Bob -->> Alice: 第二条消息
```

### 菜单

```mermaid
sequenceDiagram
    participant A
    participant B
    A ->> B: Hello
    menu
        Option 1
        Option 2
        Option 3
    end
```

## 最佳实践

### 命名规范

- 参与者名称简洁明了
- 消息内容描述清晰
- 使用别名提高可读性

### 布局建议

- 控制参与者数量（建议 ≤ 10）
- 使用激活框表示处理时间
- 使用注解补充说明

### 示例：完整时序图

```mermaid
sequenceDiagram
    autonumber
    participant U as 用户
    participant F as 前端
    participant B as 后端
    participant D as 数据库

    U ->> F: 点击登录
    activate F
    F ->> B: POST /api/login
    activate B
    B ->> D: 查询用户
    activate D
    D -->> B: 用户信息
    deactivate D

    alt 验证成功
        B -->> F: 200 OK + Token
        F -->> U: 跳转首页
    else 验证失败
        B -->> F: 401 Unauthorized
        F -->> U: 显示错误
    end
    deactivate B
    deactivate F

    Note over U, D: 登录流程完成
```

## 参考链接

- [Mermaid 官方文档 - Sequence Diagram](https://mermaid.js.org/syntax/sequenceDiagram.html)
