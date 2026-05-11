## Cortex 已连接

vault: {{VAULT_PATH}}
hot cache: {{HOT_CACHE_PREVIEW}}
索引: wiki/index.md ({{INDEX_ENTRY_COUNT}} 条)

### 协作约定

1. **先搜后问** — 非通用问题先调 `cortex-query` skill 或 `obsidian search:context query=<q> vault=<name>` 搜库 (CLI 不可用时回退 `mcp__obsidian__obsidian_simple_search`), 确认无既有经验再开工。
2. **落档** — 非平凡发现 (架构决策、疑难 bug、配置技巧、工具经验) 完成后用 `cortex-save` skill 归档:
   - 项目特定 → `wiki/30_domains/<host>/<org>/<repo>/`
   - 通用概念 → `wiki/10_concepts/`
   - 同步 `wiki/index.md` 与 `wiki/hot.md`
3. **不直接文件操作** — vault 操作回退顺序:
   - **L1 = 官方 `obsidian` CLI** (需 Obsidian app 在跑): read=`read`, write=`create overwrite=true`, append=`create append=true`, list=`files`, search=`search:context`, move=`move` (条件性自动更新 wikilink, 需 vault 设置 "Automatically update internal links" 开启), frontmatter 读=`property:read`, 写=`property:set`, 删=`property:remove`, daily=`daily`; 多 vault 用 `vault=<name>` 指定, 参数语法 `key=value` 无 `--flag`。
   - **L2 = `mcp__obsidian__*`** — 处理 CLI 无法表达的场景 (callout/heading 锚点 patch、block-id patch、canvas/非 md、metadata cache/反向链接图) 或 app 未跑时回退, 如 `obsidian_patch_content target_type=heading`。
   - **L3 = 直接写文件** — canvas/excalidraw json 等非 markdown, 或 L1/L2 均不可用时的兜底, **必须通过 `AskUserQuestion` 取得用户授权后方可落盘**。
4. **block-id 引用** — 落档时段落末尾自动加 `^cortex-<sha8>`, 后续可精准引用 `![[note#^cortex-xxx]]`。
5. **Stop hook 自动归档** — 会话结束时若产生非平凡技术发现, 自动写入 `wiki/log/YYYY-MM/`。

不写: 通用编程常识、当前已有上下文、简单 CRUD。

## 安全声明 (P0)

cortex v2 对 ingest/save 流加 3 层过滤:

- **masking**: AWS/OpenAI/Anthropic key, GitHub PAT, JWT, PEM, Slack token → `<REDACTED:*>`
- **url-security**: 拒 `127/10/172.16-31/192.168/169.254` 网段 + IPv6 ULA/link-local + 非 80/443 低端口,防 SSRF
- **html-sanitize**: 剥 `<script>/<iframe>/onerror=/javascript:` 等注入向量

集成点: `cortex-ingest` (URL 入参 + defuddle 输出),`cortex-save` (写盘前),`save_session.py` (Stop hook transcript 落档)。
绕过: 测试场景 `CORTEX_SKIP_SANITIZE=1`,生产严禁。

实现位于 `hooks/_lib/{masking,url_security,html_sanitize}.py`,纯 stdlib,幂等纯函数,命中只记规则名 (不含原值)。

## Skills 设计原则

cortex v2 全部能力以 **14 个 skill** 暴露, **0 个 command** (与本仓库 `plugins/tools/task/` 全 skill 模式对齐, 决策见 `.trellis/tasks/archive/2026-05/05-10-obsidian-kb-plugin/research/05-skills-vs-commands.md` §6.3 建议 B)。

cortex v2 共 14 个 skill, **5 自动 / 9 显式**。显式 skill frontmatter 标 `disable-model-invocation: true`, 不进 description 池, 主线模型不会自动激活, 必须用户明确请求 (中文短语 / 英文触发词 / 用户直接调用)。

**5 个自动 skill** (description 池总长 722 字符, 远低于 1536 软上限):

| skill | 触发方式 |
|-------|----------|
| `cortex-save` | 自动 + Stop / SubagentStop hook ("归档" / "save this") |
| `cortex-search` | 自动 ("查知识库" / "搜知识库") |
| `cortex-ingest` | 自动 ("ingest" / "摄取") |
| `cortex-lint` | 自动, 默认 dry-run, --fix 才改盘 ("wiki audit" / "lint") |
| `cortex-session` | 自动 ("list sessions" / "session 备份") |

**9 个显式 skill** (`disable-model-invocation: true`, 仅用户显式触发):

| skill | 触发短语 | 副作用说明 |
|-------|---------|-----------|
| `cortex-install` | "init vault" / "安装 cortex" | 写 vault 全骨架 + 询问 cron 注册 |
| `cortex-locale` | "切换语言" / "vault 语言" | 改 `_meta/version.json:.lang` |
| `cortex-fold` | "fold logs" / "归档日志" | 大批量 mv log/ → folds/ |
| `cortex-canvas` | "make canvas" / "新建画布" | 写 .canvas 文件 |
| `cortex-dashboard` | "build dashboard" / "仪表盘" | 写 .base / dashboard.md |
| `cortex-doctor` | "诊断 cortex" | 只读诊断, 但执行成本高 |
| `cortex-new` | `<type> <title>` | 创建笔记文件 |
| `cortex-refactor` | "rename / merge / split / fold / migrate-locale" | 批量改名 / 合并 / 拆分 |
| `cortex-cron` | "register cron" / "/cortex:cron" | 写系统级 launchd / cron / GHA |

约束:
- 所有 SKILL.md 的 `allowed-tools` 用**空格**分隔 (skill 语法; command 用逗号, 但本插件无 command)
- 自动 skill description 池总长 ≤ 1500 字符 (软上限 1536); 现状 722 字符, 余裕充足
- 命名: skill 目录名 == frontmatter `name` 字段, 防漂移

## Agents 设计原则

cortex v2 提供 **8 个专用 agent** (sub-agent), 在 14 个 skill 之上提供"接任务后多轮自主推进"能力。agent 与 skill 互补, 不替代。

| agent | 角色 | 主调度 |
|-------|------|--------|
| `cortex-curator` | 维护员 (proposal-only) | cortex-lint → 解读 → cortex-refactor 提议 |
| `cortex-researcher` | 研究员 | cortex-search → defuddle → cortex-ingest × N → cortex-summarizer |
| `cortex-translator` | 译者 (副本生成) | cortex-search → 翻译 → cortex-save 新 lang 副本 |
| `cortex-historian` | 史官 | cortex-session → cortex-summarizer → cortex-fold |
| `cortex-cartographer` | 制图员 | cortex-canvas → cortex-dashboard → MOC patch |
| `cortex-archivist` | 档案员 (proposal-only) | cortex-search → cortex-refactor (move) |
| `cortex-linker` | 连接员 | SC API → cortex-search → cortex-save (patch wikilinks) |
| `cortex-summarizer` | 总结员 | 读页 → 主模型 → patch 页头 callout |

约束:
- agent frontmatter `tools` 用 **YAML list** (与 skill `allowed-tools` 空格分隔不同)
- agent description ≤ 200 字符, **不**进 skill description 池 (CC agent 描述池独立)
- 命名: agent 文件名 (去 .md) == frontmatter `name` 字段
- 并行 agent ≤ 2 (硬约束); agent 不 spawn agent
- proposal-only agent (curator/archivist/linker) 不直接落盘; 落盘走 cortex-refactor + `AskUserQuestion` 用户确认 (禁文本式提问)
