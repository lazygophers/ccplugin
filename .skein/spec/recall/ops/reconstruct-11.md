---
title: 服务端口动态随机探（bind :0）
layer: recall
category: ops
keywords: [network,port,allocation,dynamic]
source: reconstruct
authored-by: skein-spec
created: 1784345975
status: active
related: []
updated: 1784345975
---

## 触发场景
启动看板服务，需要分配端口。

## 陷阱-正解
**陷阋**：硬编码固定端口 8080。
**正解**：socket bind :0 探空闲端口，立即释放，交 uvicorn 使用。

## 规则
skein.py:2096-2101 探，:2117 记 lock。

## 关联
ops/dynamic-port-allocation
