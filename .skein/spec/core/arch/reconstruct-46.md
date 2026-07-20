---
title: 精确路由声明在 StaticFiles mount 前
layer: core
category: arch
keywords: [routing,mount,starlette,order,404]
source: reconstruct
authored-by: skein-spec
created: 1784346838
status: active
related: []
updated: 1784346838
---

## 铁律

- MUST：精确路由（@app.get("/task") 等）在所有 app.mount() 之前声明
- MUST：否则裸路径被 mount 吞成 404 或被当作静态文件

## 反例表

| 禁 | 改为 |
|---|---|
| app.mount(...) 后 @app.get("/task") | 先 @app.get，后 mount |
| 404 on /task（文件不存在） | 检查路由声明顺序 |
| 页面被当静态 404 | 重新安排声明顺序 |
