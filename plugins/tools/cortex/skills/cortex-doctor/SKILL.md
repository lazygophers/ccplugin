---
name: cortex-doctor
description: 诊断 cortex 健康 — vault/MCP/CLI/REST/SC/rg/lint/backlink 共 13 项。仅显式触发 (disable-model-invocation: true)。
disable-model-invocation: true
allowed-tools: Bash Read Glob mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents
---

# cortex-doctor

对当前环境做完整体检并产出报告。

## 检查项

1. **vault 路径解析** — 跑 `${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh`, 显示命中的来源 (env / config / default / auto-detect / 未命中)
2. **vault 结构** — 共享根目录 (`_meta/`, `_templates/`, `index.md`, `hot.md`, `log/`, `folds/`) 是否齐全
3. **preset 类型** — 读 `<vault>/_meta/version.json` 显示 preset (lyt/zettel/para/blank)
4. **Obsidian MCP server** — 检测 `mcp__obsidian__obsidian_list_files_in_vault` 工具是否可用 (在主对话由 Claude 直接调用即可)
5. **Obsidian CLI** — `command -v obsidian` 是否存在, `obsidian --version` 输出
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
✅ Obsidian MCP: 可用
❌ Obsidian CLI: 未安装 (brew install obsidian-cli)
...
```

末尾给一句总结 + 建议下一步。

## 实现提示 (给 Claude)

1. 用 `Bash` 跑 `${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh` 拿 vault 路径
2. 用 `Read`/`Glob` 检查共享根目录与模板
3. MCP/CLI/REST 检查用一组 `Bash` 命令
4. 全部容错: 任一项失败仅标 ❌, 不中断后续检查

## 不做

- 不写 vault (诊断专用)
- 不自动修复, 仅给出建议命令 (用户决定是否执行)
- 不被 LLM 自动触发 (`disable-model-invocation: true`), 必须用户显式说"诊断 cortex / cortex doctor"
