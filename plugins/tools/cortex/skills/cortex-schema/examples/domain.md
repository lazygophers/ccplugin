> 样例 — type=domain, 完整可直接落盘到 领域/tech/rust/async/tokio-runtime.md

---
type: domain
area: tech
created: 2026-06-09
updated: 2026-06-09
tags: [rust, async, tokio, runtime, scheduler]
aliases: [tokio-runtime-notes, tokio-internals]
weight: 0.6
---

# Tokio Runtime 笔记

Tokio 是 Rust 主流异步 runtime, 基于 work-stealing scheduler + epoll/kqueue/IOCP reactor.

## 核心组件

- **Scheduler**: multi-thread (默认) 或 current-thread; 每 worker 一队列, 空闲 worker steal
- **Reactor**: mio 封装的 I/O 事件源, 唤醒挂起 task
- **Timer**: hashed wheel, 精度受 runtime tick 限制

## 调度行为

`tokio::spawn` 投递到当前 worker 本地队列; 队满 overflow 进全局队列. 阻塞调用必须 `spawn_blocking` 隔离, 否则饿死 worker.

## 参考

- 官方文档: https://docs.rs/tokio
- 对比 async-std: [[async-runtime-comparison]]
- 实战 patterns: [[tokio-patterns]]
