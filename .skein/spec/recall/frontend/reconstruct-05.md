---
title: petite-vue 先 await 拉数据，再 createApp
layer: recall
category: frontend
keywords: [petite-vue,async,render,data,fetch]
source: reconstruct
authored-by: skein-spec
created: 1784345946
status: active
related: []
updated: 1784345946
---

## 触发场景
编写响应式 page（需要绑定数据到 petite-vue）。

## 陷阱-正解
**陷阱**：依赖 petite-vue mounted 钩子拉数据。
**正解**：render() 内 await 拉全数据，再 createApp(初始态).mount()；vendored petite-vue 无对外钩子。

## 规则
响应式 page 必须先数据后 createApp。

## 案例
task.js:329 / dashboard.js / archive.js 同注释说明。

## 关联
frontend/async-render-data-fetch
