---
name: mermaid-gantt
description: Mermaid 甘特图语法规范，包括任务定义、时间设置、里程碑、依赖关系和样式配置
---

# Mermaid 甘特图 (Gantt Diagram)

甘特图用于项目进度管理，展示任务的时间安排和依赖关系。

## 基本语法

```mermaid
gantt
    title 项目计划
    dateFormat YYYY-MM-DD
    section 阶段一
    任务A :a1, 2024-01-01, 7d
    任务B :after a1, 5d
```

## 日期格式

### dateFormat 设置

```mermaid
gantt
    dateFormat YYYY-MM-DD
```

### 支持的格式

| 格式 | 示例 | 说明 |
| --- | --- | --- |
| `YYYY-MM-DD` | 2024-01-15 | 标准日期 |
| `YYYY-MM-DD HH:mm` | 2024-01-15 14:30 | 带时间 |
| `YYYY/MM/DD` | 2024/01/15 | 斜杠分隔 |
| `DD-MM-YYYY` | 15-01-2024 | 日在前 |

### axisFormat 设置

```mermaid
gantt
    dateFormat YYYY-MM-DD
    axisFormat %m-%d
```

常用格式符：

| 格式符 | 说明 |
| --- | --- |
| `%Y` | 四位年份 |
| `%m` | 两位月份 |
| `%d` | 两位日期 |
| `%H` | 小时（24小时制） |
| `%M` | 分钟 |
| `%W` | 周数 |

## 任务定义

### 基本语法

```
任务名称 :任务ID, 开始日期, 持续时间
```

### 任务状态

```mermaid
gantt
    section 状态示例
    已完成 :done, a1, 2024-01-01, 3d
    进行中 :active, a2, after a1, 3d
    未开始 :crit, a3, after a2, 3d
```

| 状态 | 关键字 | 说明 |
| --- | --- | --- |
| 已完成 | `done` | 任务完成 |
| 进行中 | `active` | 正在进行 |
| 关键任务 | `crit` | 关键路径 |
| 未开始 | 默认 | 普通状态 |

### 状态组合

```mermaid
gantt
    section 组合状态
    关键进行中 :crit, active, a1, 2024-01-01, 5d
    关键已完成 :crit, done, a2, after a1, 3d
```

## 任务时间设置

### 固定日期

```mermaid
gantt
    任务A :a1, 2024-01-01, 7d
```

### 相对于其他任务

```mermaid
gantt
    任务A :a1, 2024-01-01, 7d
    任务B :a2, after a1, 5d
```

### 指定结束日期

```mermaid
gantt
    任务A :a1, 2024-01-01, 2024-01-15
```

### 排除日期

```mermaid
gantt
    excludes weekends
    任务A :a1, 2024-01-01, 7d
```

## 分组

### section 分组

```mermaid
gantt
    title 项目进度
    section 需求阶段
    需求分析 :a1, 2024-01-01, 5d
    需求评审 :a2, after a1, 2d
    section 开发阶段
    设计 :a3, after a2, 3d
    编码 :a4, after a3, 10d
    测试 :a5, after a4, 5d
```

## 里程碑

```mermaid
gantt
    section 里程碑
    项目启动 :milestone, m1, 2024-01-01, 0d
    版本发布 :milestone, m2, 2024-02-01, 0d
```

里程碑特点：
- 持续时间为 0
- 显示为菱形标记
- 用于标记重要节点

## 依赖关系

### 顺序依赖

```mermaid
gantt
    任务A :a1, 2024-01-01, 5d
    任务B :a2, after a1, 3d
    任务C :a3, after a2, 4d
```

### 多任务依赖

```mermaid
gantt
    任务A :a1, 2024-01-01, 5d
    任务B :a2, 2024-01-03, 3d
    任务C :a3, after a1 a2, 4d
```

## 样式配置

### 全局配置

```mermaid
gantt
    title 样式配置示例
    dateFormat YYYY-MM-DD

    section 配置
    标题 :title, 2024-01-01, 30d
    包含今天 :todayMarker, 2024-01-15
```

### todayMarker 设置

```mermaid
gantt
    todayMarker off
    任务A :a1, 2024-01-01, 30d
```

或自定义样式：

```mermaid
gantt
    todayMarker stroke-width:5px,stroke:#0f0,opacity:0.5
    任务A :a1, 2024-01-01, 30d
```

## 高级配置

### excludes 排除日期

```mermaid
gantt
    excludes weekends 2024-01-01
    任务A :a1, 2024-01-01, 7d
```

排除类型：
- `weekends` - 周末
- `friday` - 特定星期
- 具体日期 - `2024-01-01`

### includes 包含日期

```mermaid
gantt
    includes 2024-01-06
    excludes weekends
    任务A :a1, 2024-01-01, 7d
```

## 最佳实践

### 命名规范

- 任务名称简洁明了
- 任务 ID 使用有意义的标识
- 分组名称概括性强

### 布局建议

- 合理设置时间粒度
- 使用里程碑标记关键节点
- 控制任务数量（建议 ≤ 30）

### 示例：完整甘特图

```mermaid
gantt
    title 软件开发项目计划
    dateFormat YYYY-MM-DD
    axisFormat %m/%d

    section 需求阶段
    需求调研 :done, req1, 2024-01-01, 5d
    需求分析 :done, req2, after req1, 3d
    需求评审 :active, req3, after req2, 2d

    section 设计阶段
    架构设计 :des1, after req3, 4d
    详细设计 :des2, after des1, 5d
    设计评审 :milestone, des3, after des2, 0d

    section 开发阶段
    前端开发 :dev1, after des2, 15d
    后端开发 :dev2, after des2, 15d
    联调测试 :crit, dev3, after dev1 dev2, 5d

    section 发布阶段
    部署上线 :pub1, after dev3, 2d
    验收测试 :pub2, after pub1, 3d
    项目交付 :milestone, pub3, after pub2, 0d
```

## 参考链接

- [Mermaid 官方文档 - Gantt Diagram](https://mermaid.js.org/syntax/gantt.html)
