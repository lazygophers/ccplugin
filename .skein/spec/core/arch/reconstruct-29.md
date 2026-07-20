---
title: 工作区级 fcntl.flock 排他锁（状态写命令）
layer: core
category: arch
keywords: [lock,flock,concurrent,write,task.json]
source: reconstruct
authored-by: skein-spec
created: 1784346500
status: active
related: []
updated: 1784346500
---

## 铁律

- MUST：所有修改 `.skein/` 状态的命令（task write/delete/start/done/fail）在执行前获取 `fcntl.flock` 排他锁（LOCK_EX）
- MUST：超时设置 5-10s，超时失败返回错误码，不阻塞无限
- MUST：纯读命令（list/read/query）可免锁加速

## 反例表

| 禁 | 改为 |
|---|---|
| 直接读写 task.json 无锁 | 获 flock 排他锁再写 |
| 用全局 lock | 按工作区 (pwd/.skein) 独立锁 |
| 竞态窗口：解锁 → 重读检查 | 在锁内一气完成 read-modify-write |
| 超时 freeze 不释放 | 设超时直接 exit |
