# cortex 移除自研 MCP 改用官方 mcp-obsidian

## 目标

- `.claude-plugin/plugin.json` 中 `mcpServers.cortex` 整块移除
- 自研 MCP 代码 (`scripts/mcp/cortex_mcp.py` + `scripts/mcp/tools/*` + `scripts/mcp/server.py` + `scripts/mcp/tests/*`) 全部删除
- 所有 agent/skill/command/hook 中对 `mcp__cortex__*` 的引用改为官方 `mcp__obsidian__*` 工具或 bash 等价
- `install.sh` 添加 mcp-obsidian 安装指引 (uvx mcp-obsidian + obsidian REST API plugin)

## 工具替换映射

| 自研 cortex MCP | 替代方案 |
|----------------|---------|
| `cortex_search(query, scope, limit)` | `mcp__obsidian__obsidian_simple_search(query)` 直接替换 |
| `cortex_deep_search(query, mode, ...)` | 降级为 `obsidian_simple_search` + `obsidian_complex_search` (JsonLogic);agent 文本中说明降级 |
| `cortex_save(kind, title, body, ...)` | bash 脚本 `~/.cortex/scripts/save.sh` (新增,封装 masking + frontmatter + flock + hot/index patch);agent/skill 改 Bash 调用 |
| `cortex_ingest_url(url, kind, ...)` | bash 脚本 `~/.cortex/scripts/ingest_url.sh` (新增,封装 fetch + extract + masking + save) |
| `cortex_ingest_file(path, kind, ...)` | bash 脚本 `~/.cortex/scripts/ingest_file.sh` (新增,封装 extract + masking + save) |
| `cortex_memory_read(uri, full)` | bash `~/.cortex/scripts/memory_read.sh` (URI 解析 → 文件读取) |
| `cortex_memory_write(uri, content, level, ...)` | bash `~/.cortex/scripts/memory_write.sh` (策略校验 + 落档) |
| `cortex_memory_recall(query, levels, top_k)` | bash `~/.cortex/scripts/memory_recall.sh` (grep + score) |
| `cortex_memory_forget(uri, criteria)` | bash `~/.cortex/scripts/memory_forget.sh` (标 archive_pending) |
| `cortex_memory_consolidate()` | 已废 (digest 取代),仅删引用 |
| `cortex_memory_promote(uri, target_level, ...)` | bash `~/.cortex/scripts/memory_promote.sh` |
| `cortex_ledger_append(event, date)` | bash `~/.cortex/scripts/ledger_append.sh` |
| `cortex_session_import(transcript_path, cli)` | bash `~/.cortex/scripts/session_import.sh` |
| `cortex_uri_index_rebuild()` | bash `~/.cortex/scripts/uri_index_rebuild.sh` (已有 `scripts/lib/` 实用函数) |
| `cortex_html_render(template, data)` | bash `~/.cortex/scripts/html_render.sh` (jinja 简化版或 envsubst) |

## install.sh 引导

末尾加章节:
```
=== MCP 配置 (可选) ===
本插件不再自带 MCP server。如需通过 Obsidian REST API 操作 vault,请安装官方 mcp-obsidian:

1. 在 Obsidian 启用 community plugin "Local REST API",获取 API key
2. 安装 uvx (若未装): pip install uv
3. 添加 MCP server:
   claude mcp add obsidian uvx mcp-obsidian \
     -e OBSIDIAN_API_KEY=<your-key> \
     -e OBSIDIAN_HOST=127.0.0.1 \
     -e OBSIDIAN_PORT=27123
```

## 修订方案 — python 逻辑保留改 CLI

**核心策略**: scripts/mcp/tools/*.py 内业务逻辑 (masking / frontmatter / BM25 / 子图扩展) 全保留 → 改为 CLI 入口 (argparse + JSON stdout) → 安装到 `~/.cortex/scripts/<name>.py`,bash 包装薄壳 `~/.cortex/scripts/<name>.sh` 调用 python。

**好处**: 0 算法回退,只删 MCP 协议层 (~150 行 cortex_mcp.py 注册 + server.py)。

## 文件改动清单

**删除** (~150 行):
- `scripts/mcp/cortex_mcp.py` (MCP server 实现)
- `scripts/mcp/server.py` (MCP 入口)
- `scripts/mcp/tests/*` (113 个 MCP 协议测试)

**保留+改造** (~2000 行 算法不动):
- `scripts/mcp/tools/save.py` → `scripts/cli/save.py` + argparse 入口
- `scripts/mcp/tools/search.py` → `scripts/cli/search.py`
- `scripts/mcp/tools/deep_search.py` → `scripts/cli/deep_search.py`
- `scripts/mcp/tools/ingest_url.py` → `scripts/cli/ingest_url.py`
- `scripts/mcp/tools/ingest_file.py` → `scripts/cli/ingest_file.py`
- 其余 memory/ledger/html_render/session_import/uri_index_rebuild 函数 (cortex_mcp.py 内) → 拆到 `scripts/cli/<name>.py`

**新增 bash 包装** (15 个,每个 ≤ 10 行):
- `scripts/save.sh` → `python3 $PLUGIN_ROOT/scripts/cli/save.py "$@"`
- 同样 ingest_url/ingest_file/search/deep_search/memory_{read,write,recall,forget,promote}/ledger_append/session_import/uri_index_rebuild/html_render

**修改**:
- `.claude-plugin/plugin.json` — 删 `mcpServers`
- `install.sh` — 加 mcp-obsidian 引导
- `agents/cortex-{linker,researcher,archivist}.md` — 改工具引用
- `commands/{lint,save,ingest,memory,recall,search}.md` — 改 MCP 调用
- `skills/cortex-{save,search,ingest,ingest-bulk,lint,digest,install}/SKILL.md` — 工具映射
- `scripts/hooks/user_prompt_submit.sh` — 提示词改 bash 调用

**测试**:
- 删 `scripts/mcp/tests/` (113 个 mcp 测试)
- python tests 由 243 降至 ~130 (lint + cron 保留)
- 新加 bash 脚本的简单 smoke test

## 风险

1. ~~功能回退~~ → CLI 方案后无回退,算法 100% 保留
2. **breaking change**: 用户已装 cortex 后更新 → 旧 `mcp__cortex__*` 调用 fail。缓解: install.sh 提示用户重启 Claude Code 重读 plugin.json
3. **CLI 性能**: 每次调用启动 python 进程 (~50ms 冷启动) vs MCP 常驻进程。可接受 (人工触发场景多)
4. mcp-obsidian 仅文件 CRUD,不替代 cortex 功能,只是补充能力 — install.sh 文案要说清

## 实现顺序

1. 删除 plugin.json:mcpServers + scripts/mcp/ 整目录
2. 写 ~/.cortex/scripts/ bash 工具集 (用 jq + grep + bash 函数封装)
3. 改 agent/skill/command 文本中所有 `mcp__cortex__*` 引用
4. install.sh 加 mcp-obsidian 引导段
5. 调 tests/python/test_mcp_* 删除,跑 lint + cron tests 确认绿
6. 改 README + AGENT.md + 用户文档对应章节

## 验收

- `grep -rn "mcp__cortex__" plugins/tools/cortex/` 无输出
- `cat .claude-plugin/plugin.json | jq '.mcpServers'` 返 `null`
- `bash ~/.cortex/scripts/digest.sh` 跑通无报错 (核心 cron 验收)
- python tests 全绿 (剔除 mcp/)
