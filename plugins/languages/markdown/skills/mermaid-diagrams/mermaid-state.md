---
name: mermaid-state
description: Mermaid 状态图语法规范，包括状态定义、转换、复合状态、选择和并发等完整语法
---

# Mermaid 状态图 (State Diagram)

状态图用于描述系统行为，展示状态之间的转换和事件驱动的流程。

## 基本语法

```mermaid
stateDiagram-v2
    [*] --> Still
    Still --> [*]
    Still --> Moving
    Moving --> Still
    Moving --> Crash
    Crash --> [*]
```

## 状态定义

### 简单状态

```mermaid
stateDiagram-v2
    stateId
```

### 带描述的状态

```mermaid
stateDiagram-v2
    state "这是状态描述" as s1
    s2 : 另一种描述方式
```

### 起始和终止状态

```mermaid
stateDiagram-v2
    [*] --> Active
    Active --> [*]
```

## 状态转换

### 基本转换

```mermaid
stateDiagram-v2
    s1 --> s2
```

### 带标签的转换

```mermaid
stateDiagram-v2
    s1 --> s2: 转换条件
```

### 转换语法

```
<源状态> --> <目标状态> : <转换标签>
```

## 复合状态

### 定义复合状态

```mermaid
stateDiagram-v2
    [*] --> First
    state First {
        [*] --> second
        second --> [*]
    }
```

### 多层嵌套

```mermaid
stateDiagram-v2
    [*] --> First
    state First {
        [*] --> Second
        state Second {
            [*] --> third
            third --> [*]
        }
    }
```

### 复合状态间转换

```mermaid
stateDiagram-v2
    [*] --> First
    First --> Second
    state First {
        [*] --> fir
        fir --> [*]
    }
    state Second {
        [*] --> sec
        sec --> [*]
    }
```

## 选择节点

```mermaid
stateDiagram-v2
    state if_state <<choice>>
    [*] --> IsPositive
    IsPositive --> if_state
    if_state --> False: if n < 0
    if_state --> True: if n >= 0
```

## 分支与合并

### Fork 分支

```mermaid
stateDiagram-v2
    state fork_state <<fork>>
    [*] --> fork_state
    fork_state --> State2
    fork_state --> State3
```

### Join 合并

```mermaid
stateDiagram-v2
    state join_state <<join>>
    State2 --> join_state
    State3 --> join_state
    join_state --> State4
```

### 完整示例

```mermaid
stateDiagram-v2
    state fork_state <<fork>>
    [*] --> fork_state
    fork_state --> State2
    fork_state --> State3

    state join_state <<join>>
    State2 --> join_state
    State3 --> join_state
    join_state --> State4
    State4 --> [*]
```

## 并发状态

```mermaid
stateDiagram-v2
    [*] --> Active

    state Active {
        [*] --> NumLockOff
        NumLockOff --> NumLockOn: EvNumLockPressed
        NumLockOn --> NumLockOff: EvNumLockPressed
        --
        [*] --> CapsLockOff
        CapsLockOff --> CapsLockOn: EvCapsLockPressed
        CapsLockOn --> CapsLockOff: EvCapsLockPressed
        --
        [*] --> ScrollLockOff
        ScrollLockOff --> ScrollLockOn: EvScrollLockPressed
        ScrollLockOn --> ScrollLockOff: EvScrollLockPressed
    }
```

使用 `--` 分隔并发区域。

## 注解

```mermaid
stateDiagram-v2
    State1: 带注解的状态
    note right of State1
        重要信息！
        可以写多行注解。
    end note
    State1 --> State2
    note left of State2: 左侧注解
```

### 跨状态注解

```mermaid
stateDiagram-v2
    State1 --> State2
    note over State1, State2: 跨状态注解
```

## 方向设置

```mermaid
stateDiagram-v2
    direction LR
    [*] --> A
    A --> B
    B --> C
```

方向选项：
- `TB` - 从上到下
- `BT` - 从下到上
- `LR` - 从左到右
- `RL` - 从右到左

## 注释

```mermaid
stateDiagram-v2
    [*] --> Still
    %% 这是注释
    Still --> Moving
```

## 样式

### classDef 定义

```mermaid
stateDiagram-v2
    classDef notMoving fill:white
    classDef movement font-style:italic
    classDef badEvent fill:#f00,color:white

    [*] --> Still
    Still --> Moving
    Moving --> Crash
    Crash --> [*]

    class Still notMoving
    class Moving movement
    class Crash badEvent
```

### ::: 运算符

```mermaid
stateDiagram-v2
    classDef highlight fill:#f96

    [*] --> Still:::highlight
    Still --> [*]
```

### 样式属性

| 属性 | 说明 |
| --- | --- | --- |
| `fill` | 填充颜色 |
| `stroke` | 边框颜色 |
| `color` | 文字颜色 |
| `font-style` | 字体样式 |
| `font-weight` | 字体粗细 |
| `stroke-width` | 边框宽度 |

## 空格处理

```mermaid
stateDiagram-v2
    yswsii: 带空格的状态名称
    [*] --> yswsii
    yswsii --> AnotherState
```

## 最佳实践

### 命名规范

- 状态名称使用 PascalCase
- 转换标签使用动词短语
- 注解简洁明了

### 设计建议

- 控制状态数量（建议 ≤ 20）
- 合理使用复合状态分组
- 使用注解补充说明

### 示例：订单状态

```mermaid
stateDiagram-v2
    direction TB

    [*] --> Pending
    Pending --> Confirmed: 支付成功
    Pending --> Cancelled: 取消订单

    state Confirmed {
        [*] --> Processing
        Processing --> Shipped: 发货
        Shipped --> Delivered: 签收
    }

    Confirmed --> Completed: 交易完成
    Confirmed --> Refunded: 申请退款

    Completed --> [*]
    Cancelled --> [*]
    Refunded --> [*]

    note right of Pending: 等待支付
    note right of Confirmed: 订单处理中
```

## 参考链接

- [Mermaid 官方文档 - State Diagram](https://mermaid.js.org/syntax/stateDiagram.html)
