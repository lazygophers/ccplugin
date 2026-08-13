---
title: 金额一律整数分
namespace: rules
inclusion: always
category: domain
keywords: [money,金额,精度,订单]
source: order-create-api
authored-by: skein-memory
---

所有金额字段用整数分 (int64), 禁 float。展示层才除 100, 防浮点误差。
