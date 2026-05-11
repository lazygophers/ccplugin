---
name: cortex-doctor
description: 诊断 cortex 健康 — vault/notesmd-cli/MCP/SC/rg/lint/locales/lang-fallback/sessions 共 16 项。仅显式触发。
disable-model-invocation: true
allowed-tools: Bash Read Glob mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents
---

# cortex-doctor

对当前环境做完整体检并产出报告。

## 检查项

1. **vault 路径解析** — 跑 `${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh`, 显示命中的来源 (env / config / default / auto-detect / 未命中)
2. **vault 结构** — 共享根目录 (`_meta/`, `_templates/`, `index.md`, `hot.md`, `log/`, `folds/`) 是否齐全
3. **preset 类型** — 读 `<vault>/_meta/version.json` 显示 preset (lyt/zettel/para/blank)
4. **notesmd-cli (Yakitrak)** — `command -v notesmd-cli` 是否存在, `notesmd-cli --version` 输出; 同时 `notesmd-cli list-vaults --json` 检查 vault 是否已注册到 `~/.config/obsidian/obsidian.json`。**cortex v2 主路径**: read=`print` / write=`create --overwrite` / append=`create --append` / list=`list` / search=`search-content --format json` / move=`move` / frontmatter=`frontmatter` / daily=`daily`。未安装提示: `brew tap yakitrak/yakitrak && brew install yakitrak/yakitrak/notesmd-cli` (或 scoop `scoop bucket add scoop-yakitrak https://github.com/yakitrak/scoop-yakitrak.git && scoop install notesmd-cli` / `yay -S notesmd-cli-bin` / 源码 `git clone https://github.com/Yakitrak/obsidian-cli && cd obsidian-cli && go build -o notesmd-cli .`)
5. **Obsidian MCP server (fallback)** — 检测 `mcp__obsidian__obsidian_list_files_in_vault` 工具是否可用。仅用于 heading/block 锚点 patch、canvas、metadata cache 等 CLI 不支持的场景; CLI 可用时不是必须
6. **Local REST API** — `curl -sf http://127.0.0.1:27123/` 检测端口
7. **Smart Connections** — 查 `~/Library/Application Support/obsidian/<vault>/.obsidian/plugins/smart-connections/data.json`
8. **Obsidian Git** — 同上, 提示是否需关闭 cortex auto-commit
9. **lint 基线** — `_meta/lint-baseline.json` 存在性
10. **模板完整性** — `_templates/{concept,entity,domain,dashboard,question,source}.md` 是否齐全
11. **Smart Connections REST API** — `curl -sf -m 2 http://127.0.0.1:27124/embeddings/info` 是否可达 (cortex-search L3 语义检索依赖)
12. **ripgrep** — `command -v rg` (cortex-search L5 兜底依赖)
13. **backlink 完整性** — 抽样 5 个 `log/` 与 `10_concepts/` 页面, 检查其 `[[X]]` wikilink 是否在 X 的 `## Backlinks` 段中出现; 不一致计入报告

## 行为

按顺序跑上面 13 项, 每项输出一行带 emoji 状态:

```
✅ vault 路径: /Users/.../knowledge/obsidian (源: env)
✅ 共享根: 完整
⚠️ preset: 未知 (建议跑 cortex-install lyt)
✅ notesmd-cli: v1.x (vault `brain` 已注册)
✅ Obsidian MCP (fallback): 可用
...
```

末尾给一句总结 + 建议下一步。

## 实现提示 (给 Claude)

1. 用 `Bash` 跑 `${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh` 拿 vault 路径
2. 用 `Read`/`Glob` 检查共享根目录与模板
3. notesmd-cli / MCP / REST 检查用一组 `Bash` 命令; CLI 缺失但 MCP 在 → 给降级建议 ("notesmd-cli 不可用, cortex 将走 MCP REST 路径; 需要 Local REST API 插件 + Obsidian 进程常驻; 单调用延迟 ~10ms→~50ms 量级"); 两者都缺 → ❌ 致命
4. 全部容错: 任一项失败仅标 ❌, 不中断后续检查

## 不做

- 不写 vault (诊断专用)
- 不自动修复, 仅给出建议命令 (用户决定是否执行)
- 不被 LLM 自动触发 (`disable-model-invocation: true`), 必须用户显式说"诊断 cortex / cortex doctor"
