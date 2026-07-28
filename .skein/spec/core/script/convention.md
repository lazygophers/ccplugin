---
title: convention
layer: core
category: script
keywords: [cli,script,shebang,docstring,subprocess,safety,timeout,isolation,fts,衍生文件,backlinks,glob排除,测试断言]
status: active
---

## CLI 脚本首行 shebang + 模块 docstring

### 触发场景
新建 CLI 脚本。

### 陷阱-正解
**陷阱**：无 shebang，或缺 docstring。
**正解**：首行 `#!/usr/bin/env python3`，紧随模块级 docstring。

### 规则
8/8 脚本一致（check.py:1-2 等）。

## subprocess 设 timeout/cwd/capture_output

### 触发场景
exec 端点运行白名单命令。

### 陷阱-正解
**陷阱**：子进程无限卡、无输出捕获、路径污染。
**正解**：timeout=60 超时，cwd=root 隔离，capture_output=True 捕获。

### 规则
skein.py:2282-2287 完整示例。

### 关联
ops/subprocess-safety

## 衍生文件排除范式

### 衍生文件排除范式

### 铁律

MUST：新增衍生文件（如 `backlinks.md` 或 `.recall.db`）必须在 `_rule_files` glob 中排除

MUST：排除的衍生文件也必须在测试断言中排除，否则 FTS 索引/反链扫描会把衍生文件当作规则处理

MUST：防止递归自引用：衍生文件不应被索引为规则本身

### 反例表

| 禁 | 改为 |
|---|---|
| `_rule_files = ["*.md"]` 包含衍生文件 | `_rule_files = ["*.md", "!backlinks.md"]` 显式排除 |
| 测试断言包含衍生文件 | 测试断言也加 `!= "backlinks.md"` 等排除逻辑 |
| FTS 把衍生文件当规则 | 在 glob pattern 中排除衍生文件 |

### 关联
- FTS5 索引设计
- 测试断言完整性
