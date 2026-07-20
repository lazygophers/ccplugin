---
title: HTTP 错误响应统一结构 JSONResponse + 语义状态码
layer: recall
category: impl
keywords: [error,http,status,json,response]
source: reconstruct
authored-by: skein-spec
created: 1784346658
status: active
related: []
updated: 1784346658
---

## 铁律

- MUST：所有 HTTP 错误返回 `{"error": "<message>"}` JSON 对象
- MUST：400 用于请求体/参数验证失败，403 用于安全边界/权限，404 用于资源不存在，500 用于异常
- MUST：结构 `JSONResponse({"error": "..."}, status_code=xxx)`

## 反例表

| 禁 | 改为 |
|---|---|
| `{"message": "..."}` | `{"error": "..."}` |
| 路径越界返回 404 | 返回 403（安全边界） |
| 任意错误都 500 | 按语义码分类 |
| 纯文本错误响应 | 统一 JSON 结构 |
