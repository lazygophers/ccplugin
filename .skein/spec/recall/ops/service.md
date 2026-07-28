---
title: service
layer: recall
category: ops
keywords: [network,port,allocation,dynamic,dependency,lazy,optional,serve,cleanup,singleton,atexit,idempotent,lock]
status: active
---

## 服务端口动态随机探（bind :0）

### 触发场景
启动看板服务，需要分配端口。

### 陷阱-正解
**陷阋**：硬编码固定端口 8080。
**正解**：socket bind :0 探空闲端口，立即释放，交 uvicorn 使用。

### 规则
skein.py:2096-2101 探，:2117 记 lock。

### 关联
ops/dynamic-port-allocation

## serve 缺依赖动态装 (pip install)

### 触发场景
serve 启动前，fastapi/uvicorn 可能未装。

### 陷阱-正解
**陷阱**：import 炸，无 fallback。
**正解**：serve 前检查依赖，缺则 pip 装，仍缺则告警 stderr 返回错误码。

### 规则
skein.py:2034-2045 检查函数；:2085-2092 装与告警。

### 关联
ops/optional-dependencies

## atexit cleanup 校验 port 防误删

### 触发场景
serve 进程退出时清理 lock 文件。

### 陷阱-正解
**陷阱**：误删他实例的 lock。
**正解**：atexit 清理时校验 lock 内 port == 本进程 port。

### 规则
skein.py:2103-2108 清理；:2112 atexit 注册。

### 关联
ops/singleton-cleanup

## serve 幂等去重（lock + id 探测单例）

### 铁律

- MUST：`serve` 启动前检查 `.board-server.lock` 文件是否存在
- MUST：读 lock 内的 port，探测 `http://localhost:<port>/__skein__/id` 获项目标识
- MUST：id 匹配当前项目则复用已有服务，返回该 port；否则创建新服务并写 lock

### 反例表

| 禁 | 改为 |
|---|---|
| 每次 serve 都起新 server | 先检查 lock，id 匹配则复用 |
| 多个 port 泄漏 | 单一 port，lock 去重 |
| 进程退出后 lock 不清 | atexit 清理（先检查 port 自己才清） |
