# install.sh 已安装检测 + 强制升级

## Goal

`bash install.sh` 重复跑时不要默默覆盖。本地态 (`~/.cortex/config.json` + `~/.cortex/scripts/*.sh`) 分别检测分别问; 远端态 (marketplace + plugin) 一律强制升级。

## What I already know

- `install.sh` 流程: bootstrap (marketplace add/install) → prompt vault/lang → 写 `~/.cortex/config.json` → 生成 `~/.cortex/scripts/*` wrappers → cron 提示
- bootstrap_via_claude 已通过 `claude plugins marketplace update` + `claude plugins update` 做幂等升级 (远端态已经处理好)
- 本地态目前无检测: 直接 atomic write 覆盖 config; install_wrappers.sh 默认覆盖, 仅 `--no-overwrite` 可选 skip
- prompt_yes_no 已就绪 (bash 3.2 兼容, tty 友好)

## Requirements

1. **远端态强制升级**: marketplace / plugin 若已装, 一律 `claude plugins marketplace update` + `claude plugins update` (已实现, 保留)
2. **本地态分别检测分别处理**:
   - `~/.cortex/config.json` 存在 → 询问 "config 已存在, 覆盖?" (Y/n, 默认 N)
   - `~/.cortex/scripts/` 存在且非空 → 询问 "wrappers 已存在, 重生?" (Y/n, 默认 N)
3. **"否" 行为**: 跳过本地写入, 仍跑远端升级 (这是 install.sh 主入口的核心契约)
4. **非交互默认**: 无 tty 且无 flag → 两个都覆盖 (无脑重装)
5. **`--reinstall` flag**: 跳过两个提示, 强制覆盖 config + 重生 wrappers (= 非交互默认行为)
6. **doctor.sh 真调用**: wrapper 改用 `claude --bare -p --append-system-prompt "$(cat $INSTALL_PATH/skills/cortex-doctor/SKILL.md)" "<task desc>"` 实际触发 cortex-doctor skill (headless 模式不支持 slash command, 故用 `--append-system-prompt` 注入 SKILL.md)

## Acceptance Criteria

- [ ] 首次跑 (本地全空): config 写入 + wrappers 全生成, 无提示
- [ ] 二次跑 (交互, 默认 N): 远端升级跑, config 不变, wrappers 不变
- [ ] 二次跑 (交互, config Y / wrappers N): config 重写, wrappers 不变
- [ ] 二次跑 (`--reinstall`): 无提示, config + wrappers 全覆盖
- [ ] 二次跑 (curl|bash 非交互, 无 flag): 无提示, 全覆盖
- [ ] 二次跑 marketplace + plugin 都已装: bootstrap 阶段输出 update 而非 install
- [ ] `bash ~/.cortex/scripts/doctor.sh` 实际触发 claude headless 运行 cortex-doctor skill, 输出健康检查结果 (非交互)

## Definition of Done

- `bash -n` 通过
- 手工跑 5 个 AC 场景过
- README "重复执行" 段补一句 `--reinstall` 说明
- 提交一个 `feat(cortex):` commit

## Out of Scope

- 提示拒绝后给 dry-run 摘要 (后续可加)
- 升级前备份 config.json (后续可加)

## Technical Approach

```
parse_args:
  --reinstall → REINSTALL=1
  --non-interactive → NON_INTERACTIVE=1   # 已有? 检查

detect_local_state:
  CONFIG_EXISTS = [ -f ~/.cortex/config.json ]
  WRAPPERS_EXIST = [ -d ~/.cortex/scripts ] && [ "$(ls ~/.cortex/scripts/*.sh 2>/dev/null)" ]

should_overwrite_config:
  if REINSTALL=1: yes
  elif no tty: yes        # 非交互默认
  elif !CONFIG_EXISTS: yes
  else: prompt_yes_no "config.json 已存在, 覆盖? [y/N]" N

should_regen_wrappers:
  同上, key 换成 wrappers
```

写入阶段按 flag 跳过即可; bootstrap_via_claude 不动。

## Decision (ADR-lite)

- **Context**: 重复跑 install.sh 默默覆盖, 不可控
- **Decision**: 本地态分维度独立判定 (config / wrappers 解耦), 远端态固定强制升级
- **Consequences**:
  - + 用户可保留自定义 config 同时升级 plugin
  - + `--reinstall` 一键重置
  - - 提示多一层 (两次 y/n), 但仅 in-place 重跑时触发

## Technical Notes

- `install.sh:227 prompt_value` / `install.sh:242 prompt_yes_no` 已可用
- `install_wrappers.sh --no-overwrite` 已存在, 复用作为 wrappers skip 通道
- atomic write 路径: `_atomic_write(_config_path(), out)` in `cortex_config.py cmd_init`
- 非交互检测: `[ -t 0 ]` + 无 `--reinstall` 时是 "true 非交互" → 走默认覆盖
- claude headless 限制 (官方文档): `-p` 模式下 slash command 不可用, 用 `--append-system-prompt` 注入 SKILL.md 内容 + 任务描述代替 `/cortex-doctor`
- `--bare` 跳过 hooks/plugins/MCP/CLAUDE.md 自动发现, CI/wrapper 友好
