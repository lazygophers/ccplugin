---
name: cortex-doctor
description: 诊断 cortex 健康 — vault/obsidian-cli/app-running/MCP/SC/rg/lint/locales/lang-fallback/sessions/config/wrappers 共 18 项。仅显式触发。
disable-model-invocation: true
allowed-tools: Bash Read Glob mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents
---

# cortex-doctor

对当前环境做完整体检并产出报告。

## 检查项

1. **vault 路径解析** — 跑 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/hooks/_lib/resolve_vault.sh`, 显示命中的来源 (env / config / default / auto-detect / 未命中)
2. **vault 结构** — 共享根目录 (`_meta/`, `_templates/`, `index.md`, `hot.md`, `log/`, `folds/`) 是否齐全
3. **preset 类型** — 读 `<vault>/_meta/version.json` 显示 preset (lyt/zettel/para/blank)
4. **官方 obsidian CLI** — `command -v obsidian` 是否存在, `obsidian --version` 输出 (期望 v1.12.x+); 同时 `obsidian vault list` 检查 vault 是否已注册到 `obsidian.json`。**cortex v2 主路径**: read=`obsidian read` / write=`obsidian create overwrite=true` / append=`obsidian create append=true` / list=`obsidian files` / search=`obsidian search:context` / move=`obsidian move` / frontmatter=`obsidian property` / daily=`obsidian daily`。未安装提示: 参考官方 docs <https://docs.obsidian.md/Plugins/Obsidian+CLI> (Obsidian Settings → General → Command line interface 启用并安装)
5. **Obsidian app 在跑** — 官方 CLI 经 app runtime, app 不在跑全部失败。探活: mac `pgrep -x Obsidian` / linux `pgrep obsidian` / win `tasklist /FI "IMAGENAME eq Obsidian.exe"`。未跑 → 提示用户启动 Obsidian app
6. **vault 自动更新 wikilink** — 读 `<vault>/.obsidian/app.json` 的 `alwaysUpdateLinks` 字段。`true` → ✅ `obsidian move` 会自动更新 wikilink; `false`/缺失 → ⚠ 提示开启 (Settings → Files & Links → Automatically update internal links), 否则 cortex-refactor 的 move 不会自动改链, 需走 MCP/手补
7. **Obsidian MCP server (L2 兜底)** — 检测 `mcp__obsidian__obsidian_list_files_in_vault` 工具是否可用。用于 heading-anchor patch / block-id patch / canvas / 非 md 文件 / 完整 metadata graph 等官方 CLI 不支持的场景
8. **Local REST API** — `curl -sf http://127.0.0.1:27123/` 检测端口
9. **Smart Connections** — 查 `~/Library/Application Support/obsidian/<vault>/.obsidian/plugins/smart-connections/data.json`
10. **Obsidian Git** — 同上, 提示是否需关闭 cortex auto-commit
11. **lint 基线** — `_meta/lint-baseline.json` 存在性
12. **模板完整性** — `_templates/{concept,entity,domain,dashboard,question,source}.md` 是否齐全
13. **Smart Connections REST API** — `curl -sf -m 2 http://127.0.0.1:27124/embeddings/info` 是否可达 (cortex-search L3 语义检索依赖)
14. **ripgrep** — `command -v rg` (cortex-search L5 兜底依赖)
15. **backlink 完整性** — 抽样 5 个 `log/` 与 `10_concepts/` 页面, 检查其 `[[X]]` wikilink 是否在 X 的 `## Backlinks` 段中出现; 不一致计入报告
16. **共享 config 存在性** — `~/.cortex/config.json` 是否存在。缺失 → ℹ️ info (非 fail), 提示运行 `~/.cortex/scripts/config.sh init` 或 `python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/cortex_config.py init`
17. **共享 config 合法性** — 跑 `python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/cortex_config.py validate`; exit 0 + "config ok" → ✅; "config absent" → ℹ️; exit 1 → ❌ 列出字段错误
18. **wrapper 完整性** — 检 `~/.cortex/scripts/` 下 7 个 wrapper (`lint.sh`, `fold.sh`, `dashboard.sh`, `doctor.sh`, `install_cron.sh`, `config.sh`, `update.sh`) 是否存在且可执行。缺失 → ⚠️ warn (PR5 才生成), 提示运行 `bash ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/install.sh`

## 行为

按顺序跑上面 18 项, 每项输出一行带 emoji 状态:

```
✅ vault 路径: /Users/.../knowledge/obsidian (源: env)
✅ 共享根: 完整
⚠️ preset: 未知 (建议跑 cortex-install lyt)
✅ obsidian CLI: v1.12.4 (vault `brain` 已注册)
✅ Obsidian app: 在跑 (pid 12345)
✅ alwaysUpdateLinks: true (move 自动改链)
✅ Obsidian MCP (L2 兜底): 可用
...
```

末尾给一句总结 + 建议下一步。

## 实现提示 (给 Claude)

1. 用 `Bash` 跑 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/hooks/_lib/resolve_vault.sh` 拿 vault 路径
2. 用 `Read`/`Glob` 检查共享根目录与模板
3. obsidian CLI / app-running / MCP / REST 检查用一组 `Bash` 命令; CLI 在但 app 未跑 → ❌ CLI 全部失败, 提示启动 app; CLI 缺失但 MCP 在 → 给降级建议 ("官方 obsidian CLI 不可用, cortex 将走 MCP REST 路径; 需要 Local REST API 插件 + Obsidian 进程常驻; 单调用延迟 ~10ms→~50ms 量级"); 两者都缺 → ❌ 致命
4. 全部容错: 任一项失败仅标 ❌, 不中断后续检查

## 不做

- 不写 vault (诊断专用)
- 不自动修复, 仅给出建议命令 (用户决定是否执行)
- 不被 LLM 自动触发 (`disable-model-invocation: true`), 必须用户显式说"诊断 cortex / cortex doctor"

## AUTO_MODE 行为 (wrapper 调用)

当 prompt 含 `[AUTO_MODE]` (来自 `~/.cortex/scripts/doctor.sh`):

1. **不调** AskUserQuestion (wrapper allowed-tools 已禁此工具, 强行调用必失败)
2. 任何需用户决策处 → 走默认值跳过 (诊断仅读, 不动盘)
3. fail-fast: 任何 error 立即返回错误码 + 简短消息, 不询问回退方案
4. 输出诊断报告 + 建议命令 (用户后续手动执行)
