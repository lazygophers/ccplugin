# PRD — frontmatter + tag schema 规范 + skills/agents 对齐

## 背景

vault 文件按目录归类, 但每目录的 **frontmatter schema** 和 **tag 约定** 不统一:
- 项目笔记 / 来源剪藏 / 领域概念 / 日记 / 反思 / 记忆 各应有不同字段
- tag 命名未规约 (`#技术`, `#tech/go`, `#go` 混用)
- 搜索 (cortex_search) + 链接 (cortex_linker) 难精准 join

User 要求: 每目录定义 frontmatter + tag 规范, 让内容更易关联 / 标签搜索更准。

## 目标

1. 定义 `_meta/frontmatter-schema.yaml` (新), 列每目录 frontmatter required/optional + tag 命名约定
2. 更新 templates/knowledge/ 已有 15 模板的 frontmatter 与 schema 对齐
3. 更新 skills/cortex-{save, ingest, new, memory} 让落档时按 schema 填
4. 更新 agents/cortex-{linker, curator, summarizer} 用 schema 做链接/校验/总结
5. lint 加 `frontmatter-schema-violation` 规则 (autofix=true)

### 不在范围
- 不强制迁移老 vault 笔记 (lint 报警 + 用户决定)
- 不动 SessionStart / UserPromptSubmit hook
- 不动模板内容主体 (仅 frontmatter 调)

## 设计

### 1. `_meta/frontmatter-schema.yaml` (vault 安装时复制源)

源放 `plugins/tools/cortex/templates/frontmatter-schema.yaml`:

```yaml
version: 1
description: cortex vault 每目录 frontmatter + tag 规范
namespaces:
  知识库:
    项目:
      required: [type, title, created, status]
      optional: [tags, updated, owner, started, ended, links]
      defaults:
        type: project
        status: active   # active | paused | done | archived
      tags_required: ["project/<slug>"]
      tags_optional: ["domain/<area>", "stack/<tech>"]
      filename_pattern: "<slug>.md"
    来源:
      代码仓库:
        required: [type, title, source_kind, host, org, repo, url, created]
        optional: [tags, stars, language, last_synced, license]
        defaults:
          type: source
          source_kind: repo
        tags_required: ["source/repo", "host/<host>"]
        tags_optional: ["lang/<language>", "topic/<area>"]
      网页:
        required: [type, title, source_kind, domain, url, created]
        optional: [tags, author, published, archive_url]
        defaults:
          type: source
          source_kind: web
        tags_required: ["source/web", "domain/<domain>"]
      论文:
        required: [type, title, source_kind, year, created]
        optional: [tags, authors, doi, arxiv, venue]
        defaults:
          type: source
          source_kind: paper
        tags_required: ["source/paper", "year/<year>"]
      书籍:
        required: [type, title, source_kind, author, created]
        optional: [tags, isbn, year, publisher]
        defaults:
          type: source
          source_kind: book
        tags_required: ["source/book"]
    领域:
      "*":   # 通配, 适用 7 大领域所有子目录
        required: [type, title, domain, created]
        optional: [tags, prerequisites, related, evidence, confidence]
        defaults:
          type: concept   # concept | method | fact
        tags_required: ["domain/<domain-path>"]   # e.g. domain/技术/编程语言/Go
        tags_optional: ["concept/<name>", "method/<name>"]
    日记:
      "*":
        required: [type, date, created]
        optional: [tags, mood, weather, summary]
        defaults:
          type: journal
        tags_required: ["journal/<period>"]   # journal/日, journal/周, journal/月, journal/年
        filename_pattern: "YYYY-MM-DD.md | YYYY-Wnn.md | YYYY-MM.md | YYYY.md"
    反思:
      洞察:
        required: [type, title, created]
        defaults: {type: insight}
        tags_required: ["reflect/insight"]
        tags_optional: ["domain/<area>"]
      连接:
        required: [type, title, from_domain, to_domain, created]
        defaults: {type: connection}
        tags_required: ["reflect/connection"]
      疑问:
        required: [type, title, status, created]
        defaults: {type: question, status: open}   # open | resolved
        tags_required: ["reflect/question"]
    收件箱:
      "*":
        required: [type, title, created]
        defaults: {type: inbox}
        tags_required: ["inbox"]
  记忆体系:
    L0-核心:
      "*":
        required: [uri, level, weight, created, immutable]
        optional: [tags, ref, recall_when, parents, children]
        defaults:
          level: L0
          immutable: true
          needs_user_confirm: true
        tags_required: ["memory/L0"]
    L1-长期:
      procedural:
        required: [uri, level, weight, recall_when, created]
        defaults: {level: L1}
        tags_required: ["memory/L1", "memory/procedural"]
      semantic-stable:
        required: [uri, level, weight, recall_when, created]
        defaults: {level: L1}
        tags_required: ["memory/L1", "memory/semantic-stable"]
    L2-中期:
      semantic:
        required: [uri, level, weight, recall_when, created, expires]
        defaults: {level: L2}
        tags_required: ["memory/L2", "memory/semantic"]
    L3-短期:
      episodic:
        required: [uri, level, weight, created, expires]
        defaults: {level: L3}
        tags_required: ["memory/L3", "memory/episodic"]

tag_naming:
  format: "namespace/<value>"
  separator: "/"
  case: lowercase
  allowed_chars: "a-z0-9-/.中文"
  examples:
    - "project/cortex"
    - "domain/技术/编程语言/Go"
    - "source/repo"
    - "host/github.com"
    - "memory/L1"
    - "journal/日"
```

### 2. 更新 templates/knowledge/ frontmatter

15 模板对照 schema 调:
- 已含基础 frontmatter (type/title/created), 加 `tags` 默认值
- 加 `## Tags` section 提示规范
- 不动正文

### 3. 新增 SKILL: `cortex-schema`

`plugins/tools/cortex/skills/cortex-schema/SKILL.md`:
- 提供 `read <path>` 返回该路径应用的 schema (按 namespaces 嵌套匹配)
- `validate <file>` 验证文件 frontmatter 符合 schema → 列差异
- `fill <file>` 补缺 required 字段 (用 defaults)
- 其它 SKILL 调用此 SKILL 做 schema 操作

### 4. 更新现有 SKILL

| SKILL | 改动 |
|-------|------|
| cortex-save | 落档前调 cortex-schema 取 schema 填 frontmatter + tags_required |
| cortex-ingest | URL/file → 知识库/来源/ 时按 source_kind 走对应 schema |
| cortex-memory | write 时按 level 取 schema 自动填 uri/level/weight |
| cortex-search | 召回时支持 tag filter (e.g. `tag:domain/技术/Go`) |

### 5. 更新现有 Agent

| Agent | 改动 |
|-------|------|
| cortex-linker | 用 tags_required 做 link 推荐 (e.g. `tag:source/repo` + `host/github.com` 自动连到 项目/) |
| cortex-curator | 跑 frontmatter-schema-violation lint, 给修复建议 |
| cortex-summarizer | 长页 TL;DR 时按 schema 提取关键字段 (e.g. 项目 schema → 提取 status/owner) |

### 6. lint 新规则: `frontmatter-schema-violation`

`lint/run.py`:
- 新 helper `_load_frontmatter_schema(vault)` 读 `<vault>/_meta/frontmatter-schema.yaml` (fallback plugin)
- 新 helper `_resolve_schema_for_path(rel_path, schema)` 按 namespaces 嵌套匹配 (longest prefix)
- `_check_frontmatter_schema(file_path, schema)`:
  - 缺 required → warn + autofix (用 defaults 填)
  - 缺 tags_required → warn + autofix (加 tag)
  - 多余字段 → info (不强制)
- 加 fix 函数 `_fix_frontmatter_schema` 调 yaml lib 修改

### 7. install SKILL 更新

`cortex-install` SKILL §流程 §4 加复制 `<plugin>/templates/frontmatter-schema.yaml` → `<vault>/_meta/frontmatter-schema.yaml`。

`meta-missing` lint 规则 (上次任务加的) 加 frontmatter-schema.yaml 到检测列表。

## 实施步骤

1. 新建 `plugins/tools/cortex/templates/frontmatter-schema.yaml` (按 PRD §1)
2. 更新 `cortex-install` SKILL §4 复制项
3. 更新 `lint/run.py`:
   - 加 frontmatter-schema-violation 规则 + autofix
   - 更新 _check_meta_missing 加 frontmatter-schema.yaml
4. 新建 `skills/cortex-schema/SKILL.md`
5. 更新 4 SKILL (cortex-save / ingest / memory / search) 引用 cortex-schema
6. 更新 3 Agent (cortex-linker / curator / summarizer) 引用 schema
7. 更新 15 个 templates/knowledge/ frontmatter 加 tags 默认
8. 单元测试 (frontmatter-schema 解析 + lint 规则 + autofix)

## 验收

- [ ] `_meta/frontmatter-schema.yaml` 模板存在, YAML 合法
- [ ] vault 装后 _meta/ 含 frontmatter-schema.yaml
- [ ] `cortex-schema` SKILL 存在 (read/validate/fill 3 verb)
- [ ] 4 SKILL + 3 Agent 引用 schema
- [ ] lint 加 frontmatter-schema-violation, 跑 mock vault 检测缺 required / tags_required
- [ ] lint --fix 跑后 frontmatter 自动补缺
- [ ] 15 templates/knowledge/ frontmatter 含 tags
- [ ] 258 + 新测试 PASS

## 风险

| 风险 | 缓解 |
|------|------|
| schema 太严, 老笔记全 warn | autofix=true 自动补缺, 不破坏 |
| 嵌套 namespace 匹配复杂 | longest-prefix 算法, 加单元测试 |
| tag 命名约定与用户旧 tag 冲突 | 仅强制 tags_required, optional 不动 |
| yaml 解析需 PyYAML | cortex 已用 PyYAML (lint), 复用 |

## 子任务

8 步骤拆 2 wave 并行 (≤2 agent):

**Wave A** (数据 + lint):
- A1: Step 1 + 2 + 3 (schema yaml + install SKILL + lint 规则/autofix)
- A2: Step 7 + 8 部分 (15 templates frontmatter + 测试基线)

**Wave B** (skills/agents 对齐):
- B1: Step 4 + 5 (cortex-schema + 4 SKILL update)
- B2: Step 6 + 8 完整测试 (3 Agent + 新测试)
