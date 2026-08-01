---
inclusion: auto
title: concurrency
layer: core
category: arch
keywords: [lock,flock,concurrent,write,task.json,race,batch,claim]
status: active
---

## 工作区级 fcntl.flock 排他锁（状态写命令）

### 铁律

- MUST：所有修改 `.skein/` 状态的命令（task write/delete/start/done/fail）在执行前获取 `fcntl.flock` 排他锁（LOCK_EX）
- MUST：超时设置 5-10s，超时失败返回错误码，不阻塞无限
- MUST：纯读命令（list/read/query）可免锁加速

### 反例表

| 禁 | 改为 |
|---|---|
| 直接读写 task.json 无锁 | 获 flock 排他锁再写 |
| 用全局 lock | 按工作区 (pwd/.skein) 独立锁 |
| 竞态窗口：解锁 → 重读检查 | 在锁内一气完成 read-modify-write |
| 超时 freeze 不释放 | 设超时直接 exit |

## 并写竞态禁止（需串行或 claim 批处理）

### 铁律

- MUST：同一并行批禁止 ≥2 个 `.skein` 状态写命令，必须串行或 claim 一次性认领
- MUST：hook 层检测批内写命令，≥2 个则 block/defer 后续写直到前一写完成
- MUST：就绪 subtask 批必须一次性 claim（不逐个分回合）

### 反例表

| 禁 | 改为 |
|---|---|
| start task1 && start task2（并行） | 串行或 claim 整批 |
| sediment + start 同批 | 分开两批 |
| subtask 逐个 start 分回合 | 一次 claim |
