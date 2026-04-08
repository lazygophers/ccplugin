---
description: "探索项目依赖：分析依赖树、检测安全漏洞(CVE/供应链攻击)、评估版本锁定策略、验证许可证合规。当需要审计依赖安全、理解依赖关系、检查过时包时触发。支持npm/pip/go mod/Maven/Cargo等。"
model: sonnet
user-invocable: false
agent: task:explorer-dependencies
hooks:
  SessionStop:
    - hooks:
        - type: command
          command: "PLUGIN_NAME=task uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks_skills"
  SubagentStart:
    - hooks:
        - type: command
          command: "PLUGIN_NAME=task uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks_skills"
---


# Skills(task:explorer-dependencies) - 依赖探索

分析项目依赖：依赖树/安全漏洞/版本管理/许可证合规。支持npm/yarn/pnpm/pip/poetry/uv/go mod/Maven/Gradle/Cargo。

## 核心原则

安全优先(CVE/恶意包/供应链) | 区分直接vs间接依赖 | 分析版本锁定策略 | 确保许可证兼容

## 识别模式

| 包管理器 | 配置文件 | Lock文件 |
|---------|---------|---------|
| npm | `package.json` | `package-lock.json` |
| yarn | `package.json` | `yarn.lock` |
| pnpm | `package.json` | `pnpm-lock.yaml` |
| pip | `requirements.txt` | — |
| poetry | `pyproject.toml` | `poetry.lock` |
| go mod | `go.mod` | `go.sum` |
| Maven | `pom.xml` | — |
| Cargo | `Cargo.toml` | `Cargo.lock` |

Monorepo：Lerna(`lerna.json`) | Nx(`nx.json`) | Turborepo(`turbo.json`) | pnpm workspace

## 输出格式

JSON含：`package_manager{name,lock_file,config}` + `dependencies{direct,dev,transitive,total,duplicates}` + `security{vulnerabilities{critical,high,medium,low}}` + `outdated[]` + `licenses{}` + `summary`

## 工具指南

分析：`npm ls --json` | `pip list --format=json` | `go list -m all` | `cargo tree --depth 1`
审计：`npm audit --json` | `pip-audit --format=json` | `govulncheck` | `cargo audit --json`
过时：`npm outdated --json` | `pip list --outdated` | `go list -m -u all`

## 指南

先识别包管理器 | 优先用lock文件 | 按严重级别排序审计结果 | 注意Monorepo场景

