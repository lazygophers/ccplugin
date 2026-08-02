# sediment + amend 判定门

finish 后由 `skein-specer` 异步跑的两个动作，完全复用 `skein-spec` skill，**禁新造沉淀机制**。语法细节不在这里重复，见 [skein-spec SKILL.md](../../skein-spec/SKILL.md) 与 [sediment-workflow.md](../../skein-spec/references/sediment-workflow.md) §5（amend vs sediment 抉择树）。

## fire-and-forget

main 派完 skein-specer **不等回传即结束回合**，finish 已闭环。禁为等回传延后 `skein finish`。回传到达后 main 只补 output trace，判定结果不影响 finish 的闭环性。

## 动作一：sediment（规则/决策沉淀）

skein-specer 读 diff + 各 subagent 回传摘要（含 `SPEC:` 标记），跑 `skein-spec sediment` 判定门后**自主写盘 + reindex，不逐次问用户**。

无可沉淀增量（一次性 bug / 私有细节 / 已有规则覆盖）→ 自判 drop 跳过，**禁硬凑**。

plan 阶段沉淀的决策（grill/design 推出但本轮 check 未验证）落 `--status proposed`，供 `skein-spec analyze` 的置信度检查识别；常规已验证决策走默认 `active`。

## 动作二：amend（product wiki 回写候选）

跑 `skein-spec finish-candidates <tid>`，三路降级：

1. diff 改动文件反查 anchors 命中既有 product 页 → 该页即候选 → `amend` 改写。
2. 无命中 → `skein-spec recall --src product` 以 prd 关键词找弱候选。
3. 仍无 → 报「无候选，可能是新功能域，建议新建」，**禁摊派到不相关的既有页**，可按需 `sediment --namespace product` 新建。
