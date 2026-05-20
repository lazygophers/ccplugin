---
name: desktop-code-quality-2026-04-05
description: @desktop 2026-04-05 三路并行 Agent 审查沉淀的反模式与编码规则
type: feedback
tags: [code-quality, refactoring, desktop]
---

# @desktop 代码质量规则

> 由 2026-04-05 三路并行 Agent 审查 (代码复用 / 代码质量 / 效率) 沉淀。流水账级"在 X 文件改了 Y" 已删, 仅留可复用规则。

## 反模式 (禁)

### TOCTOU (Time-of-Check to Time-of-Use)

```rust
// ❌ 竞态 + 双系统调用
if path.exists() {
    fs::read_to_string(path)?
}

// ✅ 直接读, 处理 NotFound
match fs::read_to_string(path) {
    Ok(s) => s,
    Err(e) if e.kind() == ErrorKind::NotFound => default,
    Err(e) => return Err(e.into()),
}
```

文件/网络等外部资源**直接尝试**, 不先 exists/check。

### 重复子进程调用

页面加载时**并行**多个 `claude plugins ...` 子进程 → 集中到单点服务 (`MarketplaceService::load`) + Tauri 缓存。前端事件取数, 不并发调 CLI。

### sync await 等业务结果

见 [[desktop-event-driven-architecture]] — 命令必须立即返回, 进度走事件。

## DRY 规则 (提)

| 重复 ≥3 处的模式 | 必须抽提 |
|---|---|
| `PythonBridge` 初始化 (5 处) | `get_bridge()` 辅助 |
| `execute_with_progress()` / `execute_simple()` Rust 子进程通用执行 | 服务层方法, 不 inline |
| 前端错误处理 (try/catch + toast + state set) | `executeCommand()` hook 通用执行器 |
| 进度监听 setup/cleanup | `withProgress()` 装饰器, 自动 `unlisten()` on unmount |

## 编码原则

- Rust 业务逻辑禁向 TS 暴露细节, 通过事件 (见 event-driven-architecture)
- `Result<T, E>` 处理: 用 `?` + `From<E>` 自动转, 禁 `unwrap()`/`expect()` 在生产路径
- 命令立即返回 `()`, 进度/结果走事件
- TS 侧组件 unmount 必 `unlisten()`, 防内存泄漏
- 进度事件 throttle (~16ms)

## 审查方法

三路并行 Agent (复用 / 质量 / 效率) 各自独立分析, 主线汇总。每路 Agent 输出固定 JSON schema, 便于合并去重。
