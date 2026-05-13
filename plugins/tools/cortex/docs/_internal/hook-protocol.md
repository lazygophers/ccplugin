# Hooks 机制

本文回答：cortex 的 4 个 hook (`SessionStart` / `Stop` / `SubagentStop` / `PostCompact`) 何时触发、协议是什么、启发式落档怎么判定、与 Obsidian Git 如何协调。
适用读者：想理解 cortex 自动行为的用户、调试"hook 不生效"的运维。

## 4 个 hook 一览

| Hook | 触发时机 | 行为 | 异步 |
|------|----------|------|------|
| `SessionStart` | startup / resume / clear | 注入 AGENT.md + hot.md 摘要 | 否 (timeout 1500ms) |
| `Stop` | 主会话结束 | 启发式判断是否落档 | 是 (timeout 5000ms) |
| `SubagentStop` | 子 agent 结束 | 同 Stop, reason=subagent-stop | 是 |
| `PostCompact` | compact 摘要后 | 强制落档 compact 摘要 | 是 (timeout 3000ms) |

注册见 `.claude-plugin/plugin.json` 的 `hooks` 字段。

## wrapped JSON 协议

所有 hook 走 Claude Code v2 wrapped JSON schema。命中时 stdout 输出：

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "...注入正文..."
  }
}
```

未命中时 stdout 留空, 退出码 0。**永不阻断会话**。

## SessionStart 行为

入口：`hooks/session_start.sh`。

```text
stdin → (不消费) → 解析 vault → 不命中则沉默退出
                                ↓ 命中
                        读 AGENT.md 模板 + hot.md (前 5KB)
                                ↓
                        替换 {{VAULT_PATH}} / {{HOT_CACHE_PREVIEW}} / {{INDEX_ENTRY_COUNT}}
                                ↓
                        emit v2 wrapped JSON
```

注入正文模板见 `../AGENT.md`。注入后用户在会话中可看到：

```text
## Cortex 已连接
vault: /Users/me/notes
hot cache: (已加载, 见下文)
索引: index.md (42 条)

### 协作约定
1. 先搜后问 — ...
2. 落档 — ...
...
```

`additionalContext` 软上限 ~10KB, hot.md 读取硬上限 5KB, 防止上下文爆炸。

## Stop / SubagentStop 启发式落档

入口：`hooks/stop.sh` → 调度 `hooks/_lib/save_session.py`。

### 流程

```text
stdin v2 JSON
  ↓
解析 transcript_path / stop_hook_active / hook_event_name
  ↓
stop_hook_active=true? → 是 → 跳过 (防循环)
  ↓ 否
解析 vault → 不命中 → 跳过
  ↓
transcript 文件存在? → 否 → 跳过
  ↓ 是
调度 save_session.py --vault X --transcript Y --reason {stop|subagent-stop|compact}
  ↓
rc=0 → emit v2 wrapped JSON ("📝 cortex 已落档 ...")
rc=2 → 启发式未达阈值 (静默)
rc=其他 → 失败 (log)
```

### 启发式判定 (rc=2 表示未达阈值)

`save_session.py` 评估 transcript：

- `min_lines` (默认 30): transcript 行数下限
- `min_chars` (默认 800): 字符数下限
- `skip_if_only_questions` (默认 true): 全是疑问句不归档
- 内容平凡度评分: 多 CRUD 操作 / 通用编程问答 → 平凡

任一未达 → rc=2 → 静默跳过。可通过 `~/.cortex/config.json` 的 `save.*` 字段调整 (见 `安装与配置.md`)。

### reason 字段映射

```bash
case "$HOOK_EVENT" in
  SubagentStop) REASON="subagent-stop" ;;
  PostCompact)  REASON="compact" ;;
  Stop|*)       REASON="stop" ;;
esac
```

落档文件名前缀根据 reason 不同, 便于事后筛选。

## PostCompact 行为

入口：`hooks/post_compact.sh`。

差异：

- 总是落档 (跳过启发式判定 — compact summary 本身已是浓缩信息)。
- `save_session.py --force` 标志, 绕过 `min_lines` / `min_chars` 检查。
- 写入 `记忆/L4-流水账/ledger/YYYY-MM/DD-HHMM-compact.md`。

## 与 Obsidian Git 协调 (auto-commit)

cortex 默认会在 `cortex-save` 写入后 auto-commit, 但若检测到 vault 已装 Obsidian Git 插件 (`.obsidian/plugins/obsidian-git/` 存在), 会**自动关闭** auto-commit, 让 OGit 接管。

判定逻辑：

```bash
test -d "$VAULT/.obsidian/plugins/obsidian-git" && AUTO_COMMIT=false
```

避免双重 commit 与冲突。

## 日志位置

所有 hook 失败/调试日志统一写到 `~/.cache/cortex/`:

| 文件 | 内容 |
|------|------|
| `~/.cache/cortex/session_start.log` | vault 解析、注入失败 |
| `~/.cache/cortex/stop.log` | Stop / SubagentStop 流程、启发式 rc |
| `~/.cache/cortex/post_compact.log` | PostCompact 流程 |
| `~/.cache/cortex/save.log` | save_session.py 内部 |

设 `CORTEX_DEBUG=1` 打印更多。

## 常见误解

- **"hook 没注入"** → 90% 是 vault 路径未命中。先 `echo $(jq -r .vault ~/.cortex/config.json)`, 再跑 `cortex-doctor`。
- **"Stop 没落档"** → 多半是启发式判定为平凡。显式说"归档"强制触发。
- **"PostCompact 写了空文件"** → transcript 不可读 (CC 还未 flush), 偶发, 看 `~/.cache/cortex/post_compact.log`。
- **"hook 阻塞会话"** → 不会。所有 hook `exit 0`, 异步 hook 加 `async: true`, timeout 强制结束。

## 不写 noop hook 的教训

cortex 拒绝注册"什么都不做"的 hook (例如只 log 不输出)。教训自 commit `07e713d4` (移除全部语言插件的空 hooks)。空 hook 浪费 CC 启动时间且让用户困惑。

## 相关文档

- `安装与配置.md` — vault 路径解析与启发式阈值配置
- `Skills 详解.md` — cortex-save / cortex-fold 等被 hook 调度
- `故障排查.md` — hook 不生效的诊断流程
- `架构设计.md` — hook 与 skill 的整体时序
- 协议：[Claude Code hooks v2 wrapped JSON](https://docs.claude.com/en/docs/claude-code/hooks)
