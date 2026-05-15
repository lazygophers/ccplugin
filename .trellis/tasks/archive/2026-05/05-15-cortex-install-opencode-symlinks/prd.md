# install.sh — opencode 软连同步 (与 codex 对齐) + 抽共享

## Goal

install.sh 扩展 codex 同步逻辑到 opencode (`~/.config/opencode/`)。把 cortex 全部 skills + agents 软连到 opencode 对应目录, 内容以插件市场为准 (缺加 / 多删 / 在跳)。重构为通用 sync 函数支持多目标。

## What I already know

- 上一 PR (08478312) 已加 `sync_codex_symlinks` + `_ensure_codex_symlink` (install.sh L537-591)
- opencode 路径: `~/.config/opencode/skills/` + `~/.config/opencode/agents/`
- codex 路径: `~/.codex/skills/` + `~/.codex/agents/`
- 同步语义相同 (cortex-* 前缀 / idempotent / agents 软链去 .md 后缀)
- 用户答: opencode 也同步 agents (与 codex 对齐)

## Requirements

### MVP

1. **重构 `_ensure_codex_symlink` → `_ensure_cli_symlink`** (函数名通用化, 行为不变)
2. **重构 `sync_codex_symlinks` → `sync_cli_symlinks <cli-name> <root-dir>`** 通用函数:
   - 参数: `cli-name` (e.g. "codex" / "opencode") 用于日志, `root-dir` (e.g. `$HOME/.codex` / `$HOME/.config/opencode`) 容器目录
   - 不存在 → 跳过
   - 否则同步 skills + agents 两 kind
3. **新增 `sync_external_clis()` 顶层函数** — 调用 sync_cli_symlinks 两次:
   - `sync_cli_symlinks codex "$HOME/.codex"`
   - `sync_cli_symlinks opencode "$HOME/.config/opencode"`
4. **flag 通用化**:
   - 保留 `--no-codex-sync` + `NO_CODEX_SYNC=1` (skip codex 段)
   - 新增 `--no-opencode-sync` + `NO_OPENCODE_SYNC=1` (skip opencode 段)
   - 新增 `--no-external-sync` + `NO_EXTERNAL_SYNC=1` (skip 全部, 一键关)
5. **主流程调用**: 现 `sync_codex_symlinks` 改为 `sync_external_clis`
6. **目录约定**: opencode skills/agents 软链名规则与 codex 一致 (skill 整目录, agent 软链名去 .md)

### 暂不实现 (out-of-scope)

- 不动 marketplace/plugin/cron 流程
- 不写 opencode 配置 (类似 opencode.json 等)
- 不动 ~/.cortex/scripts/* wrapper
- 不动 README (留下一轮 cleanup 同步)

## Acceptance Criteria

- [ ] 重构: `_ensure_codex_symlink` → `_ensure_cli_symlink`, `sync_codex_symlinks` → `sync_cli_symlinks` + 新 `sync_external_clis`
- [ ] codex 行为不变 (向后兼容)
- [ ] opencode 在 `~/.config/opencode/` 存在时同步 13 skill + 6 agent
- [ ] opencode 不存在时静默跳过
- [ ] 3 flag 全在: `--no-codex-sync` / `--no-opencode-sync` / `--no-external-sync`
- [ ] 3 env 同效
- [ ] `bash -n` 通过
- [ ] bash 3.2 兼容
- [ ] 模拟测试: 临时 HOME 含两个 dir, 跑后两套 symlink 全建
- [ ] idempotent (二次跑全 keep)

## Definition of Done

- bash 语法过
- 手动模拟两个目标 dir 跑 sync_external_clis, 验证 19 + 19 = 38 软链建立 (13 skill + 6 agent × 2 CLI)
- 不影响现有 codex 流程

## Out of Scope

- 不动其他 CLI (cursor / claude-desktop 等), 仅 codex + opencode
- 不动 README 同步说明 (后续 PR)
- 不写卸载 / uninstall 逻辑

## Technical Approach

通用化设计, 减少重复:

```bash
_ensure_cli_symlink() {  # 与原 _ensure_codex_symlink 完全相同, 仅改名
  ...
}

sync_cli_symlinks() {
  local cli_name="$1" root_dir="$2"
  if [[ ! -d "$root_dir" ]]; then
    log_info "$cli_name 不存在 ($root_dir), 跳过"
    return 0
  fi
  local skip_var="NO_${cli_name^^}_SYNC"  # bash 4+; 3.2 用 case 替代
  # bash 3.2 兼容:
  case "$cli_name" in
    codex)    [[ "${NO_CODEX_SYNC:-}" == "1" ]] && { log_info "NO_CODEX_SYNC=1"; return 0; } ;;
    opencode) [[ "${NO_OPENCODE_SYNC:-}" == "1" ]] && { log_info "NO_OPENCODE_SYNC=1"; return 0; } ;;
  esac

  local kind src_dir dst_dir path name link expected
  for kind in skills agents; do
    src_dir="$INSTALL_PATH/$kind"
    dst_dir="$root_dir/$kind"
    [[ -d "$src_dir" ]] || continue
    mkdir -p "$dst_dir"

    expected=""
    shopt -s nullglob
    for path in "$src_dir"/cortex-*; do
      [[ -e "$path" ]] || continue
      name="$(basename "$path")"
      [[ "$kind" == "agents" ]] && name="${name%.md}"
      expected="$expected $name"
      _ensure_cli_symlink "$dst_dir/$name" "$path"
    done

    for link in "$dst_dir"/cortex-*; do
      [[ -L "$link" ]] || continue
      name="$(basename "$link")"
      case " $expected " in
        *" $name "*) ;;
        *) rm "$link" && log_step "- unlink $cli_name/$kind/$name (已删)" ;;
      esac
    done
    shopt -u nullglob
  done
}

sync_external_clis() {
  [[ "${NO_EXTERNAL_SYNC:-}" == "1" ]] && { log_info "NO_EXTERNAL_SYNC=1, 跳过所有"; return 0; }
  sync_cli_symlinks codex "$HOME/.codex"
  sync_cli_symlinks opencode "$HOME/.config/opencode"
}
```

## Decision (ADR-lite)

**Context**: opencode 与 codex 都用 `<root>/skills/<name>` + `<root>/agents/<name>` 软链布局, cortex 应跨 4 CLI (claude / codex / opencode / opencode 之外可后续扩) 统一支持。

**Decision**: 把 codex 专用 sync 函数泛化为 `sync_cli_symlinks <name> <root>`, 顶层 `sync_external_clis` 统一调度。3 个 escape flag (codex / opencode / 全部)。

**Consequences**:
- ✅ 加新 CLI (cursor 等) 只需 1 行 sync_cli_symlinks 调用
- ✅ codex 旧行为完全兼容
- ✅ 用户细粒度控制 (单 CLI 关 / 全关)
- ⚠️ bash 3.2 无 `${var^^}`, 用 case 路由 NO_X_SYNC env 检查
