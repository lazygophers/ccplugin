---
title: http-server
layer: recall
category: arch
keywords: [routing,namespace,internal,api,security,path,traversal,realpath,validation,spa,fallback,mount,starlette,pep-563,from-future-annotations,fastapi,pydantic,运行时注解,mypy,422]
status: active
---

## 服务内部端点用 /__skein__/ 命名空间

### 触发场景
新增后端端点，需要决定命名空间。

### 陷阱-正解
**陷阱**：混用公开与内部路由，路径冲突。
**正解**：内部端点（data/queue/config 等）用 `/__skein__/` 命名空间隔离。

### 规则
skein.py:2008-2010 定义，:2210-2322 所有内部路由一致应用。

### 关联
arch/namespace-isolation

## 路径穿越防止（realpath 校验 + 父目录检查）

### 铁律

- MUST：任何读/写端点先用 `Path(p).resolve()` 获 realpath
- MUST：检查 realpath 是否在允许根（如 `.skein/spec/`）的 parents 内，不在则 403
- MUST：禁字符串拼接 path，用 pathlib 处理
- MUST：防范 `../../../etc/passwd` 等穿越

### 反例表

| 禁 | 改为 |
|---|---|
| 直接拼接 root + user_path | Path.resolve() + 父目录检查 |
| os.path.join(...) 拼接 | pathlib.Path(...).resolve() |
| 不检查父目录 | 检查 `root in realpath.parents` |
| /spec/file?path=../../../../etc/passwd | 穿越检查失败返回 403 |

## SPA catch-all fallback 声明在所有 mount 之后

### 铁律

- MUST：SPA fallback 中间件/路由声明在所有 mount 之后
- MUST：fallback 返回 index.html，让前端 router 处理路由
- MUST：否则 /vendor/app.css 等静态被 fallback 吞成 index.html

### 反例表

| 禁 | 改为 |
|---|---|
| fallback 在 mount 之前 | 在 mount 之后声明 |
| /vendor/x.css 返回 index.html 破坏 | 调整声明顺序 |
| SPA 前端路由全 404 | 确认 fallback 在最后 |

## PEP 563 + FastAPI 注解陷阱 (运行时类型内省)

**触发场景**: 给 Web 框架 (FastAPI / Pydantic / dataclasses 等依赖运行时类型注解的库) 的代码加 mypy 注解。

**陷阱**: 文件顶加 `from __future__ import annotations` (PEP 563) 会把所有注解 **string 化** (存为字符串字面量, 运行时惰性求值)。这对纯静态检查无害, 但破坏依赖运行时内省的框架:
- **FastAPI** `get_typed_signature` 用 `handler.__globals__` (模块全局命名空间) 解析 ForwardRef 字符串。
- 若 route handler 的参数类型 (如 `Request`/`WebSocket`) 只在函数/块内 **局部 import**, 则该名不在模块全局 → ForwardRef 解析失败 → 参数被当成**必填 query/body 参数** → 请求 422。

**症状**: 注解前 POST 正常 (200), 注解后同一请求 422 Unprocessable Entity; mypy 全绿但运行时崩。

**修法** (二选一, 任一即可):
1. 局部 import 后**注入模块全局**:
   ```python
   from fastapi import Request
   _g = globals(); _g["Request"] = Request
   ```
2. 把 import 提到模块顶层 (让类型在模块全局可见)。

**判定门** (加注解后必跑): 给框架代码加注解后, **必须跑一次真实 HTTP/功能请求**验运行时行为不变, 不能只信 mypy --strict 通过 (静态绿 ≠ 运行时安全)。静态类型检查 + 运行时行为验证, 缺一不可。

**反例**: 给 FastAPI handler 加注解后只跑 mypy 就宣称"零逻辑变更" (实际 PEP 563 已改运行时行为) / route 类型只在局部 import 不注入全局 / 撤掉注解规避而非修根因。

**适用**: 任何依赖运行时注解内省的框架 (FastAPI / Pydantic / SQLAlchemy 2.0 ORM / dataclasses / attrs)。核心: 注解变更对这类框架非纯增量, 需运行时验证。
