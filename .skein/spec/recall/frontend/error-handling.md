---
title: error-handling
layer: recall
category: frontend
keywords: [error,fallback,file-protocol,graceful,exception,handling,boundary,concurrency,async,deduplication,race]
status: active
---

## file:// 协议检测 & 降级处理

### 触发场景
前端依赖 HTTP 端点（fetch/WebSocket），但用户可能 file:// 直接打开 HTML。

### 陷阱-正解
**陷阱**：fetch 失败无处理，页面白屏。
**正解**：检测 location.protocol === 'file:'，降级友好提示或 reload。

### 规则
6 文件一致检测（webapp api.js / live.js / board switcher.js 等）。

### 关联
frontend/graceful-fallback

## 统一 ApiError + page 级错误边界

### 触发场景
API 请求失败或某 page 渲染失败，需要用户感知但不炸穿整站。

### 陷阱-正解
**陷阱**：异常冒泡，页面崩溃。
**正解**：统一抛 ApiError(status, message)；page render 外层 try/catch 转占位符。

### 规则
api.js:7-23 定义与抛；router.js:73-79 page catch；各 page 内自己 .catch()。

### 关联
frontend/error-boundary

## 异步竞态守卫（token 自增去重）

### 触发场景
快速切页或连续搜索，多个异步请求在途。

### 陷阱-正解
**陷阱**：旧响应覆盖新数据。
**正解**：自增 token/lastReq，仅最后一次响应生效，过期响应丢弃。

### 规则
router.js:47-78 navToken；app.js:63-71 lastReq 搜索去重。

### 案例
快速 tab 切换，仅最后 tab 数据渲染；搜索框快速输入，仅最后查询生效。

### 关联
frontend/async-deduplication
