---
name: cortex-plugin-2026-05-13
description: Cortex 插件 2026-05-13 整体重构 — 路径迁移 / AUTO_MODE persistent / slash 冒号 / 全 scripts 集中 / 文档对齐
type: project
---

# Cortex 插件 2026-05-13 整体重构

**Why**: 用户多轮指出冲突 (路径混用、版本号残留、shell 触发仍出确认问句、文档计数失真、MOC 已废仍引用、env var 配置二义)。一次性收尾,把所有不一致拉齐到单一真相。

**How to apply**: 之后任何 cortex 相关改动以本次状态为基线,不要回退到旧约定。

## 单一真相清单

| 项 | 真相 |
|----|------|
| Vault 顶层目录 | `知识库/{项目,来源/{代码仓库,网页,论文,书籍},领域/{...},日记/{日,周,月,年},反思,收件箱}` + `记忆/{L0-核心,L1-长期,L2-中期,L3-短期,L4-流水账,working,views}` + `_meta` `_templates` `_assets` `仪表盘` `归档` |
| 配置 | `~/.cortex/config.json` (keys: vault / lang / settings / install_path / timeout_default) |
| Env var 政策 | 禁配置类 (`OBSIDIAN_VAULT`/`CORTEX_VAULT`/`CORTEX_LANG`/`CORTEX_INSTALL_PATH`/`CORTEX_SETTINGS`); 仅 install.sh bootstrap 期允许; 平台契约保留 (`CLAUDE_PLUGIN_ROOT`, `CORTEX_VAULT_PATH` for MCP, `CORTEX_JOB_LABEL`, `CORTEX_STREAM_TEE_FILE`) |
| Slash 形式 | `/cortex:<name>` (冒号),dash `/cortex-<name>` claude 无法解析 |
| AUTO_MODE 行为 | persistent — 禁询问 ≠ 中止; AI 自决循环执行直至 lint clean 或工具客观失败 |
| 插件路径硬编码 | `$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex` (env var 会有解析 bug) |
| MOC | **已删** — canvas + dashboard 二件套替代 |
| 版本号概念 | **禁** — 删 v2 / v1 / legacy / migration 标记 |

## 实际计数 (与文档对齐)

| 项 | 数 |
|----|----|
| Agent | 8 (`agents/*.md`) |
| Skill | 21 (`skills/<name>/SKILL.md`) |
| Slash command | 20 (`commands/<name>.md`) |
| Bash wrapper | 17 (`~/.cortex/scripts/<name>.sh`) |
| Lint 规则 | 17 (`scripts/lint/rules.json`) |
| Hook | 5 (SessionStart / PostCompact / Stop / SubagentStop / UserPromptSubmit) |
| MCP 工具 | 15 |

## 目录布局 (python/bash 集中到 scripts/)

```
plugins/tools/cortex/
├── install.sh                ← 唯一根级 bash (例外)
├── scripts/                  ← 所有 python/bash 集中
│   ├── cortex_config.py
│   ├── install_cron.sh
│   ├── install_wrappers.sh
│   ├── regen_template_manifest.py
│   ├── cron/  hooks/  lint/  mcp/  refactor/  lib/
├── tests/
├── agents/ commands/ skills/ docs/ presets/ templates/ locales/ styles/
└── .claude-plugin/plugin.json
```

## ingest 全局规则 (folder-first + 深度 + 评分)

- 仓库/项目用**目录**承载: `index.md` 主条目 + ≥4 子文档 (architecture/decisions/pitfalls/dependencies)
- 嵌套 git repo: `find . -name .git ≥2` 时父+子各自独立 ingest
- 深度 L1-L6: 结构/文档/配置/入口码/历史/派生
- 强制 frontmatter: type / title / desc / created / updated / tags(≥3) / source_url / version / when_to_read / score(1-5) / maturity
- tags 强制: ≥3 个,含 `source/<kind>` + `topic/<domain>` + `stack/<lang>`

## 测试基线

- python 238 PASS
- bash 8 files / 11 assertions PASS
- mcp 113 PASS
- **总 359 + 8 全绿**

## 文档分层

- `docs/` — 用户使用 (起步 / 调用方式 / 进阶 / 出问题)
- `docs/_internal/` — 开发者参考 (architecture / design-decisions / hook-protocol / contributing)

## 关键 commit

| Hash | 主题 |
|------|------|
| `4ba4f2b5` | cron dashboard 改 daily (was weekly) |
| `f1fe02a8` | 范围标记改文字 (去 emoji) |
| `66dc8d2c` | 文档清单加范围列 (全局/当前目录/知识库/记忆) |
| `192d050b` | templates/ 移到 presets/seed/_templates/ |
| `32ac08ea` | neat-freak 记忆 + README 计数对齐 |
| `4e5a48ea` | python/bash 全移 scripts/ (install.sh 例外) |
| `59e9d127` | 删 MOC 引用 + install_cron 路径硬编码 |
| `454af37f` | 文档计数对齐 + 内部下沉 |
| `c2a66f53` | 7 类全局不一致 (路径/slash/env/AUTO_MODE/lint/版本号) |
| `3bac2d4b` | AUTO_MODE 改 persistent 自决循环 |
| `e1ab3f6b` | slash dash → colon |
| `73b58bd8` | ingest 全局知识库构建规则 |
| `1e74eb60` | ingest 默认深度分析 PWD |
| `169ba3a1` | cortex_stream stdout 严禁 raw NDJSON |
| `41ced4c3` | cortex_stream 顺序渲染 (去 Live 区) |

## 定时任务最终调度

| Job | 频率 | 时间 |
|-----|------|------|
| `lint.sh` | daily | 01:00 |
| `dashboard.sh` | daily | 02:30 |
| `fold.sh` | weekly Sun | 02:00 |

系统注册方式: install_cron.sh 仅**打印 snippet**, 用户手工 `crontab -e` / `launchctl load` / GHA workflow 三选一启用。当前系统未注册任何 cortex 定时任务。

## 目录布局变化

- `templates/` → `presets/seed/_templates/` (preset 统一提供, vault init 走单一复制流)
- 根目录最终: install.sh / scripts/ / tests/ / agents/ commands/ skills/ docs/ presets/ locales/ styles/ / _manifest.json AGENT.md README.md / .claude-plugin/

## 文档范围标记 (4 类, 文字描述, 禁 emoji)

- **全局** — 系统/用户级 (~/.cortex/, ~/Library/LaunchAgents, marketplace cache, Claude 会话 hook)
- **当前目录** — PWD (wrapper 调用时 cwd, 如 ingest 深度分析)
- **知识库** — vault (~/.cortex/config.json:.vault)
- **记忆层** — 记忆/L0-L4 子树
