---
title: finish 前本地测试全绿
layer: core
category: git
keywords: [test,commit,finish]
source: order-query
authored-by: skein-memory
created: 1783754714
---

commit 前必跑 `go test ./...`, 全绿才 finish。CI 无二次门, 本地是唯一关卡。
