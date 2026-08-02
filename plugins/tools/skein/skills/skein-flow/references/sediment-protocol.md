# sediment + amend 异步判定门

skein-flow finish 阶段 流程第 3 步的 sediment + amend 双动作细节。**finish 闭环 (销 worktree + 标记完成) 后**的异步 fire-and-forget, **不阻塞 finish**。本节是 finisher/main 之外的第三载体 `skein-specer` 的活, 完全复用 `skein-spec` skill, **禁新造沉淀机制**。

## 触发与机制 (fire-and-forget)

finish 闭环后, main **异步**派 `skein-specer` 跑 sediment + amend 双动作:

- **触发时机** — 第 3 步 `skein finish` 闭环 (销 worktree + 标记完成) **之后**, 非阻塞。main 派 skein-specer 后**不等回传即结束回合**, finish 已闭环。
- **fire-and-forget** — skein-specer 的回传到达后, main **只补 output trace** (finish 已闭环, sediment/amend 判定不输出 trace 即流程错误)。判定结果不影响 finish 的闭环性。
- **禁阻塞 finish** — 禁为等 skein-specer 回传延后 `skein finish`; finish 先闭环, 双动作异步在后。

## 动作一: sediment (规则/决策沉淀)

skein-specer 读 diff + 各 subagent 回传摘要 (含 `SPEC:` 标记), **自主**判定是否沉淀:

- 跑 `skein-spec sediment` 判定门 (判定 → 定 ns×inclusion → 自动写盘), 命中即写, **不逐次询问用户**。
- **自主写盘** — 判定通过后 skein-specer 自主 `skein-spec sediment` 写盘 + reindex, 无需 main 介入。
- **无增量 → 自判跳过 (禁硬凑)** — 若本次 task 无可沉淀增量 (一次性 bug / 私有细节 / 已有规则覆盖), skein-specer 自判 drop 跳过, 禁硬凑成沉淀契约。
- 详见 `skein-spec` skill。

## 动作二: amend (product wiki 回写候选, 三路降级)

skein-specer 跑 `skein-spec finish-candidates <tid>` 为 product namespace 产回写候选, **三路降级**:

1. **diff 改动文件反查 anchors** — 命中既有 product 页的 anchors → 该页即候选。
2. **皆无命中 → prd 关键词弱候选** — 用 `skein-spec recall --src product` 以 prd 关键词找弱候选。
3. **仍无 → 报「无候选, 可能是新功能域, 建议新建」, 禁硬凑** — 不强行摊派到不相关的既有页。

按候选结果落盘 (与 sediment 同批异步, 不额外等回传):
- 有候选 (①/②命中) → 用 `amend` 改写既有页。
- 无候选 (③) → 视需要用 `sediment --namespace product` 新建页, 或按建议留给用户后续手动新建, **禁凑数据硬造现状页**。

权威定义见 [skein-spec SKILL.md](../../skein-spec/SKILL.md) 「product wiki」章节 (`finish-candidates` 三路降级原文) 与 [sediment-workflow.md](../../skein-spec/references/sediment-workflow.md) §5 amend vs sediment 抉择树, 本文件不重复语法细节。

## proposed → active/superseded 转态 (sediment 沉淀 plan 期未验证决策时用)

`skein-spec sediment --status` 支持 `active`(默认) / `proposed` / `deprecated` / `superseded` 四值。**plan 阶段沉淀的决策 (grill/design 推出但本轮 check 未验证过) 落 `status: proposed`**, 供 `skein-spec analyze` 的「proposed 置信度」检查识别未验证引用; 常规已验证决策仍走默认 `active`。

- **proposed → active** — 该决策后续被某 task 的 check/analyze 实际验证成立 (不再是未验证假设) 后应转正。**CLI 限制**: `sediment` 写盘逻辑对同主题文件重复追加时, 传 `--status active` (等于默认值) 不会覆盖已有的非 active 状态 (`write.py` 只在显式传非 `active` 值时才覆盖, 防止常规追加意外抹掉 deprecated/superseded 标记)。故 proposed→active **无法**靠再跑一次默认 `sediment` 达成 —— 需直接 Edit 该主题文件 frontmatter 的 `status:` 行改 `active`, 改后跑 `skein-spec reindex` 同步索引。spec 规则文件不在 PreToolUse 硬阻名单 (只挡 task.json/task.md), 直接 Edit 允许。
- **proposed → superseded** — 决策被新方案取代 (不再成立) 时, 跑 `skein-spec sediment --namespace <ns> --category <cat> --topic <同 topic> --status superseded --title <T> --body-file <正文>` 显式传非 active 值, 正常覆盖写盘 + 自动 reindex, **无需**手改 frontmatter。
- 转态后原章节正文如需同步改写 (而非仅换状态), 走 `amend`; 仅换状态字段用上述两条即可。
