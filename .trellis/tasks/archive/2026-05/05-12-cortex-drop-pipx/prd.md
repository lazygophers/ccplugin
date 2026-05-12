# PRD — 移除 cortex 插件对 pipx 的依赖

## 背景

用户偏好系统 python3 + pip 装全局,不用 venv/pipx。现 cortex 三处依赖 pipx:

1. `install.sh:step_mcp_install` — `pipx install <plugin>/mcp`
2. `.claude-plugin/plugin.json:mcpServers.cortex.command="cortex-mcp"` — 假设 pipx console-script
3. `scripts/lib/stream_progress.sh` 路径 3 — `~/.local/pipx/venvs/cortex-mcp/bin/python` 探测

## 目标

全部走系统 python3 + `pip3 install --user <deps>`。`pyproject.toml` 保留作本地开发用 (`pip install -e .` / `uv sync`),但 install.sh 不再依赖 pipx。

## 范围

### 修改

- `plugins/tools/cortex/install.sh`:
  - 删 `step_mcp_install` pipx 路径,改 `pip3 install --user mcp pypdf ebooklib python-docx rich`
  - 函数重命名为 `step_python_deps`,保留 `--reinstall` 触发 `pip3 install --user --upgrade <deps>`
- `plugins/tools/cortex/.claude-plugin/plugin.json:mcpServers.cortex`:
  - `command` 改 `python3`
  - `args` 改 `["${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]`
- `plugins/tools/cortex/scripts/lib/stream_progress.sh`:
  - 删路径 3 (pipx venv python 探测),保留路径 1 (PATH cortex-stream) + 路径 2 (系统 python3 + rich) + fallback
  - 数组 `venv_pys` 删,`PIPX_HOME` 变量删
- `plugins/tools/cortex/install.sh:step_rich_install`:
  - 现仅探测,缺则提示;无需改动 (rich 已并入 step_python_deps 自动装,但保探测段告诉用户成功 OR 失败)
  - 可合并入 step_python_deps

### 不在范围

- 不动 `mcp/pyproject.toml` (本地开发 + CI 仍可用)
- 不动 `mcp/server.py` / tools / lib (代码不动)
- 不动 hooks / P0-P6 / Phase A 实施

## 详细规范

### 1. install.sh step_python_deps (替换 step_mcp_install)

```bash
CORTEX_PYTHON_DEPS=(mcp pypdf ebooklib python-docx rich)

step_python_deps() {
  if ! command -v python3 >/dev/null 2>&1; then
    log_error "python3 not found. install Python 3.10+ first."
    return 1
  fi

  # 检测已装包
  local missing=()
  for pkg in "${CORTEX_PYTHON_DEPS[@]}"; do
    # python-docx import name = docx
    local import_name="$pkg"
    [[ "$pkg" == "python-docx" ]] && import_name="docx"
    if ! python3 -c "import $import_name" 2>/dev/null; then
      missing+=("$pkg")
    fi
  done

  if [[ "${#missing[@]}" -eq 0 ]]; then
    log_info "python deps 已装 (mcp pypdf ebooklib python-docx rich)"
    if [[ "${REINSTALL:-0}" == "1" ]]; then
      log_step "强制升级 python deps"
      pip3 install --user --upgrade "${CORTEX_PYTHON_DEPS[@]}" >&2 || {
        log_warn "pip3 升级失败 (rc=$?), 现有装不变"
        return 0
      }
    fi
    return 0
  fi

  log_step "安装 python deps via pip3 --user: ${missing[*]}"
  if ! pip3 install --user "${missing[@]}" >&2; then
    log_warn "pip3 install 失败. MCP server / cortex_stream 可能不可用."
    log_hint "手动: pip3 install --user ${missing[*]}"
    return 0  # 不阻塞
  fi
  log_ok "python deps 已装"
}
```

`main()` 中调用位置:替换原 `step_mcp_install`,删 `step_rich_install` (功能并入)。

### 2. plugin.json `mcpServers.cortex` 改 python3 直跑

```json
"mcpServers": {
  "cortex": {
    "command": "python3",
    "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/server.py"],
    "env": {
      "CORTEX_VAULT_PATH": "${CORTEX_VAULT_PATH:-}",
      "CORTEX_PLUGIN_ROOT": "${CLAUDE_PLUGIN_ROOT}"
    }
  }
}
```

注意:Claude Code 自动展开 `${CLAUDE_PLUGIN_ROOT}` 为插件绝对路径。

### 3. stream_progress.sh 删 pipx venv 路径

`cortex_stream_runner` 路径 3 (pipx venv 探测) 整段删:

```bash
# 删:
# local pipx_home="${PIPX_HOME:-$HOME/.local/pipx}"
# local venv_pys=(
#   "$pipx_home/venvs/cortex-mcp/bin/python"
#   "$pipx_home/venvs/cortex-mcp/bin/python3"
# )
# for py in "${venv_pys[@]}"; do
#   if [[ -x "$py" ]] && "$py" -c "import rich" 2>/dev/null; then
#     "$py" "$stream_script" --label "$label" --timeout "$timeout" -- "$@"
#     return $?
#   fi
# done
```

最终 cortex_stream_runner 3 级:
1. 系统 python3 + import rich → 跑脚本 (优先)
2. PATH cortex-stream (向后兼容, 用户若手动装 pipx 仍工作)
3. fallback warn + raw exec

## 验收

1. `bash ~/.cortex/scripts/lint.sh` 走路径 1 (系统 python3 + rich) → rich Live UI
2. `python3 -c "import json; json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))"` 合法,`mcpServers.cortex.command=="python3"`
3. install.sh: 系统已装 deps → log_info 跳过;缺则 pip3 install --user;`--reinstall` 触发 upgrade
4. `bash -n install.sh stream_progress.sh` 语法绿
5. claude 重启后 mcpServers.cortex 加载成功 (python3 + server.py)
6. P0-P6 / Phase A 不回归: `bash plugins/tools/cortex/tests/run.sh` 全绿

## 不变量

- 纯 bash + pip3 + python3, 禁 pipx 引用
- pyproject.toml 保留 (本地开发 / CI / `pip install -e .` 仍可用)
- `${CLAUDE_PLUGIN_ROOT}` 由 Claude Code 注入,plugin.json env 透传
- bash 3.2 兼容
- pip3 install 失败 fail-soft, 不阻塞 install
- python3 缺则 install.sh error 退出 (合理硬要求)

## 风险

- **pip3 install --user 与 conda env 交互**:miniconda 用户 `pip3` 可能装到 conda env site-packages 而非 ~/.local. **缓解**:用户偏好已确认接受系统全局
- **python3 版本 < 3.10**:mcp pkg 要求 ≥ 3.10. **缓解**:install.sh 加版本探测 warn
- **多 python 共存**:用户 PATH 第一个 python3 可能不是 rich 所在那个. **缓解**:stream_progress.sh 已用 `python3 -c "import rich"` 探测,缺则 fallback
- **plugin.json command="python3" 无绝对路径**:依赖 claude 启动时 PATH. macOS GUI 启动 claude 可能 PATH 受限. **缓解**:文档建议 `/usr/local/bin/python3` 或显式 PATH;或 install.sh 探测后写入 plugin.json (复杂, 留 backlog)
