# PRD — novelist 插件 lint skill + 应用修复

## Goal

novelist 插件缺 lint。新建 `novelist-lint` skill (专属) + 独立 `lint.py` 脚本校验插件目录结构/文件名/文件夹组织是否符合规范; 跑 lint 把违规项移/改/删到合规。lint 不依赖现有 `scripts/check.py` (独立)。

## What I already know

- 规范源: `docs/plugin-development.md` §重要规则 + §测试验证
  - `commands/`/`agents/`/`skills/` 必须在插件根目录, 不在 `.claude-plugin/` 内
  - `SKILL.md` 文件名必须大写
  - `plugin.json` 必须含 `name` 字段, 匹配 `^[a-z0-9-]+$`
- novelist 现状:
  - 13 个 skill (novelist-{character,check,craft,design,humanize,init,outline,pipeline,proofread,rewrite,trending,worldview,write}), 全 kebab-case + 含 SKILL.md ✓
  - 7 个 agent (continuity-auditor/chapter-writer/proofreader/humanizer/outliner/worldbuilder/indexer), kebab ✓
  - `skills/.darwin-results.tsv` = 测试产物泄漏 (要删)
  - `skills/novelist-pipeline/workflow.js` 在 skill 根 (用户裁定: 保留原位)
  - `plugin.json` agents 路径用 `./agents/X.md`, skills 用 `./skills` ✓
- 现有 `scripts/check.py` 有 bug (line 470 检查 `skills.bak` 非 `skills`), 用户裁定: 新建独立 lint.py 不碰 check.py

## 范围边界

- **改/新建**:
  - 新建 `plugins/tools/novelist/skills/novelist-lint/SKILL.md`
  - 新建 `plugins/tools/novelist/skills/novelist-lint/scripts/lint.py`
  - 新建 `plugins/tools/novelist/skills/novelist-lint/references/lint-rules.md`
  - 删 `plugins/tools/novelist/skills/.darwin-results.tsv`
  - 加 `.gitignore` 规则防 `.darwin-results.tsv` 再进 (若仓库 .gitignore 未覆盖)
- **不改**:
  - `scripts/check.py` (独立, 不碰)
  - `workflow.js` (保留原位)
  - 其他 12 个 skill / 7 个 agent (合规)
- lint 范围 = novelist 插件目录 (`plugins/tools/novelist/`), 校验对象 = 目录结构 + 文件名 + 文件夹组织

## Deliverable 矩阵

| ID | 交付 | 验收 |
|---|---|---|
| D1 | `lint.py` 实现 7 规则 (R1-R7), 输出违规清单 (rule/severity/file/message) | `python3 lint.py <plugin-dir>` 跑通, 输出结构化结果 |
| D2 | `lint-rules.md` 文档化 7 规则 (定义+示例+修复指引) | 每规则含 before/after 示例 |
| D3 | `SKILL.md` 描述何时触发 + 怎么调 lint.py + 怎么解读结果修违规 | frontmatter 合规; description 前置触发词; 含调用示例 |
| D4 | 应用 lint 到 novelist: 删 .darwin-results.tsv; 验证其余全 pass | 跑 lint novelist, 仅 R5 .darwin-results.tsv 报 warning → 删后再跑全 pass |
| D5 | 质检: claude -p 验模型识别 lint skill 触发条件 + 调用方式 | 返回正确调用语义 |

## 调度图

单链, main 同步 (skill 文档 + 脚本, 上下文密集):

```mermaid
graph LR
    D1-->D2-->D3-->D4-->D5
```

## 验收标准

- `lint.py` 7 规则全实现, 对 novelist 跑: 删 .darwin-results.tsv 后全 PASS
- lint.py 可对任意插件目录跑 (参数化 `--plugin-dir`)
- SKILL.md frontmatter name/description/when_to_use 合规
- claude -p 质检: 模型读 SKILL.md 知道何时触发 + 怎么调
- .darwin-results.tsv 删除 + .gitignore 加规则
- 不碰 check.py / workflow.js

## Open Questions

无 (4 决策点已 AskUserQuestion 定)。
