# Design — cortex plugin: knowledge base + memory management system

## 系统边界

```
插件根: plugins/tools/cortex/                  ← 本 task 改动范围
运行时根 (用户机, 不在改动范围):
  ~/.cortex/                                    ← 用户级 cortex 主目录
    ├── .wiki/                                  ← 用户级知识库根 (与项目 .wiki 同构)
    │   ├── memory/                             ← L0-L4 记忆树 (按遗忘曲线分级)
    │   │   ├── L0-core/                        ← 核心记忆, 不可违反 (永久)
    │   │   ├── L1-long/                        ← 长期记忆 (已沉淀, 几乎不忘)
    │   │   ├── L2-mid/                         ← 中期记忆 (周月级)
    │   │   ├── L3-short/                       ← 短期记忆 (近期, 最易遗忘)
    │   │   └── L4-inbox/                       ← 收件箱, 原始资料未分类
    │   ├── projects/                           ← 项目模块 (GitHub/GitLab/Website 摘要)
    │   ├── domains/                            ← 领域/经验模块 (≥ 2 级目录)
    │   │   ├── tech/...                        ← 至少二级
    │   │   ├── life/...
    │   │   └── finance/...
    │   └── scripts/                            ← 知识库内部脚本 (vault 自治: lint/extract/canvas 生成等)
    ├── config/                                 ← 插件配置 (yaml/json)
    ├── state/                                  ← 增量游标 / 索引缓存
    ├── scripts/                                ← 用户操作入口脚本 (user-facing: cortex-save / cortex-recall CLI 等)
    ├── logs/                                   ← 运行日志
    └── <开放扩展位>                              ← cache/credentials/templates 等

项目根:
  <repo>/.wiki/                                 ← 项目级知识库, 与 ~/.cortex/.wiki 同构
    ├── memory/L0-core ... L4-inbox/
    ├── projects/                               ← 本项目引用的外部 repo/website
    ├── domains/                                ← 本项目专属领域知识
    └── scripts/                                ← 项目知识库内部脚本 (与 ~/.cortex/.wiki/scripts/ 用途一致)
```

**关键决策**: `~/.cortex/scripts/` 与 `~/.cortex/.wiki/scripts/` **同时存在, 用途分离**:
- `~/.cortex/scripts/` = **用户操作入口** (user-facing tools): 用户从 shell 直接调的 CLI 入口 (如 `cortex-save`, `cortex-recall`, `cortex-lint` 包装器), 关注点是"方便人用"。
- `~/.cortex/.wiki/scripts/` = **知识库内部脚本** (vault-internal): 被 lint / extract / cartographer 等流程调用的内部工具 (如 canvas 生成器、frontmatter 规整器), 关注点是"vault 自治"。

项目级 `<repo>/.wiki/scripts/` 等同于 `~/.cortex/.wiki/scripts/` 的项目专属版本 (知识库内部脚本)。**项目级不设 `.cortex/scripts/`**: 用户操作入口仅在用户级。

**记忆等级语义按遗忘曲线设计** (不按"L0 最重要 → L4 最不重要" 而按"易遗忘程度"):
- L0 = 核心 (永久, 与遗忘曲线无关)
- L1 = 长期 (Ebbinghaus 曲线尾端, 已稳固)
- L2 = 中期
- L3 = 短期 (Ebbinghaus 曲线头端, 最易遗忘)
- L4 = 收件箱 (未进入曲线, 待分类)

## 模块表

| 模块 | 文件 | 执行层 | 资源 (读 / 写) | 输入 | 输出 |
| --- | --- | --- | --- | --- | --- |
| 目录契约 | `docs/layout.md` | doc | 写: 自身 | — | 文档 |
| 布局校验脚本 | `scripts/validate-layout.sh` | bash | 读: target dir; 写: stdout | `--target <dir>` | 0 / 非 0 + 报告 |
| schema-knowledge skill | `skills/cortex-schema-knowledge/SKILL.md` | skill | 写: 自身 | — | skill |
| schema-memory skill | `skills/cortex-schema-memory/SKILL.md` | skill | 写: 自身 | — | skill |
| lint skill | `skills/cortex-lint/SKILL.md` | skill | 调用 lint.sh | — | skill |
| lint 脚本 | `scripts/lint.sh` | bash + python3 | 读: target vault; 写: stdout (默认) / target (with --fix) | `--target` `--check` `--fix` | 报告 / 修复 diff |
| extract skill | `skills/cortex-extract/SKILL.md` | skill | 调用 extract.sh | — | skill |
| extract 脚本 | `scripts/extract.sh` | bash + python3 | 读: L4 inbox; 写: L1-L3 / projects / domains | `--target` `--dry-run` (默认) / `--apply` | 归档计划 / 实落盘 |
| cortex agent | `agents/cortex.md` | agent | 协调 4 skill | dispatch prompt | agent 输出 |
| plugin.json | `.claude-plugin/plugin.json` | config | 写: 自身 | — | 注册清单 |

## 契约: 知识库三模块路径规则

| 模块 | 路径 (用户级) | 路径 (项目级) | 命名 | 必备 frontmatter |
| --- | --- | --- | --- | --- |
| projects | `~/.cortex/.wiki/projects/<host>/<owner>/<repo>/` | `<repo>/.wiki/projects/<host>/<owner>/<repo>/` | host=github.com\|gitlab.com\|<domain> | `type: project`, `source` (URL), `summary`, `mindmap` (canvas 路径) |
| domains | `~/.cortex/.wiki/domains/<area>/<sub>/...` | `<repo>/.wiki/domains/<area>/<sub>/...` | area ∈ {tech, life, finance, ...}, ≥ 2 级 | `type: domain`, `area`, `tags` |
| scripts (knowledge 模块, vault 内部) | `~/.cortex/.wiki/scripts/<name>.{sh,py}` | `<repo>/.wiki/scripts/<name>.{sh,py}` | kebab-case; 用途=vault 内部自治 (lint/canvas/frontmatter 工具) | sh: shebang + help text; py: docstring + `if __name__` |

**补充 — 用户操作入口脚本** (不属于知识库三模块, 单独治理):
- 路径: `~/.cortex/scripts/<name>.{sh,py}` (**仅用户级**, 项目级不设)
- 用途: 用户从 shell 直接调的 CLI 入口 / 包装器
- 命名: kebab-case, 鼓励 `cortex-` 前缀
- frontmatter 要求与 vault 内部脚本一致, 但不进 knowledge 模块校验范围

## 契约: 记忆五级语义 (按遗忘曲线设计)

升级方向 = 抵抗遗忘的方向: **L3 短期 → L2 中期 → L1 长期 → L0 核心**。
降级方向 = 遗忘方向: L1 → L2 → L3 → forget。L0 与 L4 不进入升降级流程。

| 级别 | 路径 | 在遗忘曲线位置 | 强度 | 复用面 | 写入触发 | 自动迁移 |
| --- | --- | --- | --- | --- | --- | --- |
| L0 | `memory/L0-core/` | 不进入曲线 (核心常驻) | 不可违反 | 全局 | 用户显式 "永远 / 硬性 / never / 严禁" | 永不自动降级, 仅手动 forget |
| L1 | `memory/L1-long/` | 曲线尾端 (已稳固, 几乎不忘) | 高 | 跨项目稳定 | L2 promote (访问 ≥ 5 次 + 评分 ≥ 0.8) 或 用户 "永久记住" | ≥ 365d 未访问 → demote 到 L2 (不自动 forget, lint 标记) |
| L2 | `memory/L2-mid/` | 曲线中段 (周月级巩固) | 较高 | 跨任务同领域 | L3 promote (访问 ≥ 3 次 或 用户 "记住") | ≥ 90d 未访问 → demote 到 L3 |
| L3 | `memory/L3-short/` | 曲线头端 (最易遗忘) | 中 | 当前任务/会话 | extract 默认入口 + 用户 "暂时 / 临时" | ≥ 7d 未访问 → forget 候选 (lint 标记, 不自动删) |
| L4 | `memory/L4-inbox/` | 未进入曲线 | 未分类 | 待处理 | 任意来源直落; extract 入口 | extract 处理后 archive (落到 L1/L2/L3) 或 delete |

**轴定义**:
- 抗遗忘度 = 距今最近访问时间窗口的耐受程度 (L1 容忍 365d / L2 容忍 90d / L3 容念 7d 不访问)
- 强度 = 用户标注的"硬度" (L0 强制 / L1 高频引用 / L2 中度 / L3 软提示)
- 复用面 = 触发场景的项目/会话数量

**关键性质**:
- 新写入默认进 L3 (短期, 待遗忘曲线检验); 用户显式 "永远 / 硬性" 才进 L0
- promote 由 lint/extract 离线观察访问统计触发, 不由用户即时口令触发 (即时 "记住" 走 L3 → L2 单跳)
- forget 候选永远只是标记, 不自动删, 由用户审批

## 资源边界 (并行决策表)

| Subtask | 读资源 | 写资源 | 与谁互斥 |
| --- | --- | --- | --- |
| S1 | 既有 plugins/tools/cortex/ | docs/layout.md, scripts/validate-layout.sh | 后续所有 (S2-S7 都依赖) |
| S2 | docs/layout.md | skills/cortex-schema-knowledge/ | 与 S3 不互斥 (不同目录) |
| S3 | docs/layout.md | skills/cortex-schema-memory/ | 与 S2 不互斥 |
| S4 | S2+S3 输出 | skills/cortex-lint/, scripts/lint.sh, tests/fixtures/lint/ | 与 S5 不互斥 |
| S5 | S2+S3 输出 | skills/cortex-extract/, scripts/extract.sh, tests/fixtures/extract/ | 与 S4 不互斥 |
| S6 | S2-S5 输出 | agents/cortex.md, .claude-plugin/plugin.json | 与所有互斥 (plugin.json 是单一文件) |
| S7 | 全部 | tests/fixtures/e2e/ 只写 fixture, 不动其他 | 串行收口 |

## 验证契约

| Subtask | 验证命令 |
| --- | --- |
| S1 | `bash plugins/tools/cortex/scripts/validate-layout.sh --target tests/fixtures/layout-ok/` 退出 0; `--target tests/fixtures/layout-bad/` 退出 ≠ 0 |
| S2 | `python3 -c "import yaml; yaml.safe_load(open('plugins/tools/cortex/skills/cortex-schema-knowledge/SKILL.md').read().split('---')[1])"` 通过, 含 type/area/scripts 三段 |
| S3 | 同上, SKILL.md 含 L0-L4 五段, 含 promote/demote 轴 |
| S4 | `bash scripts/lint.sh --check tests/fixtures/lint/` 报 ≥ 3 类违规; `--fix` 后再 `--check` 退出 0 |
| S5 | `bash scripts/extract.sh --dry-run tests/fixtures/extract/` 输出 JSON 含 plan 字段; `--apply` 后 inbox 清空, 目标位置出现新文件 |
| S6 | plugin.json JSON 校验通过; `skills` 数组 len == 4; `agents` 数组 len == 1; agent frontmatter 含 tools/model/permissionMode |
| S7 | E2E: 跑 validate-layout → lint → extract → validate-layout 全通过 |

## Review Gate

**G1 (S6 后, S7 前)**: 用户必须审:
1. 三模块命名是否需要调整 (projects/domains/scripts 是否合用户口味)
2. L1/L2/L3 时效轴阈值 (7d/90d/365d) 是否合理
3. plugin.json 中 4 skill 的 description 触发词是否能命中实际使用场景

用 AskUserQuestion 走门, 不接受纯文本 "可以"。

## Rollback Points

- S1 失败: 仅删 docs/layout.md + scripts/validate-layout.sh, 骨架仍可用
- S2/S3 失败: 删对应 skills/ 子目录, 不影响 S1
- S4/S5 失败: 删对应 skill + script + fixture, 不影响 S2/S3
- S6 失败 (plugin.json 改坏): `git checkout plugins/tools/cortex/.claude-plugin/plugin.json` 回滚到骨架版本
- S7 失败: 只是 fixture 错, 修 fixture 即可, 不需回滚生产代码

## 与既有系统的交互

- **不修改** `~/.claude/CLAUDE.md` / `~/.cortex/` (用户机器现有数据)
- **不依赖** 外部 obsidian vault (本插件契约独立)
- **不实现** SessionStart / UserPromptSubmit hook (留 hooks/ 占位, 后续 task)
- **不注册** slash commands (留 commands/ 占位)
- plugin.json 中 `hooks: {}` `commands: []` 保持空
