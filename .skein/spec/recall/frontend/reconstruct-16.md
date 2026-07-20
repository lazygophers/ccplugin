---
title: file:// 协议检测 & 降级处理
layer: recall
category: frontend
keywords: [error,fallback,file-protocol,graceful]
source: reconstruct
authored-by: skein-spec
created: 1784346008
status: active
related: []
updated: 1784346008
---

## 触发场景
前端依赖 HTTP 端点（fetch/WebSocket），但用户可能 file:// 直接打开 HTML。

## 陷阱-正解
**陷阺**：fetch 失败无处理，页面白屏。
**正解**：检测 location.protocol === 'file:'，降级友好提示或 reload。

## 规则
6 文件一致检测（webapp api.js / live.js / board switcher.js 等）。

## 关联
frontend/graceful-fallback
