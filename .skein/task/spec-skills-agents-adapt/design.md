# skills + agents 全量适配 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 1. 为什么这个 task 排最后

提示词要写的是**已落地的能力**, 不是设想。前 6 个 task 完成前写提示词, 会写出与最终实现不符的描述 —— 而提示词的错比代码的错更难发现 (没有测试会失败, 只是 agent 行为悄悄偏了)。

## 2. 改动分组 (按「改什么性质」而非按目录)

| 组 | 文件 | 性质 |
|---|---|---|
| **A. 模型描述重写** | `skein-spec/SKILL.md` | 结构性重写 (层表 → 正交两维表) |
| **B. 判据表同步** | `maintain.md` / `sediment-workflow.md` / SKILL.md 判据段 | 表格按 namespace 分行 |
| **C. 新增文件** | `prune-workflow.md` / `migration-v2.md` / `product.md.tmpl` / `map.md.tmpl` | 从零写 |
| **D. 重命名** | `core.md.tmpl`→`rules-always.md.tmpl` / `recall.md.tmpl`→`rules-auto.md.tmpl` | 机械 + 引用处跟改 |
| **E. 流程注入** | `for-plan` / `for-finish` / `for-check` / `sediment-protocol` | 在既有流程里插新步骤 |
| **F. 措辞更正** | 9 个 agent + `plugin.json` | 局部替换 (`--layer`→`--namespace`, `core 超 8000`→`always 超预算`) |

**F 组量最大但最机械**, A/C 组最需要判断力。

## 3. 两处「顺手修」的性质

| 项 | 性质 | 处置 |
|---|---|---|
| `SKILL.md:68` 引用 `references/prune-workflow.md` 但文件不存在 | **现存断链** | 补建该文件 (prune 流程本就该有独立文档) 而非删引用 |
| SKILL.md 通篇「两层」但实现三层 | **文档滞后于实现** | 本轮改成四 namespace 时一并修正 |
| SKILL.md / specer 写死 `core 超 8000` vs 代码默认曾 1000 | **两边漂移** | 措辞改为引用配置键名 `spec_always_budget`, **不再在文档里写死数字** —— 从根上消掉这类漂移 |

第三条是设计决策: **文档里禁写可配置项的具体数值**, 只写键名。写死数字必然与代码漂移。

## 4. 质量门执行方式 (CLAUDE.md 强约束)

```bash
cat <待测文件> | claude -p --bare "<问题>" --output-format stream-json 2>/dev/null \
  | jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

铁律 (违反即报错或误判):
1. 走 stdin 管道, **禁 `claude -p "$(cat ...)"` 插值** —— YAML frontmatter 的 `---` 会被当 CLI 选项, 报 `unknown option '---'`
2. `--bare` 必带 —— 否则 hook 注入劫持 prompt, 或非 Anthropic 路由模型报 400
3. `2>/dev/null` 必带 —— 否则 stderr 的 connector 警告混进 jq, 报 `Invalid numeric literal`
4. 问题问「该文件的触发场景与主流程」; 返回需非空且切题, **跑题或空返回属端点抖动, 重跑而非当结论**
5. predictability: 同一 prompt **连跑 3 次**, 主流程描述一致才算过
6. macOS 无 `timeout`, **禁包 `timeout`**

## 5. 关键取舍

| 取舍 | 决定 | 理由 |
|---|---|---|
| 文档写死预算数值 vs 写键名 | **写键名** | 写死数字必与代码漂移 (本轮的 1000/8000 矛盾就是这么来的) |
| `prune-workflow.md` 补建 vs 删引用 | **补建** | prune 是独立流程 (判据 + 自动 archive), 值得独立文档; 删引用会让 SKILL.md 的 prune 章节没有下钻处 |
| 模板重命名 vs 保留旧名 | **重命名** | `core.md.tmpl` 在新模型里没有对应概念了, 保留旧名会误导 |
| `skein-dedup` 改造幅度 | **只加一句可选增强** | 用户已定本轮 dedup 主体不动 |
| 一个 subtask 改全部 vs 分组拆 | **按 §2 分组拆 subtask** | 单个 subtask 改 20+ 文件, 失败后不知道改到哪一步; 分组后每组可独立验 |
| 质量门抖动处置 | **重跑, 不当结论** | CLAUDE.md 明确要求; 把抖动当失败会误改好文件 |

## 6. 测试接缝 (seam)

**本 task 无代码改动, 接缝 = 质量门本身。**

- 每个改动文件跑 `claude -p` 问「触发场景 + 主流程」, 返回切题即过
- predictability: 同 prompt 连跑 3 次比对主流程描述一致性
- 结构性验证 (纯脚本, 不靠 AI): 全仓 grep 确认无残留 `--layer` (除 deprecated alias 说明处) / 无残留「两层」措辞 / 无写死的 `8000` 数值 / 所有 `references/*.md` 引用的文件都存在 (无断链)
- `plugin.json` hooks 段零改动的验证: `git diff` 该文件确认 hooks 键未出现在 diff 里

## 7. 已知风险

| 风险 | 缓解 |
|---|---|
| 质量门端点抖动被当作文件质量问题 | 空返回/跑题一律重跑 (CLAUDE.md 第 4 条); 3 次一致才判过 |
| 20+ 文件改动漏改某处措辞 | 结构性 grep 验证兜底 (见 §6), 不靠人眼扫 |
| 提示词写了脚本没实现的能力 | 依赖前 6 task 完成; 发现缺能力**报告不顺手补脚本** (越界会让本 task 与前面 task 的改动交织, 冲突难解) |
| 模板重命名后 SKILL.md 引用未跟改 | 重命名与引用更新放同一 subtask, 且 grep 验证无旧名残留 |
| `plugin.json` description 过长被截断 | 现 description 已很长, 本轮**净减**冗余表述 (合并 core/recall 描述), 不净增 |
