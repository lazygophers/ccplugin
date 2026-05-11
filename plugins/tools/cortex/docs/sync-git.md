# Cortex Vault Git Sync

vault 是知识库, 跨机使用刚需。P5 在 Stop hook 末尾加 **opt-in** auto-commit, 默认完全关闭, 不影响手动流程。

## 模式

| 模式 | `_meta/version.json` 字段 | 行为 |
|------|---------------------------|------|
| 手动 (默认) | `auto_commit=false` | Stop hook 不触碰 git, 用户自己 `git commit / push / pull` |
| 仅 commit | `auto_commit=true, auto_push=false` | Stop 末尾 `git add -A && git commit -m "auto: <UTC>"` |
| commit + push | `auto_commit=true, auto_push=true` | 上述 + `git push origin HEAD` (30s timeout) |

## 启用

### 方式 A: 重跑 cortex-install

`/cortex:install` 会通过 `AskUserQuestion` 询问 3 选项, 自动写入 `_meta/version.json`。

### 方式 B: 手动编辑

```json
{
  "version": "0.x.y",
  "lang": "zh-CN",
  "preset": "lyt",
  "auto_commit": true,
  "auto_push": false
}
```

### 方式 C: CLI 自检

```bash
python3 $CLAUDE_PLUGIN_ROOT/hooks/_lib/git_sync.py status /path/to/vault
python3 $CLAUDE_PLUGIN_ROOT/hooks/_lib/git_sync.py auto   /path/to/vault
```

## 多机协同

推荐 GitHub / GitLab 私库托管, **远端只承担同步**, 不要把 vault 公开。

- 主机 A: `auto_commit=true, auto_push=true`
- 主机 B: 启动 claude 前手动 `git pull` (cortex **不自动 pull**)
- 冲突: 用户 `git mergetool` 手动解, cortex 不介入

```
Host A ──Stop hook──► commit ──push──► origin/main
                                          │
Host B  ── git pull (手动) ◄──────────────┘
```

## 排错

| 现象 | 原因 | 处理 |
|------|------|------|
| Stop 后无 commit | vault 不是 git repo / `auto_commit=false` / 无改动 | 看 `~/.cache/cortex/stop.log` |
| `push 失败 (网络/auth)` | 远端不可达 / 凭证过期 | commit 已在本地, 下次 hook 自动重试; 也可手动 `git push` |
| `commit 失败` | 用户手动 git lock / 权限 | 检查 `git status` 与 hook 权限, 下次 Stop 重试 |
| commit storm | (不会发生) `has_changes` 检测先于 commit | — |

所有 git 调用 timeout (`commit` 10s, `push` 30s), 失败不抛, 不阻塞 Stop hook。

## 风险

- **secret 落 git push**: P0 masking 只在 `ingest/save` 写盘前过滤 URL/HTML/敏感词, **不能保证 vault 内手写笔记不含 secret**。启用 `auto_push=true` 前请自查 vault, 或加 pre-commit hook 跑 secret 扫描。
- **commit 噪声**: Stop hook 频繁触发 = 频繁 commit。建议远端开 squash merge 或定期 rebase 压缩 history。
- **timezone**: commit message 用 **UTC** (`auto: YYYY-MM-DD HH:MM`), 跨机一致, 不随本地时区漂移。
