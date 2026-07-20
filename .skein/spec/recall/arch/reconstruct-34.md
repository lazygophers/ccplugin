---
title: 路径穿越防止（realpath 校验 + 父目录检查）
layer: recall
category: arch
keywords: [security,path,traversal,realpath,validation]
source: reconstruct
authored-by: skein-spec
created: 1784346589
status: active
related: []
updated: 1784346589
---

## 铁律

- MUST：任何读/写端点先用 `Path(p).resolve()` 获 realpath
- MUST：检查 realpath 是否在允许根（如 `.skein/spec/`）的 parents 内，不在则 403
- MUST：禁字符串拼接 path，用 pathlib 处理
- MUST：防范 `../../../etc/passwd` 等穿越

## 反例表

| 禁 | 改为 |
|---|---|
| 直接拼接 root + user_path | Path.resolve() + 父目录检查 |
| os.path.join(...) 拼接 | pathlib.Path(...).resolve() |
| 不检查父目录 | 检查 `root in realpath.parents` |
| /spec/file?path=../../../../etc/passwd | 穿越检查失败返回 403 |
