---
name: mermaid-flowchart
description: Mermaid 流程图语法规范，包括节点形状、连接线、子图、样式和交互等完整语法
---

# Mermaid 流程图 (Flowchart)

流程图是 Mermaid 中最常用的图表类型，用于展示流程、决策和系统架构。

## 基本语法

```mermaid
flowchart TD
    Start --> Stop
```

### 图表方向

| 方向 | 关键字 | 说明 |
| --- | --- | --- |
| 从上到下 | `TB` 或 `TD` | Top-Bottom / Top-Down |
| 从下到上 | `BT` | Bottom-Top |
| 从左到右 | `LR` | Left-Right |
| 从右到左 | `RL` | Right-Left |

## 节点形状

### 基本形状

```mermaid
flowchart LR
    A[矩形]
    B(圆角矩形)
    C([体育场形])
    D[[子程序]]
    E[(数据库)]
    F((圆形))
    G>旗帜]
    H{菱形}
    I{{六边形}}
```

| 语法 | 形状 | 用途 |
| --- | --- | --- |
| `id[文字]` | 矩形 | 普通节点 |
| `id(文字)` | 圆角矩形 | 开始/结束 |
| `id([文字])` | 体育场形 | 起点/终点 |
| `id[[文字]]` | 子程序 | 子程序调用 |
| `id[(文字)]` | 圆柱形 | 数据库 |
| `id((文字))` | 圆形 | 连接点 |
| `id>文字]` | 旗帜 | 事件 |
| `id{文字}` | 菱形 | 判断条件 |
| `id{{文字}}` | 六边形 | 准备步骤 |

### 特殊形状

```mermaid
flowchart LR
    A[/平行四边形/]
    B[\平行四边形\]
    C[/梯形\]
    D[\梯形/]
```

## 连接线

### 连接线类型

```mermaid
flowchart LR
    A --> B
    C --- D
    E -.-> F
    G ==> H
    I --文字--> J
    K -.文字.-> L
    M ==文字==> N
```

| 语法 | 类型 | 说明 |
| --- | --- | --- |
| `-->` | 实线箭头 | 标准流程方向 |
| `---` | 实线无箭头 | 关联关系 |
| `-.->` | 虚线箭头 | 可选/临时流程 |
| `==>` | 粗线箭头 | 重要流程 |
| `--文字-->` | 带标签 | 流程说明 |

### 连接长度

```mermaid
flowchart LR
    A --> B --> C
    D --> E --> F --> G
```

### 多重连接

```mermaid
flowchart LR
    A --> B
    A --> C
    A --> D
```

简写：

```mermaid
flowchart LR
    A --> B & C --> D
```

## 子图

```mermaid
flowchart TB
    subgraph one [子图标题]
        a1 --> a2
    end
    subgraph two [另一个子图]
        b1 --> b2
    end
    one --> two
```

### 子图方向

```mermaid
flowchart TB
    subgraph top [顶部]
        direction TB
        subgraph nested [嵌套]
            direction LR
            a --> b
        end
    end
```

## 交互

### 点击事件

```mermaid
flowchart LR
    A --> B
    click A "https://example.com" "链接提示"
    click B call callback() "回调提示"
```

### 工具提示

```mermaid
flowchart LR
    A[悬停查看提示]
    A@{ tooltip: "这是一个提示信息" }
```

## 样式

### classDef 定义样式

```mermaid
flowchart LR
    A[普通] --> B[高亮]
    classDef highlight fill:#f96,stroke:#333,stroke-width:2px
    class B highlight
```

### 行内样式

```mermaid
flowchart LR
    A[普通]
    B[样式节点]
    B:::highlight
    classDef highlight fill:#f9f,stroke:#333,stroke-width:4px
```

### 样式属性

| 属性 | 说明 |
| --- | --- |
| `fill` | 填充颜色 |
| `stroke` | 边框颜色 |
| `stroke-width` | 边框宽度 |
| `stroke-dasharray` | 虚线样式 |
| `color` | 文字颜色 |
| `font-weight` | 字体粗细 |

## 注释

```mermaid
flowchart LR
    A --> B
    %% 这是注释，不会显示
    B --> C
```

## 最佳实践

### 命名规范

- 节点 ID 使用简洁的标识符
- 节点文字清晰描述含义
- 连接标签简洁明了

### 布局建议

- 复杂流程使用子图分组
- 控制图表宽度，避免过宽
- 使用方向参数优化布局

### 示例：完整流程图

```mermaid
flowchart TD
    A[开始] --> B{是否登录?}
    B -->|是| C[进入主页]
    B -->|否| D[登录页面]
    D --> E[输入凭证]
    E --> F{验证通过?}
    F -->|是| C
    F -->|否| G[显示错误]
    G --> D
    C --> H[结束]

    subgraph auth [认证流程]
        D
        E
        F
        G
    end

    classDef startEnd fill:#e1f5fe,stroke:#01579b
    classDef decision fill:#fff3e0,stroke:#e65100
    class A,H startEnd
    class B,F decision
```

## 参考链接

- [Mermaid 官方文档 - Flowchart](https://mermaid.js.org/syntax/flowchart.html)
