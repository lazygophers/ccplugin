# graphify/gitnexus hook 注入按适用面过滤：非代码正文直读；多 commit 流程末尾统一重建索引

graphify 的 PreToolUse hook 在 `graphify-out/graph.json` 存在时，对每次 Read/grep
无条件注入「MANDATORY: 先跑 graphify query」。按内容分两类处理：

- **图谱里没有的内容**：`docs/`、`.scratch/`、README 等 markdown 正文基本不在图
  里。读这些、或已从早前读取拿到精确 file:line 时，直接读，注入当提示不当禁令。
- **图谱里有的内容**：改代码、跨文件探索、查调用关系——这些照全局取证顺序先跑
  `graphify query` / gitnexus。

gitnexus 的 PostToolUse 在每条 commit 后注入「index is stale, run gitnexus
analyze」。每票一 commit 的 worktree 流程中途不重建索引，
每票验收靠真跑测试（见 `workflow/ticket-acceptance.md`）；全部票关完、合回
主干后一次性 `gitnexus analyze --index-only`。
