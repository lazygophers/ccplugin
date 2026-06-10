# writeback — 回填 + 归类

走兜底拿到的答案 (互联网 / 用户; 见 `fallback.md`) → 自动回填知识库, 下次可直接 recall 命中. **命中 vault 的不回填** (本来就有). 不自建写逻辑 — 调 cortex-extract / cortex-save 落盘.

## 步骤

### 1. 归类 scope (复用 cortex-context-digest scope 规则)

| # | 信号 | 落点 vault |
| --- | --- | --- |
| 1 | 含当前 repo 名 / 仓库路径 / 具体文件 / 项目私有约定 | **项目级** `<repo>/.wiki/` |
| 2 | 跨项目通用 (通则 / 方法 / 外部技术知识) | **全局** `~/.cortex/.wiki/` |
| 3 | 兜底 / 不确定 | **项目级** (保守, 防误升污染全局) |

规则与 `cortex-context-digest/references/scope.md` 一致, 不重写.

### 2. 定级别 + 模块 (复用 cortex-extract 三轴 / cortex-schema 路径)

| 答案类型 | 目标 | 备注 |
| --- | --- | --- |
| 外部技术知识 | `领域/<area>/<sub>/` | 通用技术沉淀 |
| 外部 repo / website | `项目/<host>/<owner>/<repo>/` | **仅全局** (项目级 vault 无 项目/ 模块) |
| 记忆类 (决策 / 规则 / 临时) | `memory/`, **默认 L3-short** | 短期最易遗忘, 后续 evolve 升降 |

升级方向 = 抗遗忘 (L3→L2→L1→L0), 由 cortex-evolve 后续处理; 回填不主动升级.

### 3. 写入

- **默认自动写** (用户发起 recall 即授权回填, 无需再确认)
- **例外: L0/L1 写入仍 ask** (cortex-schema 硬规) — 回填默认落 **L3-short**, 不自动进 L0/L1; 即使命中 L0 触发词也只 mark 候选 + ask 用户
- **互联网答案必带 frontmatter `source: <URL>`** (来源可溯); 用户答案注明来源 = 用户口述

### 4. 落盘

调既有工具, 不自写:

- 多条 / 需三轴路由: `cortex-extract --apply --target <vault-by-scope>`
- 单条快存: `cortex-save`

`<vault-by-scope>` = 步骤 1 判定的 `$HOME/.cortex` (全局) 或当前 repo 根 (项目级).

## 与既有 skill 边界

| skill | 职责 |
| --- | --- |
| cortex-recall (本) | 搜 + 兜底 + 回填闭环 (查不到主动补) |
| cortex-extract | L4-inbox 内部已收件资料路由分级 (回填的落盘执行者) |
| cortex-context-digest | 整理当前会话上下文沉淀 |

recall 回填默认 L3-short (易遗忘, 交 evolve 升降); 不污染 L0/L1.
