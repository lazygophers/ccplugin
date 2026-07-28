---
title: http-server
layer: recall
category: impl
keywords: [mount,static,webserver,configuration,middleware,request,caching,stream,async,handler,blocking,fastapi,error,http,status,json,response]
status: active
---

## StaticFiles mount 设 check_dir=False

### 触发场景
mount 目录未落地或构建失败。

### 陷阱-正解
**陷阱**：check_dir=True (默认)，目录不存在时 mount 炸。
**正解**：check_dir=False 允许目录缺失。

### 规则
skein.py:2342-2348 五处 mount 均设 check_dir=False。

### 关联
impl/graceful-mount-missing-assets

## middleware 缓存 request body 供 handler 复用

### 触发场景
多个 handler 或中间件需要读 request body。

### 陷阱-正解
**陷阱**：body stream 一次性，重复读失败。
**正解**：middleware 读一次缓存进 request.scope["skein_body"]，handler 复用不重读。

### 规则
skein.py:2185-2200 middleware；:2260/:2275/:2297 handler 取用。

### 关联
impl/request-caching

## 阻塞操作 handler 用 sync def（线程池）

### 触发场景
exec 或 config 读取等阻塞操作。

### 陷阱-正解
**陷阱**：async def 内做 subprocess/同步 IO，阻塞事件循环。
**正解**：`def` (sync)，FastAPI 自动跑线程池。

### 规则
skein.py:2272-2273 _exec；:2289 _cfg_get 均 sync def。

### 关联
impl/async-handler-patterns

## HTTP 错误响应统一结构 JSONResponse + 语义状态码

### 铁律

- MUST：所有 HTTP 错误返回 `{"error": "<message>"}` JSON 对象
- MUST：400 用于请求体/参数验证失败，403 用于安全边界/权限，404 用于资源不存在，500 用于异常
- MUST：结构 `JSONResponse({"error": "..."}, status_code=xxx)`

### 反例表

| 禁 | 改为 |
|---|---|
| `{"message": "..."}` | `{"error": "..."}` |
| 路径越界返回 404 | 返回 403（安全边界） |
| 任意错误都 500 | 按语义码分类 |
| 纯文本错误响应 | 统一 JSON 结构 |
