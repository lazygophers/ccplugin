# Cortex

> Obsidian 知识库协作插件 — 让 Claude 在每个会话中以结构化、可观测、可演进的方式读写你的 vault。

## 能力速览

| 形态 | 数量 | 内容 |
|------|------|------|
| Hooks | 5 | `SessionStart` / `PostCompact` / `Stop` / `SubagentStop` / `UserPromptSubmit` |
| Skills | 15 | 自动 / 显式触发, 渐进披露 (多文件 SKILL.md+`references/`, 或单文件内分层标题) |
| Agents | 6 | curator / researcher / archivist / cartographer / summarizer / translator |
| Slash commands | 18 | `/cortex:<name>` 全自动 AUTO_MODE persistent |
| Bash wrappers | 25 | `~/.cortex/scripts/*.sh` — slash 走 stream-json + rich UI; CLI 直 exec python3 |
| Lint 规则 | 30 | autofix 循环至 vault clean |
| Python CLI | 13 | save / search / deep_search / digest / ingest_url / ingest_file / ingest_remote / refresh_projects / memory / ledger / session / html_render / image_gen |
| Cron 任务 | 4 | 3 daily (lint / dashboard / digest) + 1 weekly (refresh_projects) |
| Vault 顶层 | 7 | `知识库/` `记忆/` `仪表盘/` `归档/` `_meta/` `_templates/` `_assets/` |

触发方式:

- **Slash command** — `/cortex:lint` / `/cortex:search` / ... 任意会话内直调
- **Bash wrapper** — `bash ~/.cortex/scripts/<name>.sh` (slash 转发, stream-json + rich UI)
- **自然语言** — 命中 skill `description` 触发关键词 (如说"搜知识库 X"触 cortex-search)
- **Agent dispatch** — 复杂多步任务 (cortex-curator 扫 vault / cortex-researcher 多源调研等)

AUTO_MODE persistent (shell 触发约束): 禁询问, 禁中止, AI 自决执行直至 clean 或工具客观失败 (磁盘只读 / 权限 / git lock)。IDE 内交互模式不受此约束。

## 安装

通过 Claude Code marketplace (推荐):

```text
/plugin install cortex
```

curl 一键 (本地无 plugin 树时 bootstrap marketplace + plugin, 已装则升级):

```bash
curl -fsSL https://raw.githubusercontent.com/lazygophers/ccplugin/master/plugins/tools/cortex/install.sh | bash
```

非交互式 (CI / 脚本):

```bash
bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/install.sh \
  --non-interactive --vault "$HOME/persons/knowledge/obsidian" --lang zh-CN --no-cron
```

升级 (拉最新 marketplace + 重装 cortex):

```bash
claude plugins marketplace update ccplugin-market \
  && claude plugins update cortex@ccplugin-market
```

`install.sh` 重复执行: 远端态 (marketplace / plugin) 强制升级; 本地态 (`~/.cortex/config.json` + wrapper) 已存在时交互询问 (默认保留)。`--reinstall` 跳询问强覆盖。

## 配置

vault 路径解析顺序 (env-free, 配置类 env var 已禁用):

1. `~/.cortex/config.json` 的 `.vault` 字段
2. 默认 `~/persons/knowledge/obsidian`
3. auto-detect: 扫 `~/Documents` 与 `~/Library` 找唯一 `.obsidian/` 目录

配置编辑: `bash ~/.cortex/scripts/config.sh`。详见 [安装与配置](docs/安装与配置.md)。

## 5 分钟上手

在 Claude Code 会话中直接对话:

```text
# 1. 初始化 vault (LYT 默认)
"安装 cortex" / "init vault"          → 触发 cortex-install

# 2. 体检
"诊断 cortex" / "vault 健康吗"          → 触发 cortex-doctor

# 3. 搜知识库 (4 级回退 MCP first → search.sh → rg)
"搜知识库 auth middleware"             → 触发 cortex-search

# 4. 落档
"归档" / "save this"                   → 触发 cortex-save

# 5. 摄取 URL / 文件 / 当前目录
"ingest https://..."                  → 触发 cortex-ingest
"深度分析当前目录"                      → 触发 cortex-ingest (dir 模式)

# 6. 维护
"lint vault" / "vault 体检"             → 触发 cortex-lint (autofix 循环)
"刷新仪表盘"                            → 触发 cortex-dashboard
```

---

## 一、Bash 使用说明

### 调用方式

```bash
# Slash 模式 (默认, AUTO_MODE, 走 claude -p "/cortex:<name> auto")
bash ~/.cortex/scripts/<name>.sh

# 交互模式 (掉 -p flag, 进 claude REPL)
bash ~/.cortex/scripts/<name>.sh --interactive

# 跳过末尾 auto git commit vault
bash ~/.cortex/scripts/<name>.sh --no-commit
```

stdout 仅最终 result text; stderr 显示 rich 实时进度; wrapper 退出时自动 `git commit -m "[cortex/<job>] auto <ts>"` (不 push, 非 git repo / 无变更静默跳)。

### 影响范围标记

- 🌐 **全局** — `~/.cortex/` / `~/Library/LaunchAgents` / marketplace cache
- 📁 **当前目录** — PWD (调用 wrapper 时的 cwd)
- 📚 **知识库** — `~/.cortex/config.json:.vault` 指向的 Obsidian vault

### 27 wrapper 全清单

#### 安装 / 配置 (5)

| Wrapper | 范围 | 用途 |
|---------|------|------|
| `init.sh` | 🌐 + 📚 | 初始化 vault 骨架 + 默认模板 + 配置 |
| `install_cron.sh` | 🌐 | 注册 cron / launchd / GHA 定时任务 (本身不调 claude) |
| `config.sh` | 🌐 | 交互式编辑 `~/.cortex/config.json` (直跑 python) |
| `doctor.sh` | 🌐 + 📚 | vault / obsidian-cli / MCP / lint / locale / config 18 项体检 |

#### 维护 / 重构 (3)

| Wrapper | 范围 | 用途 |
|---------|------|------|
| `lint.sh` | 📚 | 跑 30 条 lint 规则 + autofix 循环修复至 clean |
| `refactor.sh` | 📚 | 改名 / 合并 / 拆分 / 去重 / 抽取 / migrate-locale / evolution-apply (默认 dry-run, `--apply` 落盘) |
| `dashboard.sh` | 📚 | 重渲 `index.md` / `hot.md` / canvas + KPI callout |

#### 搜索 / 召回 (3)

| Wrapper | 范围 | 用途 |
|---------|------|------|
| `search.sh` | 📚 | MCP first 四级搜索 (simple → complex → search.sh → rg) + 引用 |
| `deep_search.sh` | 📚 | hybrid 深度搜索 (keyword + vector + 重排) |
| `recall.sh` | 📚 | 记忆渐进披露召回 (L0 → L4) |

#### 数据 / 摄取 (6)

| Wrapper | 范围 | 用途 |
|---------|------|------|
| `save.sh` | 📚 | 落档非平凡发现 (4 评分字段 + block-id + wikilink 回填) |
| `ingest.sh` | 📁 + 📚 | 单源摄取入口 (file / url / 当前目录 / git repo) |
| `ingest_url.sh` | 📚 | URL 摄取 (走 defuddle 净化正文) |
| `ingest_file.sh` | 📚 | 本地文件摄取 |
| `ingest_remote.sh` | 📚 | github / website 远程仓库 / 站点摄取 |
| `refresh_projects.sh` | 📚 | `知识库/项目/` 批量增量刷 (git / website) |

#### 记忆 / 会话 / 渲染 (7)

| Wrapper | 范围 | 用途 |
|---------|------|------|
| `memory.sh` | 📚 | 记忆 CRUD (URI 寻址 L0-L4 + frontmatter 版本控制) |
| `promote.sh` | 📚 | 记忆晋级 (L4→L3 / L3→L2 / L2→L1 / L1→L0 须二次确认) |
| `forget.sh` | 📚 | 遗忘扫描 (按 policy 衰减 + 用户审批) |
| `digest.sh` | 📚 | 8 阶段全量深度 pipeline (读/析/处/维护/整合/优化/验证/清理+evolution), `.cortex/state/*.json` 增量游标 |
| `ledger.sh` | 📚 | ledger jsonl 写入 / 查询 |
| `session.sh` | 📚 | claude code transcript → `记忆/L4-流水账/sessions/` 摘要 |
| `html_render.sh` | 📁 | HTML 片段模板渲染 (badge / card / timeline / mermaid / heatmap) |

### 退出码

- `0` — clean (任务完成)
- 非 0 — stuck (工具客观失败: 磁盘只读 / 权限 / git lock / claude CLI 异常)

详见 [Bash 脚本](docs/Bash%20脚本.md)。

---

## 二、Skills 说明 (15 个)

每个 skill 走 Claude Code 标准 SKILL.md 协议。渐进披露两种形态: **多文件** (入口 SKILL.md ≤80 行 + `references/<topic>.md` 按需加载, 主流) 或 **单文件** (单 SKILL.md 内用 `# / ## / ###` 标题分层, 如 cortex-digest)。

### 触发分类

| 类型 | 说明 |
|------|------|
| **自然语言** | 用户说话命中 description 触发关键词时自动激活 |
| **Slash command** | `/cortex:<name>` 显式调 (与 skill 1:1 对应) |
| **AUTO_MODE** | wrapper 传 `auto` 后缀, 跳 `AskUserQuestion` 自决执行 |
| **Skill 内部** | skill 之间互相调度 (cortex-digest 在 evolution 阶段触 refactor) |

### 19 skill 全清单

| Skill | 触发词 | 用途 | 范围 |
|-------|--------|------|------|
| `cortex-install` | "安装 cortex" / "init vault" / "初始化 vault" | 创建 vault 双 namespace 骨架 + 模板 + cron 注册 | 🌐 + 📚 |
| `cortex-doctor` | "诊断 cortex" / "vault 健康吗" / "体检 vault" | 18 项只读体检 + 修复建议命令 (不改盘) | 🌐 + 📚 |
| `cortex-save` | "save this" / "归档" / "落档" / "save 笔记" | 选目录 + 模板 + 4 评分字段 + block-id + index/hot 同步 | 📚 |
| `cortex-ingest` | "ingest" / "摄取" | 文件 / URL / 目录摄取, 抽实体 + wikilink 回填; URL 走 defuddle | 📁 + 📚 |
| `cortex-search` | "查知识库" / "搜知识库" / "recall" / "想想" / "记得" | MCP first 四级 (simple → complex → search.sh → rg) + 记忆召回 | 📚 + 记忆层 |
| `cortex-memory` | "整理记忆" / "维护记忆" / "记忆体检" / "记忆写入" / "memory write/read" / "forget" / "遗忘" | 记忆生命周期管理 — 默认跑维护扫 (整理/升级候选/补充/forget 标记/评分); 有 verb 走 URI CRUD | 记忆层 |
| `cortex-promote` | "promote memory" / "晋级" / "审批候选" | L4→L3/...→L1→L0 (L1→L0 强制人工二次确认) | 记忆层 |
| `cortex-digest` | "digest" / "巩固记忆" / "consolidate" / daily cron 03:00 | 8 阶段全量深度 pipeline (读/析/处/维护/整合/优化/验证/清理+evolution), `.cortex/state/*.json` 增量游标 | 记忆层 + 📚 |
| `cortex-session` | "import session" / "导入会话" / Stop hook | transcript → `记忆/L4-流水账/sessions/` 摘要 + ledger append | 📚 |
| `cortex-lint` | "wiki audit" / "lint" / "vault 体检" / "lint --fix" | 跑 30 规则 + autofix 循环; 默认 dry-run | 📚 |
| `cortex-refactor` | "重命名" / "rename" / "merge" / "split" / "重构 vault" | rename/merge/split/dedupe/extract/inline/migrate-locale/evolution-apply | 📚 |
| `cortex-dashboard` | "build dashboard" / "刷新仪表盘" / daily cron 02:30 | view_query 查数据源 + 渲 KPI/图表/Top-N, 注 DASH:BEGIN/END | 📚 |
| `cortex-html` | "render html" / "render badge/card/timeline" | 模板 `{{VAR}}` 替换, 输出 HTML 片段 | 📁 |
| `cortex-config` | "查看 cortex 配置" / "改 cortex 配置" / "cortex config" / `/cortex:config` | 展示/编辑 `~/.cortex/config.json` + vault `.cortex/config/*.yaml`; 写前 schema 校验; Stop hook 自动 validate | 🌐 + 📚 |
| `cortex-image` | "生成图" / "做张图" / "text to image" / "AI 画图" / "render image" | 文生图 — 多 provider 配置 (`.cortex/config/image-gen.yaml`) 随机/指定; 10 风格 + 6 排版库; Junior Designer 工作流 + 反 AI slop | 📚 |
| `cortex-image-understand` | "看图" / "识图" / "VQA" / "OCR" / "describe image" / "图里写了什么" | 图理解 — 多 provider VLM (`.cortex/config/image-understand.yaml`); 4 模式 describe/ask/extract/OCR; 支持 zhipu glm-4v / openai gpt-4o / qwen-vl | 📚 |
| `cortex-video-understand` | "看视频" / "视频理解" / "总结视频" / "video QA" | 视频理解 — 多 provider VLM (`.cortex/config/video-understand.yaml`); 双模式 video_url (zhipu glm-4v-plus / qwen-vl-max-video) + frames (ffmpeg 抽帧, 兼容 openai gpt-4o) | 📚 |
| `cortex-audio-understand` | "转录" / "听音频" / "ASR" / "音频问答" | 音频理解 — 多 provider (`.cortex/config/audio-understand.yaml`); asr (Whisper / GLM-ASR) + chat (gpt-4o-audio / qwen-audio); transcribe/describe/ask 三子命令 | 📚 |
| `cortex-dataview` | "dataview" / "DQL" / "数据视图" / "查询块" / "dv.pages" | Obsidian Dataview 块构建/修改/解释; 5 references (dql-syntax/dataviewjs-api/integration-patterns/modify-flow/cookbook); cortex marker 幂等改写; AUTO_MODE 拒 dataviewjs (安全) | 📚 |

### 渐进披露架构

L1 always-on (hook 注入) → L2 routing (SKILL.md 骨架 + 指针) → L3 on-demand (多文件 skill 走 `references/<topic>.md` 按需加载; 单文件 skill 走标题层级跳转)。`skill-references-exists` lint 规则对多文件 skill 强制 reference 链接真实存在。详见 [Skills 详解](docs/Skills%20详解.md)。

---

## 三、Agents 说明 (6 个)

### 调度规则

- **不能由用户直调**: Claude 决策派遣 (`Task` 工具)
- **并发 ≤ 2** (硬约束): 独立任务才并行, 依赖任务串行
- **不嵌套**: agent 不能再 spawn agent, 由主线编排
- **proposal-only 类不写盘**: curator / archivist 产提案, 写盘走 cortex-refactor + 用户确认

调度时机: 并发子任务 / 长上下文隔离 / 多 source 综述 / 跨 lang 副本生成。

### 6 agent 全清单

| Agent | 调度时机 | vs-skill 边界 |
|-------|----------|---------------|
| `cortex-curator` | "audit my vault" / "vault 体检" / 周期巡检孤儿+死链 | vs `cortex-lint` + `cortex-doctor`: curator 巡检提案 (不写盘); lint 执行 + autofix; doctor 即时体检 |
| `cortex-archivist` | "清理收件箱" / "归档老笔记" / digest 路由识别失败的条目二次归属 | vs `cortex-refactor`: archivist 产归档提案; refactor 执行 move/rename/merge |
| `cortex-researcher` | "research X" / "调研 Y" / "从这几个 url 抓资料入库" | vs `cortex-ingest`: researcher 并发多源综述 (search → defuddle → ingest × N → summarizer); ingest 单源落档 |
| `cortex-cartographer` | "刷新 dashboard for X" / "为这个领域生成 canvas" / 批量项目可视化 | vs `cortex-dashboard`: cartographer 跨项目 (多 repo canvas + dashboard 并发); dashboard 单项目 |
| `cortex-summarizer` | "总结这页 / 这个领域" / 被 researcher / cartographer 调度作终产物 | vs `cortex-digest`: summarizer 即时单页摘要 (patch 页头 callout); digest 8 阶段全量深度 + 路由 + 评分 |
| `cortex-translator` | "translate this concept to en" / "把领域目录 ja 化" | 无对应 skill — 跨 lang 副本 (保 wikilink / block-id, 不动原页) |

agent frontmatter 用 YAML list (与 skill `allowed-tools` 空格分隔不同 — CC 平台契约不一致)。详见 [Agents](docs/Agents.md)。

---

## 四、定时任务说明

### 4 个推荐任务

| 时段 | wrapper | 用途 | AUTO_MODE |
|------|---------|------|-----------|
| 01:00 daily | `lint.sh` | 跑 30 规则 + autofix 循环修复至 clean | ✅ |
| 02:30 daily | `dashboard.sh` | 重渲 `index.md` / `hot.md` / canvas | ✅ |
| 03:00 daily | `digest.sh` | 8 阶段全量深度 (读/析/处/维护/整合/优化/验证/清理+evolution), 增量游标 | ✅ |
| 03:00 Mon (weekly) | `refresh_projects.sh` | `知识库/项目/` 批量增量刷 (git/website, flock 防并发) | ✅ |

全部走 wrapper bash 调 `claude -p "/cortex:<name> auto"` 触发, 需先装 Claude Code CLI。

### 安装步骤

cortex 不自动写 crontab / launchd, 仅打印 snippet 由用户复制:

```bash
# Linux / macOS cron (默认)
bash ~/.cortex/scripts/install_cron.sh cron

# macOS launchd plist
bash ~/.cortex/scripts/install_cron.sh launchd

# GitHub Actions workflow
bash ~/.cortex/scripts/install_cron.sh gha
```

`cron` 与 `launchd` 模式还会**自动注册**当前用户 crontab / `~/Library/LaunchAgents/` (内容比对一致 no-op, 不同才覆盖); `gha` 仅打印 workflow yaml。

### Cron snippet 实例

`install_cron.sh cron` 输出:

```cron
0 1 * * * bash "$HOME/.cortex/scripts/lint.sh"
30 2 * * * bash "$HOME/.cortex/scripts/dashboard.sh"
0 3 * * * bash "$HOME/.cortex/scripts/digest.sh"
0 3 * * 1 flock -n /tmp/cortex-refresh.lock bash "$HOME/.cortex/scripts/refresh_projects.sh" >> "$HOME/.cortex/logs/refresh.log" 2>&1
```

### Launchd plist 实例 (单 job)

```xml
<plist version="1.0">
<dict>
  <key>Label</key><string>dev.lazygophers.cortex.daily-lint</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>~/.cortex/scripts/lint.sh</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>1</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>~/.cache/cortex/lint.log</string>
  <key>StandardErrorPath</key><string>~/.cache/cortex/lint.err</string>
</dict>
</plist>
```

`install_cron.sh launchd` 自动 `launchctl unload`/写 plist/`launchctl load` (内容比对 no-op)。

### GitHub Actions workflow 实例

```yaml
name: cortex-cron
on:
  schedule:
    - cron: '0 1 * * *'    # daily lint
    - cron: '30 2 * * *'   # daily dashboard
    - cron: '0 3 * * *'    # daily digest
  workflow_dispatch:

jobs:
  lint:
    if: github.event.schedule == '0 1 * * *'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: cortex lint
        run: bash ${GITHUB_WORKSPACE}/plugins/tools/cortex/scripts/cron/lint.sh
      - uses: actions/upload-artifact@v4
        with: { name: lint-report, path: ~/.cache/cortex/cron/ }
```

dashboard / digest job 同 schedule 分支即可, 完整 yaml 见 `install_cron.sh gha` 输出。

详见 [周期任务](docs/周期任务.md)。

---

## 故障排查

| 症状 | 原因 | 处理 |
|------|------|------|
| SessionStart 无注入 | vault 路径未命中 3 段优先级 | 编辑 `~/.cortex/config.json` 设 `.vault`, 或跑 `doctor.sh` |
| skill 报 "MCP 不可用" | obsidian-local-rest-api 未启或端口冲突 | 检查 `~/.mcp.json` 与 Obsidian 27123/27124 端口 |
| Stop 后没落档 | 启发式判定为非平凡发现, 或 transcript 不可读 | 显式说 "归档" 触发 cortex-save |
| auto-commit 与 OGit 冲突 | 检测到 `.obsidian/plugins/obsidian-git/` | cortex 自动关闭 auto-commit, OGit 接管 |
| lint `--fix` 未改盘 | autofix 仅对部分规则生效 | 其他规则用 cortex-refactor 协助 |
| canvas 文件空 | 官方 obsidian CLI 不支持 .canvas 且 topic 无匹配节点 | 用 cortex-search 先确认 vault 内有相关页 |
| cron 不触发 | macOS SIP 限制 cron / launchd plist 未 load | 改用 launchd, `launchctl list \| grep cortex` 验证 |

详见 [故障排查](docs/故障排查.md)。

---

## 设计哲学

- **不依赖 `lib/`** — 自包含, 纯 bash + python stdlib
- **CLI 主, MCP 兜底** — 官方 `obsidian` CLI 覆盖 read/write/list/search/move/property/daily; CLI 无法表达时 (heading/block 锚点 patch / canvas / 非 md) 回退 `mcp__obsidian__*`; 仍不上才直接写文件 (须 AskUserQuestion 授权)
- **callout 替代 HTML grid** — Obsidian + GitHub 双渲染兼容
- **Hook wrapped JSON schema** — `hookSpecificOutput.{hookEventName, additionalContext}`
- **不写 noop hook** — 教训自 commit `07e713d4`
- **AUTO_MODE persistent** — wrapper / cron 触发禁询问 + 禁中止 + 禁推卸, AI 自决至 clean

---

## 详细文档

完整中文文档见 [`docs/`](docs/索引.md):

- [索引](docs/索引.md) — 文档总目录, 按场景找入口
- [快速上手](docs/快速上手.md) — 5 分钟从安装到第一次落档
- [安装与配置](docs/安装与配置.md) — vault 解析 / `config.json` schema / 升级
- [知识库结构](docs/知识库结构.md) — vault 4 子目录布局
- [Commands](docs/Commands.md) — 19 个 slash command 速查
- [Bash 脚本](docs/Bash%20脚本.md) — 27 wrapper 调用约定 + 退出码
- [Skills 详解](docs/Skills%20详解.md) — 19 skill 用途 / 触发 / 示例 / 失败处理
- [Agents](docs/Agents.md) — 6 agent + 调度边界 + frontmatter 协议
- [Lint 规则](docs/Lint%20规则.md) — 30 规则逐条解释 + `--fix` 行为
- [重构与归档](docs/重构与归档.md) — refactor 子操作 + backup + 不可逆风险
- [模板与美化](docs/模板与美化.md) — 模板 + callout + HTML 边界
- [周期任务](docs/周期任务.md) — cron / launchd / GHA 三种 snippet
- [故障排查](docs/故障排查.md) — 常见症状 → 原因 → 修复
- [i18n](docs/i18n.md) — vault 多语言 / locale 文件 / fallback / 切语言
- [多 CLI](docs/多%20CLI.md) — frontmatter cli/cli_session / 跨 CLI 查询
- [sync-git](docs/sync-git.md) — vault 自动 commit / OGit 协调
- [编程式调用](docs/编程式调用.md) — `claude --bare` + cron 注册 / 故障排查

## License

AGPL-3.0-or-later
