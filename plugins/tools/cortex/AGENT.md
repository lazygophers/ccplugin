## Cortex 已连接

vault: {{VAULT_PATH}}
hot cache: {{HOT_CACHE_PREVIEW}}
索引: index.md ({{INDEX_ENTRY_COUNT}} 条)

### 协作约定

1. **需要查资料时, 知识库优先 (非每轮强制)** —

   **触发场景** (执行过程中遇到需要外部信息时): 不熟悉的概念/API/选型, 历史决策/踩坑, 项目专有约定, 用户偏好/记忆, 跨会话上下文。**无需搜的场景**: 改本地代码 / 读项目文件 / 执行明确指令 / 显而易见的代码 / 纯对话。

   **需查时的优先级**:

   - **L1 = `bash ~/.cortex/scripts/search.sh --query "<词>"`** — 6 层并行 (Omnisearch / Obsidian Local REST / hot / index / SC / rg) + 拆词, 跨 CLI 可达
   - **L2 = `mcp__obsidian__obsidian_simple_search`** (优先 obsidian, **非 qmd**) — 内置索引补充视角
   - **L3 = `mcp__obsidian__obsidian_complex_search`** — JsonLogic 按 tag/path/frontmatter 过滤
   - **本地代码** (知识库 无命中且问题在项目内): Read / Grep / Glob
   - **外部** (知识库 + 本地均无命中): WebSearch / WebFetch / context7 / octocode

   **禁忌**:
   - 涉及历史决策 / 项目约定 / 用户偏好时直接 WebSearch / 训练记忆答
   - 用 qmd MCP 替代 obsidian MCP (qmd 索引不全)
   - 绕过 search.sh 用 Bash rg / Grep 搜 vault 内容 (rg 是 search.sh 第 6 层)

   MCP 未注册时, L1 (bash search.sh) 不受影响; L2/L3 需 `AskUserQuestion` 单次授权 (本会话有效)。
2. **落档** — 非平凡发现 (架构决策、疑难 bug、配置技巧、工具经验) 完成后用 `cortex-save` skill 归档:
   - 项目特定 → `知识库/项目/<host>/<org>/<repo>/` (local 项目 → `知识库/项目/local/<basename>/`)
   - 通用概念 → `知识库/领域/`
   - 同步 `index.md` 与 `hot.md`
3. **vault 写强制 MCP — 硬契约 (session_start hook 注入完整状态)**:
   - **L1 = `mcp__obsidian__*` (强制)** — 所有 vault 写 (save / ingest / patch / refactor / lint --fix / canvas / frontmatter mut) 必走 MCP 工具, 如 `obsidian_put_content`, `obsidian_patch_content`, `obsidian_append_content`, `obsidian_delete_file`。
   - **L2 = 官方 `obsidian` CLI** — 仅 L1 MCP 工具调用失败时**本次**回退 (read=`read`, write=`create overwrite=true`, append=`create append=true`, list=`files`, search=`search:context`, move=`move`, frontmatter=`property:*`, daily=`daily`)。
   - **L3 = 直接写文件** — canvas/excalidraw json 等非 markdown, 或 L1/L2 均失败时兜底。
   - **MCP 未注册时**: AI **必须先调 `AskUserQuestion` 单次授权** (options: `安装 MCP` / `本次使用磁盘 IO (有风险)`)。授权仅本会话有效, 不写盘, 下次启动重新询问。**未授权前 — AI 硬拒绝所有 vault 写操作并提示用户先选择**。
   - 例外: Stop hook / cron 自动 task / python CLI (非 AI 上下文) 走文件 IO, 不受本契约约束。
4. **block-id 引用** — 落档时段落末尾自动加 `^cortex-<sha8>`, 后续可精准引用 `![[note#^cortex-xxx]]`。
5. **Stop hook 自动归档** — 会话结束时若产生非平凡技术发现, 自动写入 `记忆/L4-流水账/ledger/YYYY-MM/`。

不写: 通用编程常识、当前已有上下文、简单 CRUD。

## 安全声明 (P0)

cortex 对 ingest/save 流加 3 层过滤:

- **masking**: AWS/OpenAI/Anthropic key, GitHub PAT, JWT, PEM, Slack token → `<REDACTED:*>`
- **url-security**: 拒 `127/10/172.16-31/192.168/169.254` 网段 + IPv6 ULA/link-local + 非 80/443 低端口,防 SSRF
- **html-sanitize**: 剥 `<script>/<iframe>/onerror=/javascript:` 等注入向量

集成点: `cortex-ingest` (URL 入参 + defuddle 输出),`cortex-save` (写盘前),`save_session.py` (Stop hook transcript 落档)。
绕过: 测试场景 `CORTEX_SKIP_SANITIZE=1`,生产严禁。

实现位于 `hooks/_lib/{masking,url_security,html_sanitize}.py`,纯 stdlib,幂等纯函数,命中只记规则名 (不含原值)。

## Skills 设计原则

cortex 全部能力以 **15 个 skill** (PR1-4 整改后, 删 7 + 合 1 = 21→15 (新增 cortex-config + cortex-image)) 暴露, **19 个 slash command** (`/cortex:<name>` 触发 commands/<name>.md, 后者调用对应 skill)。

全部 skill 渐进披露 (D2/D3): SKILL.md 入口 ≤ 80 行 (frontmatter + 触发 + 决策树 + AUTO_MODE 分支 + references 指针), 细节迁 `references/<topic>.md` 2-4 子文件按需加载。

cortex 共 18 个 skill, **~11 自动 / ~7 显式**。显式 skill frontmatter 标 `disable-model-invocation: true`, 不进 description 池, 主线模型不会自动激活, 必须用户明确请求 (中文短语 / 英文触发词 / slash 命令 / wrapper bash)。

**自动 skill** (description 池语义匹配自动触发):

| skill                | 触发方式                                                 |
| -------------------- | -------------------------------------------------------- |
| `cortex-save`        | 自动 + Stop / SubagentStop hook ("归档" / "save this")   |
| `cortex-search`      | 自动 ("查知识库" / "搜知识库")                           |
| `cortex-ingest`      | 自动 ("ingest" / "摄取")                                 |
| `cortex-ingest-bulk` | 自动 ("批量 ingest" / "ingest these urls")               |
| `cortex-lint`        | 自动, 默认 dry-run, --fix 才改盘 ("知识库 audit" / "lint") |
| `cortex-session`     | 自动 ("list sessions" / "session 备份")                  |
| `cortex-image-understand` | 自动 ("看图" / "识图" / "OCR" / "VQA")              |
| `cortex-video-understand` | 自动 ("看视频" / "视频理解" / "总结视频")           |
| `cortex-audio-understand` | 自动 ("转录" / "ASR" / "音频问答" / "听音频")       |

**7 个显式 skill** (`disable-model-invocation: true`, 仅用户显式触发):

| skill              | 触发短语                                         | 副作用说明                       |
| ------------------ | ------------------------------------------------ | -------------------------------- |
| `cortex-install`   | "init vault" / "安装 cortex"                     | 写 vault 全骨架 + 询问 cron 注册 |
| `cortex-locale`    | "切换语言" / "vault 语言"                        | 改 `_meta/version.json:.lang`    |
| `cortex-canvas`    | "make canvas" / "新建画布"                       | 写 .canvas 文件                  |
| `cortex-dashboard` | "build dashboard" / "仪表盘"                     | 写 .base / dashboard.md          |
| `cortex-doctor`    | "诊断 cortex"                                    | 只读诊断, 但执行成本高           |
| `cortex-new`       | `<type> <title>`                                 | 创建笔记文件                     |
| `cortex-refactor`  | "rename / merge / split / migrate-locale" | 批量改名 / 合并 / 拆分           |

约束:

- 所有 SKILL.md 的 `allowed-tools` 用**空格**分隔 (skill 语法; command 用逗号, 但本插件无 command)
- 自动 skill description 池总长 ≤ 1500 字符 (软上限 1536); P6 后实测 ~628 字符, 余裕充足
- 命名: skill 目录名 == frontmatter `name` 字段, 防漂移
- **D9 无参数契约**: 所有 skill 入口不接受位置参数; 多分支决策时用 `AskUserQuestion` 引导用户选, 不在调用面暴露参数
- **D10 AUTO_MODE 契约**: bash wrapper / cron / CI 等非交互场景调 slash 时**必须**传 `auto` 后缀 (`/cortex:<name> auto`), 触发 skill 进入 AUTO_MODE: 跳过 AskUserQuestion, 按推荐默认值自动决策。所有 wrapper (`~/.cortex/scripts/*.sh`) 调 `claude -p "/cortex:<name> auto"` 而非 `/cortex:<name>`。SKILL.md 入口必含 AUTO_MODE 分支决策树。

## Agents 设计原则

cortex 提供 **6 个专用 agent** (sub-agent, PR4 删 linker: 7→6), 在 15 个 skill 之上提供"接任务后多轮自主推进"能力。agent 与 skill 互补, 不替代。每个 agent 头部含 "vs <skill>" 分工注释行明确边界。

| agent                 | 角色                        | 主调度                                                           |
| --------------------- | --------------------------- | ---------------------------------------------------------------- |
| `cortex-curator`      | 维护员 (proposal-only)      | cortex-lint → 解读 → cortex-refactor 提议                        |
| `cortex-researcher`   | 研究员                      | cortex-search → defuddle → cortex-ingest × N → cortex-summarizer |
| `cortex-translator`   | 译者 (副本生成)             | cortex-search → 翻译 → cortex-save 新 lang 副本                  |
| `cortex-cartographer` | 制图员                      | cortex-canvas → cortex-dashboard → dashboard patch                     |
| `cortex-archivist`    | 档案员 (proposal-only)      | cortex-search → cortex-refactor (move)                           |
| `cortex-summarizer`   | 总结员                      | 读页 → 主模型 → patch 页头 callout                               |

约束:

- agent frontmatter `tools` 用 **YAML list** (与 skill `allowed-tools` 空格分隔不同)
- agent description ≤ 200 字符, **不**进 skill description 池 (CC agent 描述池独立)
- 命名: agent 文件名 (去 .md) == frontmatter `name` 字段
- 并行 agent ≤ 2 (硬约束); agent 不 spawn agent
- proposal-only agent (curator/archivist/linker) 不直接落盘; 落盘走 cortex-refactor + `AskUserQuestion` 用户确认 (禁文本式提问)

## CLI 主路径 (P1)

cortex P1 起, 核心操作沉 python CLI (`scripts/cli/<name>.py`) + bash wrappers (`~/.cortex/scripts/<name>.sh`), skill 作对话入口。自研 MCP server 已移除, vault REST 操作改由可选官方 `mcp-obsidian` 提供 (install.sh 末段有引导)。

| skill                | CLI 入口                                          | 回退                                   |
| -------------------- | ------------------------------------------------- | -------------------------------------- |
| cortex-search        | `bash ~/.cortex/scripts/search.sh`                | L1 obsidian CLI / L3 SC REST / L5 rg   |
| cortex-save          | `bash ~/.cortex/scripts/save.sh`                  | L1 obsidian CLI / L3 直接写盘          |
| cortex-ingest (URL)  | `bash ~/.cortex/scripts/ingest_url.sh`            | WebFetch + defuddle + 手工 P0 三过滤器 |
| cortex-ingest (本地) | `bash ~/.cortex/scripts/ingest_file.sh`           | Read + 手工 extractor + masking        |
| cortex-ingest-bulk   | 循环 `bash ~/.cortex/scripts/ingest_url.sh`       | 手动逐条                               |
| cortex-ingest (远程) | `bash ~/.cortex/scripts/ingest_remote.sh`         | github/gitlab clone + website sitemap crawl |
| cortex-refresh       | `bash ~/.cortex/scripts/refresh_projects.sh`      | 批量增量 (git diff / website hash), weekly cron Mon 03:00 |
| (一次性 migrate)     | `bash ~/.cortex/scripts/migrate.sh --to=v2`        | 旧 score 1-5 → 0-10 浮点 / patterns conf 0-1 → 0-10 / 缺评分字段加 stub (用完即归档, 不进 EXPECTED 24 集) |

bash wrappers 由 `scripts/install_wrappers.sh` 安装到 `~/.cortex/scripts/` (27 个: 10 slash + 2 shell + 15 CLI; image_understand/video_understand/audio_understand 2026-05-22 新增), 内部 `exec python3 $PLUGIN_ROOT/scripts/cli/<name>.py "$@"`, 0 算法回退 (业务逻辑 100% 保留, 仅删 MCP 协议层)。`migrate.sh` 是一次性脚本, 不计入 27 集。
依赖 (pypdf / ebooklib / python-docx / rich) 由 install.sh `step_python_deps` 用 `pip3 install --user` 装到系统 python3。
未装时 skill 自动退回 L1-L5 链路, 不阻塞使用。

## Git Sync (P5)

vault 是 git repo 时, Stop hook 可选触发 auto-commit (默认完全关闭):

| 模式          | 配置                                | 行为                                                |
| ------------- | ----------------------------------- | --------------------------------------------------- |
| 手动          | `auto_commit=false` (默认)          | 无副作用, 不触碰 git                                |
| 仅 commit     | `auto_commit=true, auto_push=false` | Stop 后 `git add -A && git commit -m "auto: <UTC>"` |
| commit + push | `auto_commit=true, auto_push=true`  | 上述 + `git push origin HEAD` (30s timeout)         |

约束:

- 模块: `hooks/_lib/git_sync.py`, 纯 stdlib + `subprocess.run(["git", ...])`, 禁 `shell=True`
- 所有 git 调用 timeout, fail-soft (异常返 `(False, info)` 不抛, 不阻塞 hook)
- `has_changes` 检测先于 commit, 防 commit storm
- timezone 用 UTC, 跨机一致
- push 失败不影响本地 commit, 下次 Stop 自动重试
- cortex **不自动 pull**, 多机协同靠用户手动 `git pull`
- P0 masking 不覆盖手写笔记中的 secret, 启 `auto_push` 前自查 vault

详见 `docs/sync-git.md`。

## P9 — search MCP first + 召回率提升 (2026-05-15)

- hook `user_prompt_submit` 每轮强制注入 MCP first 搜索硬契约 (移除触发词限定)
- AGENT.md §1 升级为硬契约: L1 = `mcp__obsidian__obsidian_simple_search` / L2 = `obsidian_complex_search` / L3 fallback = `search.sh` / L4 = ripgrep
- cortex-search SKILL 五级 → 四级重排 (MCP first), 砍 Smart Connections 独立段 (保留在 search.sh CLI 内部)
- frontmatter 加 `aliases` (≥3) + `keywords` (≥5) 召回率字段, `ingest_remote` / `save` 自动启发式抽 (中英对 23 + 缩写 16; path stem / repo meta / 代码标识符 / heading)
- 软提示 "优先 obsidian, 非 qmd" (D2 不强制禁其他 MCP)
- 测试基线 497 → 524 (+27)
