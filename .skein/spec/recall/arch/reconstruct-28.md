---
title: 重依赖（fastapi/uvicorn）局部 import（顶层无可见）
layer: recall
category: arch
keywords: [import,dependency,lazy,build,layering]
source: reconstruct
authored-by: skein-spec
created: 1784346479
status: active
related: []
updated: 1784346479
---

## 铁律

- MUST：fastapi、uvicorn、websocket、atexit、socket、threading 等只在函数/方法内 import
- MUST：顶层不可见这些 import（防 CLI 主流程依赖）
- MUST：serve-only 工作集中在 `_run_server` / `serve` 等函数内

## 反例表

| 禁 | 改为 |
|---|---|
| `from fastapi import FastAPI` at module top | import FastAPI inside serve() function |
| `import uvicorn` at top | import uvicorn only in _run_server() |
