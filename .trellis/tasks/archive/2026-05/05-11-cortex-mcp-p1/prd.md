# PRD — Cortex P1 MCP python server (骨架 + search/save)

## 背景

cortex v2 14 skill 全靠 prompt 引导模型调 bash/obsidian CLI/mcp__obsidian,**幂等性差、错误处理散、跨平台脆弱**。kioku 通过 MCP server (44 lib + 11 tool) 把核心操作沉到结构化 API,skill 仅作对话入口。

P1 落 MCP 骨架 + 首轮 2 个 tool (search/save) 验通整条链路。其余 4 tool (ingest_url/ingest_file/lint/refactor) 留 P4+。

## 目标

`plugins/tools/cortex/mcp/` 起 python MCP server (stdio transport),注册 2 个 tool,经 `.claude-plugin/plugin.json` 加载,模型通过 `mcp__cortex__search` / `mcp__cortex__save` 直接调用。

## 范围

### 新增文件

```
plugins/tools/cortex/mcp/
├── pyproject.toml           # 声明依赖 mcp>=1.0, 用户 pipx install
├── README.md                # 安装/启动/调试说明
├── server.py                # MCP stdio entry, 注册 tool
├── tools/
│   ├── __init__.py
│   ├── search.py            # cortex_search tool 实现
│   └── save.py              # cortex_save tool 实现
├── lib/
│   ├── __init__.py
│   ├── vault_path.py        # 解析 vault 根 (复用 hooks/_lib/resolve_vault.sh 逻辑)
│   ├── frontmatter.py       # YAML frontmatter 读写
│   ├── wikilinks.py         # [[link]] / ^block-id / ![[note#^id]] 工具
│   └── lock.py              # fcntl flock 防并发写
└── tests/
    ├── __init__.py
    ├── test_search.py
    ├── test_save.py
    └── test_lib.py
```

复用 `plugins/tools/cortex/hooks/_lib/masking.py` (P0 已交付),`mcp/tools/save.py` import 它。

### 修改文件

- `.claude-plugin/plugin.json` — 加 `mcpServers.cortex` 段
- `install.sh` — `step_mcp_install()` 检测 pipx + `mcp` pkg,缺则交互提示
- `skills/cortex-search/SKILL.md` — 首选 `mcp__cortex__search`,L1-L5 回退作 fallback
- `skills/cortex-save/SKILL.md` — 首选 `mcp__cortex__save`,L1-L3 回退作 fallback
- `AGENT.md` — Skills 设计原则段加 §MCP 主路径 子段

### 不在范围

- 其它 4 tool (ingest_url/ingest_file/lint/refactor) → P4
- hooks .sh 不改语言
- 其它 12 skill 不改
- vendor wheel 不进仓

## 详细规范

### 1. `mcp/pyproject.toml`

```toml
[project]
name = "cortex-mcp"
version = "0.1.0"
description = "MCP server for cortex Obsidian knowledge base"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
]

[project.scripts]
cortex-mcp = "cortex_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build]
packages = ["."]
```

用户装:`pipx install ${CLAUDE_PLUGIN_ROOT}/mcp` (本地路径 install,无需发包)。

### 2. `mcp/server.py`

```python
#!/usr/bin/env python3
"""Cortex MCP server — stdio transport."""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

# Allow running directly without install
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tools.search import SEARCH_TOOL, handle_search
from tools.save import SAVE_TOOL, handle_save

app = Server("cortex")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [SEARCH_TOOL, SAVE_TOOL]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "search":
        return await handle_search(arguments)
    if name == "save":
        return await handle_save(arguments)
    raise ValueError(f"unknown tool: {name}")

def main() -> None:
    async def _run():
        async with stdio_server() as (r, w):
            await app.run(r, w, app.create_initialization_options())
    asyncio.run(_run())

if __name__ == "__main__":
    main()
```

### 3. `mcp/tools/search.py`

签名:

```python
SEARCH_TOOL = Tool(
    name="search",
    description="搜索 cortex vault: 多级回退 (hot → index → SC → rg)",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索词"},
            "limit": {"type": "integer", "default": 10},
            "scope": {
                "type": "string",
                "enum": ["all", "concepts", "domains", "log"],
                "default": "all",
            },
        },
        "required": ["query"],
    },
)

async def handle_search(args: dict) -> list[TextContent]: ...
```

回退顺序:
1. 读 `hot.md`,grep query
2. 读 `index.md`,grep query
3. 若 `SC_API` 可达(`http://127.0.0.1:27123` Smart Connections REST),POST `/search` query
4. `rg --json -i <query> <vault>/wiki/` (cap 50 hits)

输出结构化 list:`[{path, title, snippet, score, source}]`,序列化 JSON 入 `TextContent.text`。

### 4. `mcp/tools/save.py`

签名:

```python
SAVE_TOOL = Tool(
    name="save",
    description="落档发现到 cortex vault: frontmatter + masking + block-id + index/hot 同步",
    inputSchema={
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["concept", "domain", "log"],
            },
            "title": {"type": "string"},
            "body": {"type": "string", "description": "markdown 正文"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "host": {"type": "string", "description": "kind=domain 时必填"},
            "org": {"type": "string"},
            "repo": {"type": "string"},
        },
        "required": ["kind", "title", "body"],
    },
)
```

流程:
1. `masking.mask(body)` 前置(import P0 module)
2. 解析路径:
   - `concept` → `wiki/10_concepts/<slug(title)>.md`
   - `domain` → `wiki/30_domains/<host>/<org>/<repo>/<slug(title)>.md`
   - `log` → `wiki/log/YYYY-MM/<HH-MM-slug(title)>.md`
3. 加 frontmatter (`type/title/created/tags/aliases`)
4. `wikilinks.add_block_id(body)` — 段落末加 `^cortex-<sha8>`
5. `lib.lock.flock_write(path, content)` — flock 防并发
6. `hot.md` / `index.md` patch (追加新链接)
7. 返回 `{path, block_ids: [...], hits: <masking hit count>}`

### 5. `mcp/lib/lock.py`

```python
import fcntl, os
from contextlib import contextmanager

@contextmanager
def file_lock(path: str, timeout: float = 5.0):
    """advisory flock; timeout 后 raise TimeoutError."""
```

### 6. `.claude-plugin/plugin.json` 增段

```json
{
  "mcpServers": {
    "cortex": {
      "command": "cortex-mcp",
      "args": [],
      "env": {
        "CORTEX_VAULT_PATH": "${CORTEX_VAULT_PATH:-}"
      }
    }
  }
}
```

如 pipx 装在 `~/.local/bin`,`cortex-mcp` 在 PATH。否则 fallback `python3 ${CLAUDE_PLUGIN_ROOT}/mcp/server.py`。

### 7. `install.sh` 增 `step_mcp_install()`

```bash
step_mcp_install() {
  if ! command -v pipx >/dev/null 2>&1; then
    log_warn "pipx 未安装, MCP server 不可用. 装法: brew install pipx"
    log_warn "跳过 MCP 安装, cortex skill 将退回 CLI/MCP-obsidian 路径."
    return 0
  fi
  if pipx list --short 2>/dev/null | grep -q '^cortex-mcp '; then
    log_info "cortex-mcp 已装 (pipx)"
    if [ "${REINSTALL:-0}" = "1" ]; then
      log_info "强制重装"
      pipx install --force "${PLUGIN_ROOT}/mcp"
    fi
  else
    log_info "装 cortex-mcp via pipx"
    pipx install "${PLUGIN_ROOT}/mcp" || log_warn "pipx 装失败, MCP 不可用"
  fi
}
```

在 `main()` 中 `step_doctor` 前调。

### 8. skill 改动

`skills/cortex-search/SKILL.md` 在工作流首段加:

```markdown
## 调用优先级

1. **优先**: `mcp__cortex__search` (MCP server 已装) — 结构化 JSON 输出, schema 稳定
2. **回退**: 下述 L1-L5 (CLI / Smart Connections / mcp__obsidian / rg) — MCP 不可达时
```

`skills/cortex-save/SKILL.md` 同模式,首选 `mcp__cortex__save`。

### 9. AGENT.md §MCP 主路径

```markdown
## MCP 主路径 (P1)

cortex P1 起,核心操作沉 MCP server (`mcp__cortex__*`),skill 作对话入口。

| skill | MCP tool | 回退 |
|-------|---------|------|
| cortex-search | `mcp__cortex__search` | L1 obsidian CLI / L5 rg |
| cortex-save | `mcp__cortex__save` | L1 obsidian CLI / L3 直接写盘 |

MCP server 装:`pipx install ${CLAUDE_PLUGIN_ROOT}/mcp` (install.sh 自动)。
未装时 skill 自动退回 L1-L5 链路, 不阻塞使用。
```

## 验收标准

1. `mcp/` 文件齐全,`python3 mcp/server.py < /dev/null` 不崩(虽不能完整 handshake)
2. `pipx install plugins/tools/cortex/mcp/` 成功,`which cortex-mcp` 返路径
3. `pytest plugins/tools/cortex/mcp/tests/` 全绿:
   - search: hot 命中、index 命中、rg fallback、空结果各 1 用例
   - save: concept/domain/log 三种 kind 各 1 用例,masking 前置生效,block-id 注入,flock 并发安全
4. `.claude-plugin/plugin.json` `mcpServers.cortex` 段有效 JSON,通过 `python3 -c "import json; json.load(open('...'))"`
5. install.sh `--reinstall` 模式重装 pipx pkg,无 pipx 时打 warn 不阻塞
6. `claude -p "搜 cortex 知识库 P0 安全硬化"` 验证模型优先调 `mcp__cortex__search`(若模型未识别,记 backlog)
7. `cortex-search/SKILL.md` + `cortex-save/SKILL.md` 文档明示 MCP 优先 + 回退序
8. AGENT.md §MCP 主路径 段存在

## 不变量

- MCP server 纯 stdlib + `mcp` pkg,无其它外部依赖
- vault 路径解析与 hooks/_lib/resolve_vault.sh 一致(优先 `_meta/version.json:.vault_path`,缺则 `~/Documents/<vault>`)
- save tool 写盘前必调 masking
- 所有 tool inputSchema 严格,缺字段 raise `ValueError`,经 MCP 协议返结构化 error

## 风险

- **pipx 与 plugin 路径耦合**:`pipx install <path>` 装的是 snapshot,plugin 升级后需重装。**缓解**:install.sh `--reinstall` 触发 `pipx install --force`
- **MCP server 启动失败静默**:claude 启动时 MCP 加载失败仅打日志,用户无感知。**缓解**:`cortex-doctor` skill 加 `mcp__cortex__search ping` 健康检查项 (P1.5 增量)
- **Win 兼容**:`fcntl` Win 无。**缓解**:`lib/lock.py` 用 `try: import fcntl` fallback msvcrt.locking 或 noop + warn(P1 仅 macOS/Linux,Win 留 P4 backlog)
- **依赖版本漂移**:`mcp` pkg API 不稳。**缓解**:pin `mcp>=1.0,<2.0`,CI 验证(后续 task)
