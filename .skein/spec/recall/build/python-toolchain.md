---
title: python-toolchain
layer: recall
category: build
keywords: [monorepo,build,pyproject,multi-project,uv,lock,dependency,tool,python,version,3.11,requires-python,entry-point,cli,packaging,setuptools,wheel]
status: active
---

## monorepo 多 pyproject 各自独立

### 触发场景
需要添加新的 Python 子项目（如新 plugin），或更新多项目版本。

### 陷阱-正解
**陷阱**：直接在根 pyproject.toml 添加子项目代码。
**正解**：子项目在独立目录（lib/, plugins/x/）各持 pyproject.toml + .python-version，由 uv.lock 与 update_version.py 协调。

### 规则
构建版本脚本遍历所有子项目目录跑 uv 与版本 bump。

### 关联
build/uv-dependency-management, build/python-version-lock

## uv 依赖管理与锁定

### 铁律

- MUST：依赖解析与同步必须走 `uv lock -U` 和 `uv sync` 命令
- MUST：lockfile 固定名为 `uv.lock`
- MUST：本地子包通过 `[tool.uv.sources]` 字段用 path 引用
- MUST：版本更新脚本必须遍历所有子项目目录调用 uv 命令

### 反例表

| 禁 | 改为 |
|---|---|
| pip install / pip freeze | uv sync / uv lock -U |
| poetry.lock 作锁文件 | 用 uv.lock |
| 本地 lib 用 install -e . | [tool.uv.sources] path 依赖 |
| 仅根目录 uv，不处理子项目 | 脚本遍历各子项目 uv lock/sync |

## Python 3.11 版本统一锁

### 铁律

- MUST：所有 Python 子项目 `pyproject.toml` 中 `requires-python = ">=3.11"`
- MUST：每个 Python 项目根目录有 `.python-version` 文件，内容为 `3.11`
- MUST：包括根项目、lib/、各 plugin/ 子项目均遵守

### 反例表

| 禁 | 改为 |
|---|---|
| requires-python = ">=3.9" | requires-python = ">=3.11" |
| .python-version 缺失 | 创建 .python-version，内容 3.11 |
| 根项目有版本锁但子项目缺 | 所有子项目都有 .python-version |

## CLI 入口经 [project.scripts] 声明（非直接 python 文件）

### 触发场景
新增用户命令。

### 陷阱-正解
**陷阱**：直接 python scripts/xxx.py 或 sys.path 硬编码。
**正解**：[project.scripts] 声明 name="scripts.<mod>:<entry>"；argparse 用 :main，typer 用 :app。

### 规则
pyproject.toml:21-27 完整示例。

## setuptools 打包排除 plugins/lib（子项目独立）

### 触发场景
打包根项目为 wheel。

### 陷阱-正解
**陷阱**：setuptools 把 plugins/ 和 lib/ 打进 wheel。
**正解**：packages.find include=["scripts*"], exclude=["plugins*","lib*"]。

### 规则
pyproject.toml:36-39。
