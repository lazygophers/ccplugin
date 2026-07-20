---
title: serve 幂等去重（lock + id 探测单例）
layer: recall
category: ops
keywords: [serve,idempotent,singleton,lock,port]
source: reconstruct
authored-by: skein-spec
created: 1784346778
status: active
related: []
updated: 1784346778
---

## 铁律

- MUST：`serve` 启动前检查 `.board-server.lock` 文件是否存在
- MUST：读 lock 内的 port，探测 `http://localhost:<port>/__skein__/id` 获项目标识
- MUST：id 匹配当前项目则复用已有服务，返回该 port；否则创建新服务并写 lock

## 反例表

| 禁 | 改为 |
|---|---|
| 每次 serve 都起新 server | 先检查 lock，id 匹配则复用 |
| 多个 port 泄漏 | 单一 port，lock 去重 |
| 进程退出后 lock 不清 | atexit 清理（先检查 port 自己才清） |
