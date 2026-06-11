---
name: cortex-lint
description: lint / 校验 / 体检 / audit / 死链 / 孤儿 / 规范化 / frontmatter — cortex 知识库与记忆树的合规检查与可逆 autofix。覆盖 wikilink 死链、frontmatter 缺字段、命名违规、目录同构、孤儿页、等级语义反写、脚本目录用途混淆等 7 类规则。默认 --fix 落盘修复；--check opt-in 仅预览。
when_to_use: "lint/体检/校验 vault/audit; 整理 .wiki/ 前先跑; 排查死链/孤儿; frontmatter 补齐; memory 5 级目录核对; extract 前的形态检查"
argument-hint: "[--check|--fix] [target]"
arguments: "[--check|--fix] [路径]"
user-invocable: true
disable-model-invocation: true
context: fork
agent: cortex-lint-worker
---

# cortex-lint

cortex vault 的 7 类合规检查与可逆 autofix。默认 `--fix` 落盘修复；`--check` opt-in 仅预览。

> 破坏性提示：默认 `--fix` 会改 vault (autofix R2/R4 等可修项)；只想看违规不落盘时显式传 `--check`。

## 后台执行段 (cortex-lint-worker 执行)

本段由 `context: fork` 派 `cortex-lint-worker` 后台跑：默认 `--fix` 跑 7 规则扫描 + autofix 落盘，产出修复报告。

```bash
plugins/tools/cortex/scripts/lint.sh [--rules R1,R2,...] [--target <dir>]
```

默认 `--fix` + 全规则；`--target` 默认 `$HOME/.cortex`；退出 0=全部 error 已修/无 error，非 0=fix 失败。worker 默认直接落盘 autofix (R2/R4 可修项)，把修复/残留清单 (规则 ID / 文件 / 级别 error|warn / 是否已修) 作为报告返回主会话。

仅预览 (不落盘) 时显式传 `--check`：

```bash
plugins/tools/cortex/scripts/lint.sh --check [--rules R1,R2,...] [--target <dir>]
```

## 7 规则速查

| ID | 规则 | 级别 | autofix |
| --- | --- | --- | --- |
| R1 | wikilink 死链 | warn | 否 |
| R2 | frontmatter 必备字段 | error | 是 (按路径推断) |
| R3 | 命名 (领域 ≥2 级, 脚本 kebab) | warn | 否 |
| R4 | 同构 (memory L0-L4 + 三模块齐全) | error | 是 (mkdir) |
| R5 | 孤儿页 (无反链 + mtime>30d) | warn | 否 |
| R6 | 等级语义一致 (路径↔level) | error | 否 |
| R7 | 脚本目录用途分离 | warn | 否 |

`error` 命中即非零退出且机器可修；`warn` 仅打印。

## 何时读哪个 reference

| 任务 | 文件 |
| --- | --- |
| 查 7 规则具体定义 / 检测策略 | `references/rules.md` |
| 查 R2 推断 / R4 mkdir / lint.sh + _lint/ 实现 | `references/fixers.md` |
| 查 stdout/stderr 格式 + fixture + 验证命令 | `references/output.md` |

## 引用

- 目录契约权威: `cortex-schema` (顶层 + 三模块 + 5 级)
- 三模块 schema: `cortex-schema`
- 记忆等级 schema: `cortex-schema`
- extract (lint 通过后跑): `cortex-extract`
