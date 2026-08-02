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

## 8. d1 执行留痕 (2026-08-02)

`skein-spec/SKILL.md` 重写已完成并提交 (worktree commit `670d7ae9f`), 6 条验收 grep 自证全过。两个待 main 裁定的问题:

1. **质量门 (`claude -p --bare`) 系统性打不通, 非内容问题** — 3 次调用 (2 次对本文件 + 1 次纯净健全性检查 `echo hi | claude -p "say ok"`) 全部 `API Error: Unable to connect to API (ConnectionRefused)`, `apiKeySource:"none"`, 10 次内部 retry 全失败, 耗时约 3 分钟/次。与文件内容无关 (纯净 prompt 同样失败), 判断是本 worktree/session 缺 API key 路由的环境问题, 非「跑题/空返回」式端点抖动, 重跑不会自愈。**d1 本身内容已按 CLAUDE.md 规范尝试质量门, 未能跑通; 请 main 决定是换有 API 访问的环境代跑, 还是本 subtask 的质量门验证并入 d5 统一处理。**
2. **发现一个不在本 task 范围内的测试 bug (脚本代码, 按边界禁止顺手改)** — `plugins/tools/skein/scripts/tests/test_docs_commands.py::test_all_doc_command_examples_are_valid` 现 406 passed / 1 failed (基线 407/0)。根因: 该测试的 `_top_subs()` 用正则 `^    ([a-z][a-z0-9\-_]*)\s{2,}` 解析 `--help` 输出, 但 `finish-candidates` 这个子命令名太长, argparse 把说明文字换到下一行, 该行末尾没有 `\s{2,}`, 正则永远抓不到它, 导致 CLI 里明明已注册的 `finish-candidates` 被判「不是 CLI 子命令」。这是**已存在的潜伏 bug** (`cli.py:81` 早就注册了这个子命令), 本 task 之前没有任何文档写过 `finish-candidates` 这个词, 从未触发过; d1 新增的 product wiki 章节第一次在文档里提到它, 才把这条潜伏 bug 揪出来。**本 task 边界明确「纯文档/提示词, 脚本缺能力报告不顺手改」, 故未动 test 文件, 报告给 main 裁定** (建议另开一个小 task 修 `_top_subs()` 正则, 兼容子命令名过长换行的 `--help` 输出格式)。

## 🔴 main 裁定: d1 的 claude -p 质量门并入 d5 (2026-08-02)

**事实**: exec-d1b 按 CLAUDE.md 规范跑质量门 3 次 (2 次对 SKILL.md 同 prompt + 1 次纯净健全性检查
`echo hi | claude -p --bare "say ok"`), 全部 `API Error: Unable to connect to API (ConnectionRefused)`,
stream-json 显示 `apiKeySource:"none"`, 内部 10 次 retry (backoff 到 32s) 全失败。纯净 prompt 同样失败,
排除内容问题。

**main 独立复现**: 用 `skein-setup/SKILL.md` 跑同样命令, 同样 ConnectionRefused。同一时段
`concurrency-pools` 的 exec-s7 亦报 6 次跨 25 分钟的同样错误。**环境级故障, 非单次抖动**
(抖动重跑会自愈, 这个不会)。

**裁定**: d1 的质量门验证并入 **d5**(质量门 + 结构性验证, 依赖 d1-d4), 届时环境可能已恢复。
d1 内容验收 6 条已自证通过 (grep 证据齐全), 不因端点故障扣留。

**d5 的收口义务**: 补跑 `skills/skein-spec/SKILL.md` 的质量门, 连跑 3 次确认主流程描述一致。
**若端点仍未恢复, 照实标注「因端点故障未验证」, 禁用源码核对冒充质量门通过。**

## 🟢 main inline 修: test_docs_commands.py 的潜伏正则 bug (2026-08-02)

d1 新增 product wiki 章节时第一次在文档里写 `finish-candidates`, 揪出一条潜伏已久的 bug。

**根因**: `tests/test_docs_commands.py::_top_subs()` 用 `^    ([a-z][a-z0-9\-_]*)\s{2,}` 解析
`--help` 输出抓子命令名。子命令名过长时 argparse 把 help 文字挤到下一行, 该行只剩子命令名、
行尾无空格, 正则永远抓不到。实测 `spec.py --help` 输出:

```
'    finish-candidates'
'                     [finish 用] 为 task 生成候选 product wiki 页 (三路降级:'
```

`spec/cli.py:81` 早已注册该命令, 但此前无任何 .md 文档提过这个词, 故从未触发。

**处置**: main inline 修 (commit `d5ad71162`), 正则补 `$` 分支 →
`^    ([a-z][a-z0-9\-_]*)(?:\s{2,}|$)`。修前 `test_docs_commands` 1 failed, 修后 3 passed。

**为什么 main 直接修而不派 subtask**: 单文件单处正则、位置已由 main 独立验证 (跑 `--help` 看到
实际输出), 符合作用域边界的 inline 豁免条件。当前 API 环境每次派发都有可观断线概率
(本 session 已 8 个 agent 死于连接中断), 为一行正则另开 task 不划算。

**exec-d1b 的处理是对的**: 它守住「纯文档/提示词, 脚本缺能力报告不顺手改」的边界, 报告而非自行动手。
这条 bug 的成因需跨文件判断 (cli.py 注册了 vs 测试正则抓不到), 不是执行者边界内该拍板的。
