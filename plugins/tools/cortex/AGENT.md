## Cortex 已连接

vault: {{VAULT_PATH}}
hot cache: {{HOT_CACHE_PREVIEW}}
索引: wiki/index.md ({{INDEX_ENTRY_COUNT}} 条)

### 协作约定

1. **先搜后问** — 非通用问题先调 `cortex-query` skill 或 `mcp__obsidian__obsidian_simple_search` 搜库, 确认无既有经验再开工。
2. **落档** — 非平凡发现 (架构决策、疑难 bug、配置技巧、工具经验) 完成后用 `cortex-save` skill 归档:
   - 项目特定 → `wiki/30_domains/<host>/<org>/<repo>/`
   - 通用概念 → `wiki/10_concepts/`
   - 同步 `wiki/index.md` 与 `wiki/hot.md`
3. **不直接文件操作** — 经 `mcp__obsidian__*` 工具或 cortex skill, 避免破坏 vault 索引。
4. **block-id 引用** — 落档时段落末尾自动加 `^cortex-<sha8>`, 后续可精准引用 `![[note#^cortex-xxx]]`。
5. **Stop hook 自动归档** — 会话结束时若产生非平凡技术发现, 自动写入 `wiki/log/YYYY-MM/`。

不写: 通用编程常识、当前已有上下文、简单 CRUD。

## Skills 设计原则

cortex 全部能力以 **11 个 skill** 暴露, **0 个 command** (与本仓库 `plugins/tools/task/` 全 skill 模式对齐, 决策见 `.trellis/tasks/05-10-obsidian-kb-plugin/research/05-skills-vs-commands.md` §6.3 建议 B)。

| skill | 触发方式 |
|-------|----------|
| `cortex-install` | 自动 |
| `cortex-search` | 自动 |
| `cortex-save` | 自动 + Stop / SubagentStop hook |
| `cortex-ingest` | 自动 |
| `cortex-lint` | 自动 (默认 dry-run, --fix 才改盘) |
| `cortex-canvas` | 自动 |
| `cortex-dashboard` | 自动 |
| `cortex-fold` | 自动 (默认 dry-run, --apply 才改盘) |
| `cortex-doctor` | **显式** (`disable-model-invocation: true`) — "诊断 cortex" |
| `cortex-new` | **显式** (`disable-model-invocation: true`) — 创建文件有副作用 |
| `cortex-refactor` | **显式** (`disable-model-invocation: true`) — rename/merge/split/fold, 大动干戈 |

约束:
- 所有 SKILL.md 的 `allowed-tools` 用**空格**分隔 (skill 语法; command 用逗号, 但本插件无 command)
- skill description 长度 ≤ 1024 字符, 11 个合计 ≤ 1500 字符 (description 池软上限 1536)
- 命名: skill 目录名 == frontmatter `name` 字段, 防漂移
