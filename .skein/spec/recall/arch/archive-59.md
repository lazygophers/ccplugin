---
title: PEP 563 + FastAPI 注解陷阱 (运行时类型内省)
layer: recall
category: arch
keywords: [pep-563,from-future-annotations,fastapi,pydantic,运行时注解,mypy,422]
source: archive
authored-by: skein-spec
created: 1784346961
status: active
related: []
updated: 1784346961
---

---
title: PEP 563 + FastAPI 注解陷阱 (运行时类型内省)
layer: core
category: arch
keywords: [pep-563,from-future-annotations,fastapi,pydantic,运行时注解,mypy,422,forward-ref,局部import,类型注解]
source: skein-trellis-optimize
authored-by: skein-memory
created: 1784308055
---

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
