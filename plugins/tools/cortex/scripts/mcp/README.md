# cortex-mcp

MCP server for the cortex Obsidian knowledge base. Exposes structured tools used by the cortex skills (`cortex-search`, `cortex-save`, memory × 6, html_render, etc.) so the model invokes typed APIs instead of orchestrating bash/CLI pipelines.

## 运行方式 (唯一)

`python3 <绝对路径>` — 禁包安装, 禁 pipx, 禁 console-script entry point.

```bash
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/mcp/server.py
```

Plugin manifest (`.claude-plugin/plugin.json`) 的 `mcpServers.cortex.args` 已硬编码:

```json
[
	"~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/scripts/mcp/server.py"
]
```

Claude Code 启动时直接以 `python3 <abs>/server.py` 拉起, 无中间层。

## 依赖

`install.sh` 的 `step_python_deps` 用 `pip3 install --user` 装到系统 python3 (装库不装包):

- `mcp>=1.0.0,<2.0.0`
- `pypdf>=4.0`
- `ebooklib>=0.18`
- `python-docx>=1.1`
- `rich>=13.0,<15.0`

手工补装:

```bash
pip3 install --user mcp pypdf ebooklib python-docx rich
```

## 工具清单 (15)

`cortex_search` / `cortex_deep_search` / `cortex_save` / `cortex_ingest_url` / `cortex_ingest_file` / `cortex_memory_{read,write,recall,forget,consolidate,promote}` / `cortex_html_render` / `cortex_uri_index_rebuild` / `cortex_session_import` / `cortex_ledger_append`.

## Debug

```bash
python3 server.py < /dev/null   # MCP stdio, EOF clean exit
pytest tests/                   # 113 unit tests
```

## 环境变量 (运行时)

- `CORTEX_VAULT_PATH` — 显式 vault override; 否则读 `~/.cortex/config.json:.vault`, fallback 扫 `~/Documents/` / `~/Library/Mobile Documents/` 单一 `.obsidian/` 匹配。
- `CORTEX_PLUGIN_ROOT` — Claude Code 注入, 指向 `~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex`。
- `CORTEX_SC_URL` — Smart Connections REST (默认 `http://127.0.0.1:27123`), 1s timeout 回退 ripgrep。

**禁** 的配置类 env (运行时不读): `OBSIDIAN_VAULT` / `CORTEX_VAULT` / `CORTEX_LANG` — 单一真相 = `~/.cortex/config.json`。
