# cortex install.sh — codex skills/agents 软连同步

## Goal

install.sh 增加 codex 跨 CLI 兼容步骤: 检测 `~/.codex/` 存在则把 cortex 全部 skills + agents 软连到 `~/.codex/skills/` + `~/.codex/agents/`, 内容以插件市场为准 (差异修复语义: 缺加 / 多删 / 在跳)。

## What I already know

- `~/.codex/` 已存在含 `skills/` 子目录, 现有 symlink 模式: `<name> -> /path/to/skill-dir` (整目录链, 非单 SKILL.md)
- 例: `~/.codex/skills/baoyu-comic -> /Users/luoxin/.agents/skills/baoyu-comic`
- `~/.codex/agents/` 不存在 (codex 未原生用 agents), 但用户要求创建 + 同步
- 插件市场源目录: `$INSTALL_PATH/skills/` + `$INSTALL_PATH/agents/` (install.sh 已知 `$INSTALL_PATH`)
- 整改后 cortex 13 skill + 6 agent (全部 cortex- 前缀)
- install.sh 主流程末尾在 cron 注册后, 适合插同步步骤 (`prune_stale_cron` 之后 / 完成 banner 之前)

## Requirements

### MVP

1. **检测 `~/.codex/` 存在** → 仅当 dir 存在才执行同步 (codex 用户才有); 不存在静默跳过
2. **skills 同步** (`~/.codex/skills/`):
   - mkdir -p 确保目录在
   - 遍历 `$INSTALL_PATH/skills/cortex-*/` 取期望 cortex skill 列表
   - 对每个市场 skill: 检查 `~/.codex/skills/<name>` 状态
     - 不存在 → `ln -s "$INSTALL_PATH/skills/<name>" ~/.codex/skills/<name>` 新建
     - 已是软链 + target 正确 → 跳过
     - 已是软链 + target 错 → `rm` 重链
     - 是真实目录/文件 (非软链) → **警告跳过** (不覆盖用户手动文件)
   - 扫 `~/.codex/skills/cortex-*` 找市场不存在的 (已删 skill 如 cortex-canvas 等): rm symlink
3. **agents 同步** (`~/.codex/agents/`):
   - 同 skills 逻辑, mkdir -p 创建 (新目录), 6 agent 同理软连
4. **范围限定**: 仅管 `cortex-*` 前缀。其他用户自己装的 skill/agent 不动
5. **输出**: 每个操作打日志 (`+ link cortex-search`, `- unlink cortex-canvas (已删)`, `= keep cortex-lint`), 末尾汇总 `synced N skills / M agents`
6. **幂等**: 重复跑 install.sh 第二次该步骤应输出全 keep

### 非交互 + 错误
- `NO_CODEX_SYNC` env / `--no-codex-sync` flag 跳过 (escape hatch)
- 失败 (权限拒 / 路径不可读) 仅 warn 不阻塞整流程
- 干跑 (dry-run) 不必专门支持 (整 install.sh 本身没 dry-run mode)

## Acceptance Criteria

- [ ] install.sh 加 `sync_codex_symlinks()` 函数 + 主流程末尾调用
- [ ] `~/.codex/` 不存在 → 跳过 (无输出 / 一行 skip log)
- [ ] `~/.codex/` 存在 → 创建 `skills/` (已存在) + `agents/` (新建)
- [ ] 13 skill + 6 agent 全软连到 `~/.codex/skills/cortex-*` + `~/.codex/agents/cortex-*`
- [ ] 已废 `cortex-canvas` 等若存在残留 symlink → 删除
- [ ] 用户手动文件 (非软链) 不覆盖, warn 跳过
- [ ] 重复跑 idempotent (二次跑全 keep)
- [ ] `--no-codex-sync` / `NO_CODEX_SYNC=1` 跳过
- [ ] 不影响 install.sh 现 marketplace/plugin update + cron 注册流程

## Definition of Done

- bash 3.2 兼容 (macOS 默认)
- bash -n install.sh 语法通过
- 单元测试可选 (install.sh 本身无单测惯例); 但需手测:
  - `~/.codex/` 不存在: 全流程过, 无 codex 相关输出
  - `~/.codex/` 存在: 跑后 ls -la ~/.codex/skills/cortex-* 全是软链指 marketplace
  - 二次跑: 全 keep
  - 手动建 ~/.codex/skills/cortex-foo (真文件 + 非软链): warn 不覆盖

## Out of Scope

- 不动 ~/.cortex/scripts/* wrapper 安装逻辑
- 不动 marketplace / plugin install 逻辑
- 不动 cron 注册
- 不写 codex 配置 (~/.codex/config.toml 等)
- 不卸载工具 (uninstall 是独立路径)
- 不动其他非 cortex- 前缀 symlink

## Technical Approach

新增 sync_codex_symlinks() 函数, 主流程在 cron 之后 + final banner 之前调用。pure bash, 兼容 3.2 (无关联数组)。

伪码:

```bash
sync_codex_symlinks() {
  [[ -d "$HOME/.codex" ]] || { log_step "~/.codex 不存在, 跳过 codex 同步"; return 0; }
  [[ "${NO_CODEX_SYNC:-}" == "1" ]] && { log_step "NO_CODEX_SYNC=1, 跳过"; return 0; }

  for kind in skills agents; do
    local src_dir="$INSTALL_PATH/$kind"
    local dst_dir="$HOME/.codex/$kind"
    [[ -d "$src_dir" ]] || continue
    mkdir -p "$dst_dir"

    # 期望集 (市场)
    local expected=""
    for path in "$src_dir"/cortex-*; do
      [[ -e "$path" ]] || continue
      local name="$(basename "$path")"
      expected="$expected $name"
      # link 或修复
      _ensure_symlink "$dst_dir/$name" "$path"
    done

    # 扫废: dst 中 cortex-* 不在 expected 集 → 删 (仅 symlink)
    for link in "$dst_dir"/cortex-*; do
      [[ -L "$link" ]] || continue
      local name="$(basename "$link")"
      case " $expected " in *" $name "*) ;; *) rm "$link" && log_step "- unlink $kind/$name (已删)";; esac
    done
  done
}

_ensure_symlink() {
  local dst="$1" src="$2" name="$(basename "$1")"
  if [[ -L "$dst" ]]; then
    if [[ "$(readlink "$dst")" == "$src" ]]; then
      log_dim "= keep $name"
    else
      rm "$dst" && ln -s "$src" "$dst" && log_step "↻ relink $name"
    fi
  elif [[ -e "$dst" ]]; then
    log_warn "$dst 是真实文件/目录 (非软链), 跳过 (避免覆盖用户手动)"
  else
    ln -s "$src" "$dst" && log_step "+ link $name"
  fi
}
```

### CLI flag

- 新增 `--no-codex-sync` flag → 设 `NO_CODEX_SYNC=1`
- env `NO_CODEX_SYNC=1` 同效

## Decision (ADR-lite)

**Context**: codex CLI 与 claude 是平级用户, cortex 整改后 skill/agent 全标准化, 用户跨 CLI 共享只需软链, 无需重装。

**Decision**: install.sh 末尾自动检测 ~/.codex 并同步 cortex-* 软链 (skills + agents); 优雅跳过 codex 不存在场景。

**Consequences**:
- ✅ 跨 CLI 零拷贝共享 skill/agent
- ✅ install.sh 单一入口, codex 用户无需额外步骤
- ✅ skill 升级随 marketplace 更新自动生效 (软链)
- ⚠️ 用户若手动建 cortex-foo 实文件会被 warn 跳过 (非破坏)
- ⚠️ codex 未来若改 skill 加载路径, 需更新 install.sh

## Technical Notes

- 现有 install.sh 已含 `log_step`, `log_warn`, `log_dim`, `_tag` 等 helper
- bash 3.2 兼容: 用 case + 空格分隔字符串而非关联数组 (与 install_wrappers.sh KEEP_LIST 同手法)
- `readlink` 跨平台: macOS BSD `readlink` 无 `-f`, 直接 `readlink "$link"` 返 symlink target 即可
- 主流程插入点: prune_stale_cron 之后 / "✓ cortex 安装完成" banner 之前
