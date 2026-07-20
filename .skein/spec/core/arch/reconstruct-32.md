---
title: exec 端点白名单 argv 命令构造（禁 shell 注入）
layer: core
category: arch
keywords: [security,exec,whitelist,argv,injection]
source: reconstruct
authored-by: skein-spec
created: 1784346554
status: active
related: []
updated: 1784346554
---

## 铁律

- MUST：有白名单函数（如 `_exec_argv(cmd, ...)` ）枚举允许的每个命令
- MUST：对每个命令显式构造 argv 列表，禁 shell=True 或 f-string 拼接
- MUST：白名单外命令返回 None，路由返回 403
- MUST：subprocess.run 调用传 argv 列表，禁 shell=True

## 反例表

| 禁 | 改为 |
|---|---|
| shell=True + f"skein {cmd} {user_input}" | argv 列表 + 白名单检查 |
| 直接拼接命令字符串 | _exec_argv 返回 None 则 403 |
| os.system(user_cmd) | subprocess.run([...], shell=False) |
| 允许任意子命令 | 白名单枚举各命令 |
