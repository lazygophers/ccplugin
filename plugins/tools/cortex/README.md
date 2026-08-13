# cortex

> 知识库 + 记忆管理插件: 双层同构 vault (`~/.cortex/.wiki/` + `<repo>/.wiki/`), 5 级记忆按遗忘曲线分级, 3 模块知识库 (projects/domains/scripts), lint + extract 自动化.

## 概述

cortex 提供与具体 vault 解耦的双层同构契约, 任何项目都能复用:

- **用户级**: `~/.cortex/.wiki/` (跨项目沉淀)
- **项目级**: `<repo>/.wiki/` (项目专属事实)

两层内部结构完全一致, 同一套 skill + 脚本两边跑.

记忆按 **Ebbinghaus 遗忘曲线** 分 5 级: L0 核心 / L1 长期 / L2 中期 / L3 短期 / L4 收件箱. 升级方向 = 抵抗遗忘 (L3 → L2 → L1 → L0). 默认新条目入 L3-short, 复用足够多才 promote 上去.

## 组件

| 类型 | 路径 | 触发 |
| --- | --- | --- |
| Agent | `agents/cortex.md` | "维护知识库 / 整理记忆 / 校验 vault / 提取 inbox" 类请求 (前台主协调) |
| 后台 Worker | `agents/cortex-{lint,history,evolve,extract,ingest}-worker.md` | `background: true`; 被对应 skill `context: fork` 启动; 只读扫描 + 跑脚本 (脚本默认 apply 直接落盘) |
| Skill `cortex-schema` | `skills/cortex-schema/SKILL.md` | "知识库 / vault / projects / domains / scripts / 入库 / 归档 / schema / 记忆 / memory / L0-L4 / 永远 / 暂时 / 记住 / 忘了 / 遗忘 / 等级" |
| Skill `cortex-ingest` | `skills/cortex-ingest/SKILL.md` | "ingest / 抓取 / import / build / GitHub / GitLab / website / local dir" |
| Skill `cortex-lint` | `skills/cortex-lint/SKILL.md` | "lint / 校验 / 体检 / audit / 死链 / 孤儿 / 规范化 / frontmatter" |
| Skill `cortex-extract` | `skills/cortex-extract/SKILL.md` | "extract / 提取 / promote / 整理 / inbox / digest" |
| Skill `cortex-recall` | `skills/cortex-recall/SKILL.md` | "查/搜知识库 / recall / 想想 / 记得 / 查资料 (搜→兜底→回填)" |
| Skill `cortex-history-digest` | `skills/cortex-history-digest/SKILL.md` | "Claude Code 历史 / transcripts / digest ~/.claude/projects" |
| Skill `cortex-context-digest` | `skills/cortex-context-digest/SKILL.md` | "整理上下文 / 沉淀会话 / 任务收尾 / scope global\|project" |
| Skill `cortex-evolve` | `skills/cortex-evolve/SKILL.md` | "升级记忆 / 降级 / promote / demote / 金字塔 / 记忆 audit / 再平衡" |
| 脚本 `validate-layout.sh` | `scripts/validate-layout.sh` | 校验目录契约必备项 |
| 脚本 `ingest.sh` | `scripts/ingest.sh` | GitHub/GitLab/Website/local 输入识别 + 路由 (默认 apply; --dry-run 预览) |
| 脚本 `lint.sh` | `scripts/lint.sh` | 7 规则校验 + R2/R4 autofix |
| 脚本 `extract.sh` | `scripts/extract.sh` | L4-inbox → L1/L2/L3 + projects/domains 路由 |
| 脚本 `history-digest.sh` | `scripts/history-digest.sh` | 扫 ~/.claude/projects jsonl → 学习增量 (默认 apply; --dry-run 预览) |
| Hooks | `hooks/{session-start,user-prompt-submit,stop}.sh` | 轻量注入提示 (不扫/不写盘): SessionStart=vault 概览+缺结构构建提示 / UserPromptSubmit=主动 recall 提示 / Stop=沉淀提示 |
| Commands | `commands/` | 占位 (后续 task) |

## 目录契约

完整契约权威源 (单一真相):
- 目录契约 / 三模块 / 顶层布局 / 同构 / 模板 / 5 级记忆 / 等级映射 / 遗忘曲线: [`cortex-schema`](./skills/cortex-schema/)

摘要:

```
~/.cortex/
├── .wiki/                  ← 用户级知识库根
│   ├── memory/
│   │   ├── L0-core/        ← 永久, 不可违反
│   │   ├── L1-long/        ← 长期 (曲线尾端)
│   │   ├── L2-mid/         ← 中期
│   │   ├── L3-short/       ← 短期 (extract 默认入口)
│   │   └── L4-inbox/       ← 收件箱
│   ├── projects/<host>/<owner>/<repo>/
│   ├── domains/<area>/<sub>/
│   └── scripts/            ← vault 内部脚本
├── config/  state/  scripts/  logs/   ← 后者 = 用户操作入口 CLI
└── <开放扩展位>             ← cache/credentials/templates 等
```

项目级 `<repo>/.wiki/` 与 `~/.cortex/.wiki/` 完全同构.

## 边界

- **可读**: 用户与项目 vault + 插件自身
- **可写**: 仅 `~/.cortex/` 与 `<repo>/.wiki/`
- **只读**: `.trellis/**` + 项目源码非 vault 部分
- **禁触**: `dist/build/generated` 类目录
- **默认 apply 直接落盘** (含 L0-core 写入, 不再 ask); 需预览用 `--dry-run` / `--check`
- **与外部 obsidian vault 独立**, 无路径耦合

## 触发

| 场景 | 触发路径 |
| --- | --- |
| "ingest / 抓 GitHub repo / 导入项目 / build 知识库 / 从 local dir 入库" | `cortex-ingest` |
| "查 / 搜知识库 / recall / 想想 / 记得 / 查资料" | `cortex-recall` |
| "归档 / 整理 inbox / 提取 L4" | `cortex-extract` |
| "整理 Claude Code 历史 / digest transcripts" | `cortex-history-digest` |
| "整理上下文 / 沉淀本次会话 / digest context" | `cortex-context-digest` |
| "升级 / 降级 / promote / demote / 金字塔 / 记忆 audit" | `cortex-evolve` |
| 用户说 "记住 / 永远 / 暂时" | `cortex-schema` 加载 |
| 用户说 "lint / 体检 / 校验 vault" | `cortex-lint` 加载 |
| 多 skill 协作 | `cortex` agent 调度 |

## 安装

通过 ccplugin-market 安装. `plugin.json` 已声明 `CLAUDE_PLUGIN_ROOT` 相对路径, Claude Code 注入根目录即可.
