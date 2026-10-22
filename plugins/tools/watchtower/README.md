# watchtower

Claude Code mod pane 插件：常驻面板展示**当前 session 最近 10 条 agent 返回值**。

数据直接从当前 session 的 transcript（Claude Code 自动写的 `~/.claude/projects/<项目路径编码>/<session_id>.jsonl`）读出，滤出 Task/Agent 的 tool_use/tool_result 配对（含后台异步 agent 的 task-notification `<result>`）。**零自建存储**：不写 hook 落盘、不建数据目录、无清理逻辑；插件坏了只坏展示层，transcript 数据无损。

## 装了以后看到什么

Claude Code 界面多一块常驻面板 **Agent returns**：

- `session.start` 时自动打开，每 2 秒刷新一次（`clock.every` + `ui.render`）
- 每行 = 一条 agent 返回值：时间 + 正文第一个非空行（超宽截断；窄面板放不下 taskId，不渲染）
- 最多 10 条，新的在前；面板可手动关闭，关闭后本 session 不再自动重开
- 终端太窄 dock 不下 pane 时，面板保持未绘制状态，不报错

不做的事：不跨 session / 历史查询，不做返回值筛选、搜索、导出。

已知限制：session.start 事件不带 sessionId 时，取该项目目录下 mtime 最新的 transcript 兜底；同项目并发第二个 session 可能读到别的 session 的记录。

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin watchtower@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install watchtower@ccplugin-market
```

## 验证

1. 装好插件后新开一个 Claude Code session，确认右侧出现 Agent returns 面板
2. 让 Claude 派一个 agent（Task，同步或后台异步均可），等它返回
3. 面板应在返回后 2 秒内出现该返回值（时间、正文）
4. 无头环境验证：跑一个 `claude -p` session 派 Task agent，然后对该 session 的 transcript 跑解析器，确认能读出刚产生的返回值：
   ```bash
   node -e 'import("./plugins/tools/watchtower/scripts/parse-transcript.mjs").then(m => console.log(m.recentAgentReturns("<transcript.jsonl>", 10)))'
   ```

## 结构

```
.claude-plugin/plugin.json   # 插件清单
hooks/hooks.json             # 声明 hooks module
hooks/register.ts            # pane 生命周期：session.start 绑引擎开面板，clock.every 刷新，ui.close 关闭
hooks/views/pane.tsx         # 面板视图
scripts/parse-transcript.mjs # transcript 定位 + agent 返回值解析（locateTranscript / recentAgentReturns）
```

transcript 内部格式无官方契约，字段结构靠实测（`.scratch/research/2026-10-22-transcript-task-entry-structure.md`）；Claude Code 升级改格式时先重跑该实测。

## 许可证

AGPL-3.0-or-later
