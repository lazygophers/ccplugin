# watchtower

Claude Code mod pane 插件：常驻面板展示**当前 session 最近 50 条返回条目**——agent 返回值与主对话每轮的最终回复（Stop 时刻的 assistant 文本）按时间混排。

数据直接从当前 session 的 transcript（Claude Code 自动写的 `~/.claude/projects/<项目路径编码>/<session_id>.jsonl`）读出，滤出 Task/Agent 的 tool_use/tool_result 配对（含后台异步 agent 的 task-notification `<result>`）。**零自建存储**：不写 hook 落盘、不建数据目录、无清理逻辑；插件坏了只坏展示层，transcript 数据无损。

## 装了以后看到什么

Claude Code 界面多一块常驻面板 **Agent returns**：

- `session.start` 时自动打开，每 2 秒刷新一次（`clock.every` + `ui.render`）
- 每条默认收起：时间 + 调用标题（后台通知取 `<summary>`（如 `Agent "…" finished`），否则 Task/Agent 的 `tool_use` `input.description`，再无则回退正文第一个非空行）+ 正文预览（按面板宽度自适应行数：≥60 列两行、窄屏一行，超宽截断、超长词硬切不炸版；窄面板放不下 taskId，不渲染）
- 点击某条就地展开该条全文（按宽度换行），再点收起；同一时刻至多一条展开，2 秒刷新不丢展开态（该条滚出最近 10 条才自动收起）
- 条目头部区分来源：agent 条目 `▸ HH:MM <标题>`（后台通知取 `<summary>`，否则 `input.description`），主回复条目 `◆ HH:MM 主回复`（预览从正文首行起）；点击展开全文同上
- 最多 50 条（两类混池按 transcript 行序取最近），新的在前；面板可手动关闭，关闭后本 session 不再自动重开
- 终端太窄 dock 不下 pane 时（引擎策略：没人操作时 144 列起才摆放，人点过/命令触发过 110 列起），面板保持未绘制状态，不报错；此时 prompt 上方有一行 `Agent returns: … — 点此打开` band，点击即可打开面板，仍摆不下时弹 toast 说明原因

不做的事：不跨 session / 历史查询，不做返回值筛选、搜索、导出。

已知限制：session.start 事件不带 sessionId 时，取该项目目录下 mtime 最新的 transcript 兜底；同项目并发第二个 session 可能读到别的 session 的记录。transcript 超过 4 MiB（引擎单次读上限，见 `$.fs.read` 文档）时读不了，面板显示 `Cannot read transcript: …` 一行错误。

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
3. 面板应在返回后 2 秒内出现该返回值（时间、标题、正文预览）；点击该条展开全文，再点收起
4. 无头环境验证：跑一个 `claude -p` session 派 Task agent，然后对该 session 的 transcript 跑解析器，确认能读出刚产生的返回值：
   ```bash
   node -e 'import("./plugins/tools/watchtower/scripts/parse-transcript.mjs").then(m => console.log(m.recentReturns("<transcript.jsonl>", 50)))'
   ```

## 结构

```
.claude-plugin/plugin.json   # 插件清单
hooks/hooks.json             # 声明 hooks module
hooks/register.ts            # pane 生命周期：session.start 绑引擎开面板，clock.every 刷新，ui.close 关闭
hooks/views/pane.tsx         # 面板视图
scripts/parse-transcript.mjs # transcript 定位 + 返回条目解析（locateTranscript / recentReturns：agent 返回值 + 主回复）
```

transcript 内部格式无官方契约，字段结构靠实测（`.scratch/research/2026-10-22-transcript-task-entry-structure.md`）；Claude Code 升级改格式时先重跑该实测。

## 许可证

AGPL-3.0-or-later
