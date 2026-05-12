# cortex-mcp

MCP server for the cortex Obsidian knowledge base. Exposes structured tools used
by the cortex skills (`cortex-search`, `cortex-save`) so the model invokes typed
APIs instead of orchestrating bash/CLI pipelines.

## Tools

- `cortex_search` — multi-layer fallback search (hot.md → index.md → Smart
  Connections REST → ripgrep). Returns structured hit list with path/title/
  snippet/score/source.
- `cortex_save` — write a typed note (concept / domain / log) into the vault.
  Runs masking, adds frontmatter, injects `^cortex-<sha8>` block-ids, takes an
  advisory `fcntl` flock, then patches `hot.md` / `index.md`.

## Install

`pipx` recommended:

```bash
pipx install ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/mcp
which cortex-mcp   # should resolve to ~/.local/bin/cortex-mcp
```

`install.sh` runs `step_mcp_install` automatically. Use `--reinstall` to force
a clean install after the plugin tree updates (`pipx install --force`).

If `pipx` is not available, you can run the server directly:

```bash
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/mcp/server.py
```

The plugin manifest declares both the `cortex-mcp` console entry point and a
`python3 server.py` fallback so the loader works without pipx.

## Debug

The server speaks MCP stdio. Quick smoke test:

```bash
python3 server.py < /dev/null   # should start and exit cleanly on EOF
```

Run the unit suite:

```bash
pytest tests/
```

## Environment

- `CORTEX_VAULT_PATH` — explicit vault override; otherwise the server falls back
  to `~/.config/cortex/config.json` (`vault` key) and finally to a single
  `.obsidian/` match under `~/Documents/` or `~/Library/Mobile Documents/`,
  mirroring `hooks/_lib/resolve_vault.sh`.
- `CORTEX_SC_URL` — Smart Connections REST endpoint (default
  `http://127.0.0.1:27123`). The server probes it with a 1s timeout and falls
  through to ripgrep if unreachable.
