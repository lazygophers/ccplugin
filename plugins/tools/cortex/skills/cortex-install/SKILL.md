---
name: cortex-install
description: 初始化 vault — 双 namespace (知识库 + 记忆 L0-L4) + 仪表盘 + 归档; lang (zh-CN/en/ja); 询问 9 cron。仅显式触发 ("init vault" / "安装 cortex")。
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Glob AskUserQuestion mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content
---

# cortex-install

把一个 (新或既有) Obsidian vault 初始化为 cortex 标准布局 — **双 namespace** (知识库 + 记忆 L0-L4) + 仪表盘 + 归档 + HTML 片段库 + 9 cron jobs。

## 触发场景

- 用户初次安装 cortex, 需要把空 vault 起骨架
- 已有 vault 需补 `_meta/` / `_templates/` / 新结构

## 设计总览

### 顶层结构

```
vault/
├── _meta/                       元数据 (version/policy/lint-baseline/uri-index/migrations)
├── _templates/                  模板 (含 html/ memory/ knowledge/ 子目录 + 8 既有 _index/concept/...)
├── _assets/                     图片/svg/HTML 复用资源
├── 主页.md                      全局入口 (HTML 二维仪表盘)
├── 焦点.md                      当前焦点 working set
├── 知识库/                      人类组织维度
├── 记忆/                    AI URI 寻址 + L0-L4 分级
├── 仪表盘/                      格式化看板 (HTML)
└── 归档/                        冷藏
```

### 知识库 (人类视角)

```
知识库/                                  仅 4 子目录
├── 项目/<host>/<org>/<repo>/             github/gitlab + 本地项目 (本地走相对 $HOME 路径策略, 不足 3 段补 `_local`)
├── 领域/<域>/                            域名由用户/AI 自决创建 (创作/学习/工作/技术/生活/金融/未分类/...; 域下结构自由)
├── 日记/日/<YYYY-MM>/<YYYY-MM-DD>.md     仅日维度 (周/月/年 已废弃 — 历史数据归档到 归档/日记/<YYYY-QN>.md 季度桶)
└── 收件箱/                               落档兜底, 等 digest 分发到 项目/笔记 或 领域/<域>
```

域名不固化, 用户/AI 落档时自决建创建。

### 记忆 (AI URI 寻址 L0-L4)

```
记忆/
├── L0-核心/                     不可篡改 (identity/values/...) — 写入需 user confirm + git tag
├── L1-长期/{procedural,semantic-stable}/   高 weight, 仅用户显式删除
├── L2-中期/semantic/            365 天未召回 → archive
├── L3-短期/episodic/            90 天未召回 → archive
├── L4-流水账/{ledger,sessions}/ append-only; 30 天后 gzip
├── working/                     当前 session (volatile)
└── views/{consolidated}/        派生视图 (recent/hot/candidates/alerts)
```

URI scheme: `L0://identity/me` / `L1://procedural/git-flow` / `L2://semantic/go/goroutine` / `L3://episodic/2026-05-12/T1430` / `L4://ledger/2026-05-12` / `L4://session/claude-code/sess-x`。

## 输入

- vault 路径来自 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/resolve_vault.sh`
- preset 固定 `lyt` (不可选)

## 流程

### 1. 解析 vault

跑 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/hooks/_lib/resolve_vault.sh` 拿绝对路径; 失败则提示用户配置 `OBSIDIAN_VAULT` env 或 `~/.cortex/config.json`。

### 2. 询问 lang

`AskUserQuestion`: 默认 `zh-CN`, 可选 `en` / `ja` / 用户自定义。写入 `_meta/version.json:.lang`。

### 3. 写共享根

固定项 (新建/补齐):

- `_meta/version.json` — `{"preset": "lyt", "lang": "<from Q2>", "preserve_transcript": true, "created": "<UTC ISO>"}`
- `_meta/lint-baseline.json` — `{"exempt": []}`
- `_meta/memory-policy.yaml` — 从 `<PLUGIN_ROOT>/templates/memory-policy.yaml` (或 `<PLUGIN_ROOT>/presets/seed/_meta/memory-policy.yaml` 若存在) 复制; 定义 L0-L4 写入/遗忘/晋级 + recall + 9 cron 配置
- `_meta/uri-index.json` — 空骨架 `{"version": 1, "rebuilt_at": "<UTC ISO>", "count": 0, "entries": {}}`
- `_meta/template-manifest.json` — 复制 `<PLUGIN_ROOT>/templates/_manifest.json` (vault 侧基线, 供 lint `template-outdated` / `seed-outdated` 快速比对; lint 也支持 fallback 到每文件 sha256)
- `_meta/triggers.yaml` — 复制 `<PLUGIN_ROOT>/templates/triggers.yaml` (session_start hook 注入的触发关键词基线; 用户可自由编辑, 已存在则跳过)
- `_meta/frontmatter-schema.yaml` — 复制 `<PLUGIN_ROOT>/templates/frontmatter-schema.yaml` (每目录 frontmatter + tag 规范基线; lint `frontmatter-schema-violation` 与各 SKILL 落档前 schema 填充均依赖此文件; 已存在则跳过)
- `_meta/migrations/` — `mkdir -p` (放 `.gitkeep`)
- `_templates/` — 完整复制 `<PLUGIN_ROOT>/templates/`:
  - 既有: `concept.md` / `entity.md` / `domain.md` / `dashboard.md` / `question.md` / `source.md` / `_index.md`
  - `html/` 子目录 (8 文件): `badge.html` / `card.html` / `timeline.html` / `canvas-heatmap.html` / `progressive-disclosure.html` / `mermaid-flowchart.md` / `mermaid-sankey.md` / `mermaid-mindmap.md`
  - `memory/` 子目录 (6 文件): `L0-core.md` / `L1-procedural.md` / `L1-semantic-stable.md` / `L2-semantic.md` / `L3-episodic.md` / `L4-session.md`
  - `knowledge/` 子目录 (15 文件): `project.md` / `source-{repo,web,paper,book}.md` / `domain-{concept,fact,method}.md` / `journal-{day,week,month,year}.md` / `reflection-{insight,connection,question}.md`
- `index.md` / `hot.md` / `log/_index.md` / `folds/_index.md` — 空骨架 (frontmatter `type: meta`)

### 4. 写业务结构

读 `<PLUGIN_ROOT>/presets/_structure.json` (44 seed_files):

**顶层** (mkdir):
- `知识库/` / `记忆/` / `仪表盘/` / `归档/` / `_assets/`

**知识库子目录** (仅 4 项, 域名不固化):
- `知识库/项目/<host>/<org>/<repo>/` (github/gitlab/本地项目; 本地走相对 $HOME 路径策略, 不足 3 段补 `_local`)
- `知识库/领域/<域>/` (域名由用户/AI 自决创建: 创作/学习/工作/技术/生活/金融/未分类/...; 域下结构自由)
- `知识库/日记/日/<YYYY-MM>/<YYYY-MM-DD>.md` (仅日维度, 周/月/年 已废弃; 历史数据归档到 `归档/日记/<YYYY-QN>.md`)
- `知识库/收件箱/` (落档兜底, 等 digest 分发到 项目/笔记 或 领域/<域>)

**记忆子目录**:
- `记忆/L0-核心/`
- `记忆/L1-长期/{procedural,semantic-stable}/`
- `记忆/L2-中期/semantic/`
- `记忆/L3-短期/episodic/`
- `记忆/L4-流水账/{ledger,sessions}/`
- `记忆/working/`
- `记忆/views/{consolidated}/`

**Seed files** (按 `_structure.json:seed_files[]` 复制 44 文件):
- 根入口 2: `主页.md` / `焦点.md` (`dst_key="."` → vault 根)
- `_meta/memory-policy.yaml` 1
- 知识库 `_index.md` × 24 (项目/来源/领域/日记/反思/收件箱 各层)
- 记忆 `_index.md` × 5 (L0/L1/L2/L3/L4 顶层)
- 仪表盘 stub × 12: `总览.md` / `知识库分布.md` / `记忆-L0-核心.md` / `记忆-L1-长期.md` / `记忆-L2-中期.md` / `记忆-L3-短期.md` / `记忆-L4-流水.md` / `记忆-晋级候选.md` / `记忆-腐化监控.md` / `知识-记忆 桥接.md` / `记忆-cron 状态.md` / `固化流.md`

写入策略见下文 §写入策略。

### 5. 询问 git auto-sync (P5)

若 `<vault>/.git` 存在, **必须**用 `AskUserQuestion` (禁文本式提问) 问 1 single-choice:

- 问: "vault 是 git repo, 是否启用 Stop hook 自动 commit?"
- 选项:
  - `关` (默认) → 写 `_meta/version.json`: `auto_commit=false, auto_push=false`
  - `仅 commit` → `auto_commit=true, auto_push=false`
  - `commit + push` → `auto_commit=true, auto_push=true`

提示用户: 启用 `commit + push` 前请自查 vault 不含 secret (P0 masking 只覆盖 ingest/save, 不护手写笔记)。详见 `docs/sync-git.md`。

vault 不是 git repo → 跳过, 不写两字段。

### 6. 回报

列已创建/已存在/跳过的文件; 提示运行 `/cortex:doctor` 验证。

### 7. 询问 9 cron (P6 内联, 装机一次性, 原 cortex-cron skill 并入)

**必须**调 `AskUserQuestion` (禁文本式提问), 合并 ≤4 questions 单次调用:

**Q1 (multiSelect)**: "勾选要注册的 cron job (9 项)":
- `daily 01:00 知识库 lint`
- `weekly Sun 02:00 fold`
- `daily 02:30 dashboard`
- `daily 02:00 memory-promote` (L4→L3 提炼 + 候选写 candidates.md)
- `daily 03:00 memory-forget` (扫过期标 archive_pending)
- `weekly Sun 04:00 memory-compact` (L4 流水账 gzip)
- `weekly Sun 04:30 digest` (ledger → views 周报)
- `biweekly 1,15 05:00 memory-warden` (腐化检测)
- `monthly 1 06:00 memory-archive` (执行归档)

**Q2 (single)**: "注册平台":
- `不启用` (默认)
- `launchd (macOS)`
- `cron (Linux/macOS)`
- `GitHub Actions (远程仓库)`

Q2 = `不启用` → 跳过, 安装完成。
Q2 ∈ {launchd, cron, gha} → 走内联注册流程 (下文)。

**解析 PLUGIN_ROOT** (cron daemon 不继承 shell env, snippet 必须绝对路径):
优先级: `$CORTEX_INSTALL_PATH` env > `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex` > `$CLAUDE_PLUGIN_ROOT`。**避免**本地开发源码路径 (cron 上下文不可达)。

**每 job 的 wrapper**: `<PLUGIN_ROOT>/scripts/cron/{lint,dashboard,memory-promote,memory-forget,memory-compact,digest,memory-warden,memory-archive}.sh`, 内部走 `claude --bare --no-session-persistence --settings ~/.claude/settings.glm-4.7-flash.json -p "..." --allowed-tools "Bash Read Glob Write Edit"` (memory-* 需写, 不允许删除)。

**Cron 调度表**:

| job | cron 表达式 |
|-----|-------------|
| lint | `0 1 * * *` |
| fold | `0 2 * * 0` |
| dashboard | `30 2 * * 0` |
| memory-promote | `0 2 * * *` |
| memory-forget | `0 3 * * *` |
| digest | `30 4 * * 0` |
**后端 1: launchd (macOS)** — 为每选中 job 写 plist:
- 路径: `~/Library/LaunchAgents/dev.lazygophers.cortex.<job>.plist`
- 内容: `<ProgramArguments>` = `["bash", "<PLUGIN_ROOT>/scripts/cron/<job>.sh"]`, `<StartCalendarInterval>` 按上表
- 落盘前**必须**再调 `AskUserQuestion` 打印完整 plist, 选项 `写入` / `取消` / `改时间`
- 用户选 `写入` → `Write` plist + `Bash launchctl load <plist>`

**后端 2: cron (Linux/macOS)** — append `~/.cortexrc.cron`:
- 行格式: `0 2 * * *  bash <PLUGIN_ROOT>/scripts/cron/memory-promote.sh   # cortex.memory-promote`
- 落盘前 `AskUserQuestion` 打印待 append 行, 选项 `写入` / `取消` / `改时间`
- `Bash echo '...' >> ~/.cortexrc.cron && (crontab -l 2>/dev/null; cat ~/.cortexrc.cron) | crontab -`

**后端 3: GitHub Actions (远程仓库)** — **不自动写**, 仅打印模板:
- 提示用户复制到 `<vault repo>/.github/workflows/cortex-cron.yml`
- 模板包含 9 个 `jobs.<name>`, 各 `on.schedule.cron`, `runs-on: ubuntu-latest`, `steps` 安装 cortex 插件 + 跑 `bash scripts/cron/<job>.sh`
- 提示 vault 须为 GitHub repo, secrets 配 `OBSIDIAN_API_KEY` (若 lint 走 REST)

**关键约束**:
- 写 plist / crontab 前**必须** dry-run + `AskUserQuestion` 二次确认
- cron job 默认 `--allowed-tools "Bash Read Glob Write Edit"` (memory-* 需写; lint 只读保持 `Bash Read Glob`)
- wrapper 提供 `flock -n` + `timeout 600` (复用 `scripts/cron/run.sh`)

**用户态 wrapper (16 个)**:

`install_wrappers.sh` 在 `~/.cortex/scripts/` 生成 16 个用户入口 (按用途分 4 组):

| 组 | wrapper | 用途 |
|----|---------|------|
| 基础 | `doctor.sh` / `config.sh` / `update.sh` / `init.sh` | 健康检查 / 配置 / 升级 / vault 初始化 |
| cron 代理 | `lint.sh` / `dashboard.sh` / `digest.sh` / `install_cron.sh` | cron job 手动触发 |
| 内容 | `ingest.sh` / `search.sh` / `save.sh` / `refactor.sh` | 摄取 / 检索 / 落档 / 重构 |
| 记忆 | `memory.sh` / `recall.sh` / `promote.sh` / `digest.sh` | CRUD / 渐进召回 / 晋级 / 周报巩固 |

每个 wrapper 内部走 `claude --bare --no-session-persistence --max-budget-usd 0.30 -p "..."` 调对应 SKILL, `AUTO_MODE` 前缀关闭交互询问。
- 不写 `~/.claude/settings.json`, 只写 LaunchAgents / crontab 区域
- 检测 `$CI` env → 只打印 GHA yaml, 不真写

**卸载提示**: `launchctl unload <plist> && rm <plist>` (launchd) / 编辑 `~/.cortexrc.cron` 删行 + `crontab ~/.cortexrc.cron` (cron) / 删 `.github/workflows/cortex-cron.yml` (gha)。重跑 `cortex-install` 可再次配置。

## 写入策略

- **不覆盖已有文件** — 用 `Glob` 或 `mcp__obsidian__obsidian_get_file_contents` 检查目标路径, 存在则跳过并标 `(skipped)`
- 优先用 `mcp__obsidian__obsidian_append_content` (vault 索引一致); MCP 不可用回退 `Write`
- 模板文件中的 `{{TITLE}}` / `{{CREATED}}` / `{{UPDATED}}` / `{{PRESET}}` 占位 **不在此 skill 替换** — `_templates/` 下保留原样供 `/cortex:new` 与 `cortex-memory` skill 使用
- 任何单文件失败不中断后续步骤, 最后统一报错

## 输出格式

```
解析 vault: /Users/.../knowledge/obsidian (源: env)
preset: lyt
lang: zh-CN

[共享根]
✅ 写入 _meta/version.json (lang=zh-CN)
✅ 写入 _meta/lint-baseline.json
✅ 写入 _meta/memory-policy.yaml
✅ 写入 _meta/uri-index.json (空骨架)
✅ 写入 _meta/template-manifest.json (复制 plugin manifest 基线)
✅ 复制 _meta/triggers.yaml (session_start 触发关键词基线)
✅ 复制 _meta/frontmatter-schema.yaml (每目录 frontmatter + tag 规范基线)
✅ 创建 _meta/migrations/
✅ 复制 _templates/concept.md ... _index.md (7 既有)
✅ 复制 _templates/html/ (8 片段)
✅ 复制 _templates/memory/ (6 模板)
✅ 复制 _templates/knowledge/ (15 模板)
✅ 写入 index.md / hot.md / log/_index.md / folds/_index.md

[知识库 namespace]
✅ 创建 项目/<host>/<org>/<repo>/ 来源/{网页,论文,书籍}/
✅ 创建 领域/{技术,金融,生活,工作,学习,创作,元学习}/ + 30 三级子类
✅ 创建 日记/{日,周,月,年}/ 反思/{洞察,连接,疑问}/ 收件箱/
✅ 复制 24 个 _index.md

[记忆 namespace]
✅ 创建 L0-核心/ L1-长期/{procedural,semantic-stable}/ L2-中期/semantic/
✅ 创建 L3-短期/episodic/ L4-流水账/{ledger,sessions}/ working/ views/{consolidated}/
✅ 复制 5 个 L<N> _index.md

[仪表盘]
✅ 复制 总览.md / 知识库分布.md / 记忆-L0..L4 / 晋级候选 / 腐化监控 / 桥接 / cron 状态 / 固化流 (12 stub)

[根入口]
✅ 复制 主页.md (HTML 二维仪表盘骨架)
✅ 复制 焦点.md

[git auto-sync]
✅ auto_commit=false, auto_push=false (用户选 `关`)

[cron 注册]
✅ 已注册 launchd: lint / memory-promote / memory-forget (3 项)
⏭️  未选: dashboard / memory-compact / digest / memory-warden / memory-archive

[wrapper]
✅ 已生成 16 个 wrapper 到 ~/.cortex/scripts/ (4 组):
   - 基础: doctor.sh / config.sh / update.sh / init.sh
   - cron 代理: lint.sh / dashboard.sh / digest.sh / install_cron.sh
   - 内容: ingest.sh / search.sh / save.sh / refactor.sh
   - 记忆: memory.sh / recall.sh / promote.sh / digest.sh

总结: 68 项写入, 5 项跳过, 0 项失败
下一步:
  - /cortex:doctor 验证 + 跑 `bash ~/.cortex/scripts/ledger.sh uri_index_rebuild` 初始化索引
  - 记忆 CRUD: ~/.cortex/scripts/memory.sh read|write|update|forget <uri>
  - 渐进召回: ~/.cortex/scripts/recall.sh <query>
  - 晋级检测: ~/.cortex/scripts/promote.sh [--dry-run]
  - 周报巩固: ~/.cortex/scripts/digest.sh [--week N]
```

## 错误处理

- 单文件 IO/权限错: 标 ❌, 继续下一项, 末尾汇总
- vault 路径解析失败: 立即退出并提示配置方式
- 模板/preset 源缺失 (插件文件丢): 立即退出, 提示重装 cortex 插件
- `_meta/memory-policy.yaml` 源缺失: 警告, 跳过该单项, 提示手动从 `<PLUGIN_ROOT>/templates/memory-policy.yaml` 复制
- 任何文件已存在: 跳过, 不覆盖

## 验证

完成 SKILL.md 修订后跑下面命令, 验证 AI 能正确理解安装流程:

```bash
claude --settings ~/.claude/settings.glm-4.7-flash.json \
  -p "$(cat plugins/tools/cortex/skills/cortex-install/SKILL.md)" \
  --output-format stream-json \
  | jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

返回非空且包含 双 namespace / L0-L4 / 9 cron 关键描述 → 通过。

## AUTO_MODE 行为 (wrapper 调用)

当 prompt 含 `[AUTO_MODE]` (来自 `~/.cortex/scripts/init.sh`, 注意 `install.sh` 本体仍保留人工交互, 此段仅针对 init.sh wrapper 路径):

1. **不调** AskUserQuestion (wrapper allowed-tools 已禁此工具, 强行调用必失败)
2. 默认决策: `lang=zh-CN`, git auto-sync=off, cron=off (用户后续手动跑 `~/.cortex/scripts/install_cron.sh` 装计划任务)
3. persistent: 任何 error 自决降级 / 重试 / 换工具组合, 禁询问, 禁中止
4. 写盘前不需二次确认 (AUTO_MODE 隐含已授权)

约束: 本 SKILL 主流程含 `AskUserQuestion` 描述仅适用于 `install.sh` 顶层交互场景; 通过 init.sh wrapper 调用时一律按上述默认值跳过。
