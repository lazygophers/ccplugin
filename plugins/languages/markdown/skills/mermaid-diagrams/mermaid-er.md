---
name: mermaid-er
description: Mermaid 实体关系图语法规范，包括实体定义、关系类型、属性、键约束和样式配置
---

# Mermaid 实体关系图 (ER Diagram)

实体关系图用于数据库设计，展示实体、属性和实体之间的关系。

## 基本语法

```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
```

## 实体定义

### 基本实体

```mermaid
erDiagram
    CUSTOMER
    ORDER
    PRODUCT
```

### 带属性的实体

```mermaid
erDiagram
    CUSTOMER {
        string name
        string custNumber
        string sector
    }
    ORDER {
        int orderNumber
        string deliveryAddress
    }
```

### 属性类型

```mermaid
erDiagram
    PRODUCT {
        int id PK
        string name
        string description
        float price
        int stock
        string[] tags
        datetime createdAt
    }
```

### 属性键约束

```mermaid
erDiagram
    CUSTOMER {
        string id PK "主键"
        string email UK "唯一键"
        string name
        string phone
    }
    ORDER {
        int id PK
        string customerId FK "外键"
        string status
    }
```

| 键类型 | 标记 | 说明 |
| --- | --- | --- |
| `PK` | 主键 | Primary Key |
| `FK` | 外键 | Foreign Key |
| `UK` | 唯一键 | Unique Key |
| `PK, FK` | 组合 | 同时是主键和外键 |

### 属性注释

```mermaid
erDiagram
    USER {
        string id PK "用户唯一标识"
        string name "用户名，最长50字符"
        int age "年龄，18-120"
    }
```

## 关系定义

### 关系语法

```
<实体A> <关系> <实体B> : <关系标签>
```

### 关系类型

```mermaid
erDiagram
    A ||--|| B : "一对一"
    C ||--o{ D : "一对多"
    E }|--|{ F : "多对多"
    G }o--o{ H : "零或多对零或多"
```

### 关系符号说明

| 符号 | 含义 |
| --- | --- |
| `||` | 恰好一个 |
| `o|` | 零或一个 |
| `}|` | 一个或多个 |
| `o{` | 零或多个 |
| `--` | 标识关系（实线） |
| `..` | 非标识关系（虚线） |

### 完整关系表

| 左侧 | 右侧 | 含义 |
| --- | --- | --- |
| `\|\|` | `\|\|` | 恰好一个对恰好一个 |
| `\|\|` | `o\|` | 恰好一个对零或一个 |
| `\|\|` | `\}\|` | 恰好一个对一个或多个 |
| `\|\|` | `o{` | 恰好一个对零或多个 |
| `}\|` | `}\|` | 一个或多个对一个或多个 |
| `o{` | `o{` | 零或多个对零或多个 |

### 关系别名

```mermaid
erDiagram
    CAR 1 to zero or more NAMED-DRIVER : allows
    PERSON many(0) optionally to 0+ NAMED-DRIVER : is
```

可用别名：
- `one or zero` / `zero or one`
- `one or more` / `one or many`
- `zero or more` / `zero or many`
- `only one` / `1`
- `many(0)` / `many(1)` / `0+` / `1+`

## 标识关系

### 标识关系（实线）

```mermaid
erDiagram
    CAR ||--|{ NAMED-DRIVER : allows
```

### 非标识关系（虚线）

```mermaid
erDiagram
    PERSON }o..o{ CAR : drives
```

## 实体别名

```mermaid
erDiagram
    p[Person] {
        string firstName
        string lastName
    }
    a["Customer Account"] {
        string email
    }
    p ||--o| a : has
```

## 方向设置

```mermaid
erDiagram
    direction LR
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
```

方向选项：
- `TB` - 从上到下
- `BT` - 从下到上
- `LR` - 从左到右
- `RL` - 从右到左

## 样式

### 直接样式

```mermaid
erDiagram
    A ||--|| B : label
    style A fill:#f9f,stroke:#333,stroke-width:4px
    style B fill:#bbf,stroke:#f66,stroke-width:2px
```

### 类定义

```mermaid
erDiagram
    CAR {
        string registrationNumber
    }
    PERSON {
        string name
    }
    PERSON:::highlight ||--|| CAR : owns

    classDef highlight fill:#f96
```

## 布局配置

### ELK 布局

```mermaid
---
config:
  layout: elk
---
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
```

## 最佳实践

### 命名规范

- 实体名称使用大写
- 属性使用 camelCase
- 关系标签使用动词短语

### 设计建议

- 明确主键和外键
- 使用注释说明复杂属性
- 控制实体数量（建议 ≤ 15）

### 示例：完整 ER 图

```mermaid
erDiagram
    direction TB

    CUSTOMER {
        string id PK "客户ID"
        string name "客户名称"
        string email UK "邮箱地址"
        string phone "联系电话"
    }

    ORDER {
        int id PK "订单ID"
        string customerId FK "客户ID"
        datetime orderDate "下单时间"
        string status "订单状态"
    }

    PRODUCT {
        int id PK "产品ID"
        string name "产品名称"
        float price "单价"
        int stock "库存数量"
    }

    ORDER_ITEM {
        int orderId PK, FK "订单ID"
        int productId PK, FK "产品ID"
        int quantity "数量"
        float unitPrice "单价"
    }

    CUSTOMER ||--o{ ORDER : "下单"
    ORDER ||--|{ ORDER_ITEM : "包含"
    PRODUCT ||--o{ ORDER_ITEM : "被订购"
```

## 参考链接

- [Mermaid 官方文档 - ER Diagram](https://mermaid.js.org/syntax/entityRelationshipDiagram.html)
