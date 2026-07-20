---
title: 失败路径显式断言 (SystemExit/pytest.raises)
layer: recall
category: test
keywords: [test,exception,assertion,failure]
source: reconstruct
authored-by: skein-spec
created: 1784346042
status: active
related: []
updated: 1784346042
---

## 触发场景
验证并发/失败契约。

## 陷阺-正解
**陷阺**：无异常处理验证。
**正解**：SystemExit / pytest.raises 显式验失败契约。
