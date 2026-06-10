# Design — cortex-recall

## skill 结构

```
skills/cortex-recall/
├── SKILL.md (≤ 60 行)
└── references/
    ├── search.md      双层搜索策略 + 多级回退 + 引用格式
    ├── fallback.md    兜底 (WebSearch → 拿不准问用户)
    └── writeback.md   回填 + 归类 (scope 判定 + 级别 + L0/L1 ask)
```

## frontmatter

```yaml
---
name: cortex-recall
description: "知识库搜索 + 兜底 + 回填闭环 — 先搜双层 vault (项目级 <repo>/.wiki + 用户级 ~/.cortex/.wiki); 未命中走兜底 (WebSearch → 拿不准问用户); 答案按 scope 归类 (项目级/全局) 自动回填知识库. 触发: 查/搜知识库/recall/想想/记得/这个怎么."
when_to_use: "查知识库/搜 vault/recall/想想/记得/查资料/这个之前怎么做的/有没有记录过"
argument-hint: "[query]"
arguments: "[查询]"
user-invocable: true
---
```

## SKILL.md 内容

1. frontmatter
2. 1 段总览 (搜→兜底→回填闭环)
3. 流程速查 (4 步 ASCII)
4. 路由表 (3 references)
5. 边界 (vs cortex-extract / context-digest / ingest)
6. 引用 cortex-schema / cortex-extract / cortex-context-digest

## references/search.md (≤ 220)

双层搜索范围 (按优先序):
1. 项目级 `<repo>/.wiki/` (memory L0-L4 + 领域) — 当前项目专属, 优先
2. 用户级 `~/.cortex/.wiki/` (memory + 项目 + 领域 + 脚本) — 跨项目沉淀

多级回退 (工具):
- mcp-obsidian `*_search` (若 vault = obsidian)
- `rg` / grep vault 目录
- 读 hot/index 缓存 (若有)

返回格式: 答案 + 引用 (file:line / wikilink)。命中即返回, 不走兜底。

## references/fallback.md (≤ 220)

未命中 vault → 兜底顺序:
1. **WebSearch** 互联网
   - 拿得准 (来源权威 + 一致) → 用答案, 标 source URL
   - 拿不准 (来源冲突 / 模糊 / 时效性强) ↓
2. **问用户** (AskUserQuestion 或直接提问)
   - 用户答 → 用答案

"拿不准" 判定: 多来源冲突 / 无权威源 / 涉及项目私有约定 (互联网不可能知道) → 直接问用户, 不靠 WebSearch 瞎猜。

## references/writeback.md (≤ 220)

回填 (互联网/用户答案 → vault):
1. **归类 scope** (复用 cortex-context-digest scope 规则):
   - 含当前 repo 名/路径/具体文件 / 项目私有约定 → 项目级 `<repo>/.wiki/`
   - 跨项目通用 (通则/方法/外部技术知识) → 全局 `~/.cortex/.wiki/`
   - 兜底 → 项目级 (保守)
2. **定级别 + 模块** (复用 cortex-extract 三轴 / cortex-schema 路径):
   - 外部技术知识 → 领域模块 (领域/<area>/<sub>/)
   - 记忆类 (决策/规则/临时) → memory, 默认 L3-short
   - 外部 repo/website → 仅全局 项目模块 (项目级无 项目/)
3. **写入**:
   - 默认自动写 (用户要求无需确认)
   - **例外**: L0/L1 写入仍 ask (cortex-schema 硬规); 回填默认落 L3-short, 不自动进 L0
   - 互联网答案必带 frontmatter `source: <URL>`
4. 调 cortex-save / cortex-extract 落盘 (不自建写逻辑)

## 边界 (vs 既有 skill)

| skill | 职责 |
| --- | --- |
| cortex-recall | 搜 + 兜底 + 回填 闭环 (查不到主动补) |
| cortex-extract | L4-inbox 内部已收件资料路由分级 |
| cortex-context-digest | 整理当前会话上下文沉淀 |
| cortex-ingest | 外部 repo/website 主动入库 |
| cortex-schema | 路径/级别契约权威 |

recall 是"查询驱动 + 缺则补"; extract/digest 是"已有资料整理"。

## wire (S2)

- plugin.json skills 数组 +cortex-recall (7→8)
- keywords + recall/search/query
- agent cortex.md 相关 skill 表 +1 行
- README 组件表 + 触发表 +1
- llms.txt skill 列表 7→8
- 根 marketplace.json cortex desc: 7→8 skill

## 资源边界

| Subtask | 写 |
| --- | --- |
| S1 | skills/cortex-recall/** (新建) |
| S2 | plugin.json + agent + README + llms + marketplace.json |
| S3 | 只读验证 + 暂存 |

## 验证

- SKILL.md ≤ 60 + frontmatter 合规
- 3 references 存在
- plugin.json skills==8, marketplace cortex desc 含 8
- 6 既有脚本 smoke (validate/lint/extract/ingest/history-digest + plugin.json JSON)

## Rollback

```bash
git checkout plugins/tools/cortex/{.claude-plugin,agents,README.md,llms.txt} .claude-plugin/marketplace.json
rm -rf plugins/tools/cortex/skills/cortex-recall/
```
