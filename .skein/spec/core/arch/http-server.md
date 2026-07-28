---
title: http-server
layer: core
category: arch
keywords: [security,exec,whitelist,argv,injection,routing,mount,starlette,order,404,config]
status: active
---

## exec 端点白名单 argv 命令构造（禁 shell 注入）

### 铁律

- MUST：有白名单函数（如 `_exec_argv(cmd, ...)` ）枚举允许的每个命令
- MUST：对每个命令显式构造 argv 列表，禁 shell=True 或 f-string 拼接
- MUST：白名单外命令返回 None，路由返回 403
- MUST：subprocess.run 调用传 argv 列表，禁 shell=True

### 反例表

| 禁 | 改为 |
|---|---|
| shell=True + f"skein {cmd} {user_input}" | argv 列表 + 白名单检查 |
| 直接拼接命令字符串 | _exec_argv 返回 None 则 403 |
| os.system(user_cmd) | subprocess.run([...], shell=False) |
| 允许任意子命令 | 白名单枚举各命令 |

## 精确路由声明在 StaticFiles mount 前

### 铁律

- MUST：精确路由（@app.get("/task") 等）在所有 app.mount() 之前声明
- MUST：否则裸路径被 mount 吞成 404 或被当作静态文件

### 反例表

| 禁 | 改为 |
|---|---|
| app.mount(...) 后 @app.get("/task") | 先 @app.get，后 mount |
| 404 on /task（文件不存在） | 检查路由声明顺序 |
| 页面被当静态 404 | 重新安排声明顺序 |

## 配置写端点防注入（仅认 CONFIG_DEFAULTS 键）

### 铁律

- MUST：POST /config 接收的 JSON 仅保留 CONFIG_DEFAULTS 中已列举的键
- MUST：按类型 coerce，coerce 失败时保持原值或默认
- MUST：未知键一律忽略

### 反例表

| 禁 | 改为 |
|---|---|
| 接收任意 JSON key | 仅过滤已知 key |
| 直接将用户 JSON 写入配置 | 按已知字段逐个赋值 + 类型转换 |
| 新增 key 被接受 | 未知 key 忽略 |
