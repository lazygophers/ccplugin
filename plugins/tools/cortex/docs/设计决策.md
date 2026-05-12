# 设计决策

本文回答：cortex 的关键架构决策为什么这么选 (ADR D1-D7), 以及 research-driven 的 §10 修订点。
适用读者：想了解"为什么不是别的做法"的开发者、想给 cortex 做出反向决策的贡献者。

完整 ADR 原文见 `.trellis/tasks/archive/2026-05/05-10-obsidian-kb-plugin/prd.md`。本文做中文化解读。

## D1: 不依赖 lib/, 自包含

**决策**：cortex 不引入 ccplugin 主仓 `lib/` 中的任何模块, 全部用 Python stdlib + bash。

**理由**：

- ccplugin 插件可能被独立 clone / 软链使用, 缺 lib 时仍需可运行。
- lib 升级影响面广, 解耦后 cortex 可独立演进。
- 减少 hook 启动延迟 (无 import 链)。

**代价**：

- 一些通用工具 (logging / config 解析) 在 cortex 内重复实现。
- 与其他 ccplugin 插件 (如 task / statusline) 无代码共享。

**反向决策可能**：未来若插件爆炸式增长, 重复成本超过解耦收益, 可考虑分一个 `cortex-lib/` 子包。

## D2: CLI 主, MCP 兜底 

**决策**：vault 操作优先走官方 obsidian CLI v1.12.4 (binary `obsidian`, 2026-02-27 GA), `mcp__obsidian__*` 仅在 CLI 不支持时使用 (heading/block 锚点 patch、canvas、metadata cache、反向链接图); CLI 与 MCP 均不可用时落 L3 直接写盘, 须 AskUserQuestion 授权。

**理由**：

- 官方维护 = 长期可靠, 与 Obsidian 版本同步, 第三方 notesmd-cli 的"官方未出"理由已消失。
- 命令面 `read` / `create overwrite=true` / `create append=true` / `files` / `search:context` / `move` / `property:read|set|remove` / `daily` 覆盖 cortex 主链操作。
- 参数语法统一 `key=value` 无 `--flag`; 多 vault 用 `vault=<name>` 显式指定。
- `move` 在 vault 设置 "Automatically update internal links" 开启时**自动更新 wikilink**; cortex-doctor 校验此设置。

**代价**：

- 需 Obsidian app 在跑 (无头模式不可用); SessionStart hook 通过 `pgrep -x Obsidian` 检测, 未跑直接回退 L2=mcp__obsidian__*。
- 用户需安装: `brew install --cask obsidian-cli` 或参照 Obsidian 官方 docs (Settings → General → Command line interface)。
- 部分场景 (heading/block 锚点 patch、callout 注入、canvas / 非 md) CLI 无法表达, 必须 L2 (mcp__obsidian__*); cortex-summarizer callout 顶部注入必走 MCP。

**L1/L2/L3 阶梯**：L1 = 官方 obsidian CLI (app 在跑); L2 = mcp__obsidian__* (Local REST API 插件 + app 常驻); L3 = 直接写盘 (Read/Write/Edit, 须 AskUserQuestion 授权, per-file 默认, ≥3 文件 per-batch)。

## D3: callout 替代 HTML grid

**决策**：模板与 cortex-save 输出优先用 Obsidian callout, 仅 dashboard 多列 KPI 卡片回退 HTML grid。

**理由**：

- callout 在 Obsidian + GitHub 双端都能渲染。
- HTML 在 GitHub Markdown 中 style 属性会被剥离。
- callout 语法浅, 用户改起来容易。

**代价**：

- 复杂版面 (网格、并排卡片) callout 表达不出。

**判定边界**：≥3 列 + 需视觉对齐 → HTML; 否则 callout。

## D4: Hook wrapped JSON schema

**决策**：所有 hook 输出走 v2 schema:

```json
{"hookSpecificOutput": {"hookEventName": "X", "additionalContext": "..."}}
```

**理由**：

- CC 优先消费 v2。
- wrapped 结构方便扩展未来字段 (e.g. metadata)。

**代价**：

- 每个 hook 都得拼 JSON, bash 引号容易出错。cortex 用 `python3 -c` 内嵌生成。

## D5: 不写 noop hook

**决策**：拒绝注册"什么都不做"或"只 log 不 emit"的 hook。

**理由**：

- 教训自 commit `07e713d4` (移除全部语言插件的空 hooks)。
- 空 hook 浪费 CC 启动 100-500ms。
- 用户看 `/hooks` 列表时困惑"为什么有这个"。

**实施**：cortex 4 个 hook (SessionStart / Stop / SubagentStop / PostCompact) 都有实际行为, 没注册 PreToolUse / PostToolUse / Notification 等当前无需求的 hook。

## D6: 显式 vs 自动 skill 二元划分

**决策**：副作用大的 skill (cortex-doctor / cortex-new / cortex-refactor) 标 `disable-model-invocation: true`, 必须用户显式请求。

**理由**：

- doctor 只读但耗时 (13 项体检)。
- new 创建文件, 误触会污染 vault。
- refactor 改盘 + 反链, 不可逆风险高。

**代价**：

- 用户需记得这 3 个 skill 不能"暗示触发", 必须明确说"诊断"/"new"/"refactor"。

决策依据：`.trellis/tasks/archive/2026-05/05-10-obsidian-kb-plugin/research/05-skills-vs-commands.md` §6.3 建议 B。

## D7: 默认 dry-run

**决策**：`cortex-lint` / `cortex-refactor` / `cortex-fold` 默认 dry-run, `--fix` / `--apply` 才改盘。

**理由**：

- 用户先看预览 (diff / report), 然后通过 `AskUserQuestion` 内置工具确认改盘 (禁文本式提问)。
- 减少误操作回滚成本。

**代价**：

- 用户需多输一次命令。但显式确认换不可逆操作的安全, 值得。

## §10 Research-driven 修订点

prd 在 §10 列了 research 后浮现的修订:

### §10.1 SessionStart additionalContext 软上限

研究发现 CC 对 `additionalContext` 软限制 ~10KB, 超过会截断或忽略。

**修订**：cortex `session_start.sh` 内 `MAX_BYTES = 5000` (hot.md 单项), AGENT.md + hot.md 合计 ≤10KB。

### §10.2 全 skill 模式

最初 prd 设计了 commands + skills 双模式, research/05 分析后发现全 skill 更优 (与 task 插件对齐, 触发更自然)。

**修订**：去掉所有 commands, 11 个能力全部以 skill 暴露。

### §10.3 五级搜索回退

最初设计三级 (MCP → ripgrep), research 发现可加 hot.md / index.md / Smart Connections REST 提速。

**修订**：cortex-search 五级回退 (hot → index → SC → MCP → rg)。

### §10.4 启发式落档判定

最初 Stop hook 总是落档, 研究发现绝大多数会话内容平凡 (CRUD / 通用问答), 全落档造成 wiki 噪音。

**修订**：加 `min_lines` / `min_chars` / `skip_if_only_questions` 启发式, 默认阈值 30 行 / 800 字符。

### §10.5 OGit 协调

最初 cortex 自己 auto-commit, 研究发现很多 vault 已用 Obsidian Git 插件, 双 commit 冲突。

**修订**：检测到 `.obsidian/plugins/obsidian-git/` 自动关闭 cortex auto-commit。

### §10.6 callout 13 类白名单

研究发现 Obsidian 标准 callout 13 类 + 各自别名 (e.g. `summary` ≡ `tldr`), 自定义类型双端兼容差。

**修订**：lint rule `callout-unknown-type` 强制白名单。

### §10.7 block-id 全局唯一

研究发现 Obsidian 跳转 `[[note#^id]]` 的 `id` 须文件内唯一, 但 cortex 跨文件用同样 hash 算法可能撞。

**修订**：lint rule `block-id-duplicate` autofix 重算冲突 sha8。

## 反向决策候选

未来可能反转的决策：

| 当前 | 反转候选 | 触发条件 |
|------|----------|----------|
| 不依赖 lib | 抽 cortex-lib 子包 | 重复成本高于解耦收益 |
| 全 skill | 加少量 command | 用户反馈"自然语言触发不可控" |
| MCP 主 | 完全自管 REST | obsidian-mcp-server 维护中断 |
| 默认 dry-run | 信任的操作直接 apply | 用户疲劳, 频繁加 --apply |

## 相关文档

- `架构设计.md` — 模块依赖与数据流
- `Hooks 机制.md` — D4 + D5 的实施细节
- `Skills 详解.md` — D6 的 11 skill 名单
- `Lint 规则.md` — §10.6 / §10.7 修订
- 决策依据：`.trellis/tasks/archive/2026-05/05-10-obsidian-kb-plugin/prd.md` §10
- 全 skill 决策：`.trellis/tasks/archive/2026-05/05-10-obsidian-kb-plugin/research/05-skills-vs-commands.md`
