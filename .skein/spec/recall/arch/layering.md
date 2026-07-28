---
title: layering
layer: recall
category: arch
keywords: [architecture,lib,layer,dependency,import,lazy,build,layering,separation-of-concerns,data]
status: active
---

## lib = 共享库层，scripts 单向依赖

### 触发场景
提取公用函数/DB 工具时决定放 lib 还是 scripts。

### 陷阱-正解
**陷阱**：库函数散落 scripts/ 各处，或 lib 反向依赖 scripts。
**正解**：通用工具/DB ORM 放 lib，scripts 单向依赖 lib（`from lib...`），lib 不反依赖。

### 规则
依赖图：scripts → lib，不反向。

### 关联
arch/monorepo-layer-isolation, arch/circular-dependency-prevention

## 重依赖（fastapi/uvicorn）局部 import（顶层无可见）

### 铁律

- MUST：fastapi、uvicorn、websocket、atexit、socket、threading 等只在函数/方法内 import
- MUST：顶层不可见这些 import（防 CLI 主流程依赖）
- MUST：serve-only 工作集中在 `_run_server` / `serve` 等函数内

### 反例表

| 禁 | 改为 |
|---|---|
| `from fastapi import FastAPI` at module top | import FastAPI inside serve() function |
| `import uvicorn` at top | import uvicorn only in _run_server() |

## 后端算数据 / 前端呈现（职责分离）

### 触发场景
业务逻辑与数据计算。

### 陷阱-正解
**陷阱**：前端重算 DAG/状态/节点。
**正解**：后端算好经 JSON 下发，前端只做呈现映射（色彩/布局）。

### 规则
Python _board_data() 注 CSS links + 结构化数据；前端 setNodeMaps() 注入映射。
