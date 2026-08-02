---
title: 订单状态机测试覆盖要求
namespace: rules
inclusion: auto
category: test
keywords: [状态机,测试,订单,table-driven]
source: order-pay
authored-by: skein-memory
---

订单状态机测试必覆盖: 待支付→已支付→已发货→已完成, 及各态非法跳转拒绝 (table-driven test)。
