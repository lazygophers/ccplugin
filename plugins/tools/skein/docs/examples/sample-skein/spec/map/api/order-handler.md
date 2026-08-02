---
title: 订单处理模块映射
namespace: map
inclusion: fileMatch
category: api
keywords: [订单,处理,模块,映射]
globs: ["plugins/tools/skein/scripts/*.py"]
anchors:
  - 模块职责
  - 入口函数
  - 数据流
---

## 模块职责

`order_handler` 模块负责订单相关的 HTTP 请求处理:
- 订单创建 POST /orders
- 订单查询 GET /orders/{id}
- 订单支付 PUT /orders/{id}/pay

## 入口函数

主要入口点在 `order_handler.py`:
- `create_order()`: 处理订单创建请求
- `get_order()`: 处理订单查询请求
- `pay_order()`: 处理订单支付请求

## 数据流

```
HTTP Request → order_handler → order_service → domain_model → DB
                              ↓
                         validation ← inventory_client
```

1. Handler 层: 请求解析/参数校验
2. Service 层: 业务编排/事务控制
3. Domain 层: 核心业务逻辑
4. Infra 层: 数据持久化/外部调用
