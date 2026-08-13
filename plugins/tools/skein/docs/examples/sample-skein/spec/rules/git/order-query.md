---
title: finish 前本地测试全绿
namespace: rules
inclusion: always
category: git
keywords: [test,commit,finish]
source: order-query
authored-by: skein-memory
---

commit 前必跑 `go test ./...`, 全绿才 finish。CI 无二次门, 本地是唯一关卡。
