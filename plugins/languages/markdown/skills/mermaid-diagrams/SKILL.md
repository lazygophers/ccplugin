---
name: mermaid-diagrams
description: Mermaid 图表绘制规范，包括流程图、时序图、甘特图、类图、Git图、ER图、用户旅程图、象限图、状态图、饼图、思维导图等完整语法
---

# Mermaid 图表绘制规范

Mermaid 是基于 JavaScript 的图表绘制工具，使用文本描述生成图表，可在 Markdown 中直接渲染。

## 快速导航

| 图表类型 | 文档 | 用途 |
| --- | --- | --- |
| 流程图 | [mermaid-flowchart.md](mermaid-flowchart.md) | 流程、决策、系统架构 |
| 时序图 | [mermaid-sequence.md](mermaid-sequence.md) | 对象交互、消息传递 |
| 甘特图 | [mermaid-gantt.md](mermaid-gantt.md) | 项目进度、任务规划 |
| 类图 | [mermaid-class.md](mermaid-class.md) | 面向对象设计、类结构 |
| Git 图 | [mermaid-gitgraph.md](mermaid-gitgraph.md) | 分支策略、提交历史 |
| ER 图 | [mermaid-er.md](mermaid-er.md) | 数据库设计、实体关系 |
| 用户旅程图 | [mermaid-journey.md](mermaid-journey.md) | 用户流程、体验设计 |
| 象限图 | [mermaid-quadrant.md](mermaid-quadrant.md) | 数据分类、优先级分析 |
| 状态图 | [mermaid-state.md](mermaid-state.md) | 系统行为、状态转换 |
| 饼图 | [mermaid-pie.md](mermaid-pie.md) | 数据比例、占比分析 |
| 思维导图 | [mermaid-mindmap.md](mermaid-mindmap.md) | 知识结构、概念组织 |

## 图表选择指南

| 场景 | 推荐图表 |
| --- | --- |
| 展示业务流程 | 流程图 |
| 描述系统交互 | 时序图 |
| 规划项目进度 | 甘特图 |
| 设计类结构 | 类图 |
| 展示 Git 工作流 | Git 图 |
| 设计数据库 | ER 图 |
| 分析用户体验 | 用户旅程图 |
| 优先级决策 | 象限图 |
| 描述状态变化 | 状态图 |
| 展示数据占比 | 饼图 |
| 组织知识体系 | 思维导图 |

## 基本语法结构

所有 Mermaid 图表都使用代码块格式：

```markdown
```mermaid
图表类型
    图表内容
```
```

## 通用配置

### 主题设置

```mermaid
---
config:
  theme: dark
---
flowchart LR
    A --> B
```

可用主题：`base`、`forest`、`dark`、`default`、`neutral`

### 方向设置

适用于流程图、状态图、ER 图：

| 方向 | 关键字 |
| --- | --- |
| 从上到下 | `TB` 或 `TD` |
| 从下到上 | `BT` |
| 从左到右 | `LR` |
| 从右到左 | `RL` |

### 样式定义

```mermaid
flowchart LR
    A[普通] --> B[高亮]
    classDef highlight fill:#f96,stroke:#333,stroke-width:2px
    class B highlight
```

## 核心约定

### 强制规范

- ✅ 使用 `mermaid` 作为代码块语言标记
- ✅ 图表类型关键字放在第一行
- ✅ 节点 ID 使用简洁标识符
- ✅ 连接标签使用动词短语

### 最佳实践

- 控制图表复杂度，避免过度嵌套
- 使用子图/分组组织相关元素
- 添加必要的注解说明
- 保持图表风格一致

## 禁止行为

- ❌ 图表类型关键字拼写错误
- ❌ 节点 ID 包含特殊字符
- ❌ 过度复杂的嵌套结构
- ❌ 缺少必要的连接关系

## 参考链接

- [Mermaid 官方文档](https://mermaid.js.org/)
- [Mermaid Live Editor](https://mermaid.live/)
