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

## 8. d4 执行留痕 (9 agent + plugin.json)

**本轮为第六棒接续** (前五棒全因 API 断连零 commit)。起点 HEAD `4aa218b33`, 承接前任半成品 `skein-specer.md` 未提交改动 (可用, 接着改完), 逐文件独立 commit。

### 8.1 改动清单 (9 agent 各改了什么)

| agent | 改动 |
|---|---|
| `skein-specer.md` | 前任半成品(amend 章节)基础上补 amend/reconstruct·maintain/prune/auto-fix 五类写路径, JSON 输出加 `amended[]`, 四类→五类措辞 |
| `skein-recaller.md` | 加 `--src` 分源参数, `inclusion:auto` 扩至全 namespace 召回, 回传按 `rules`/`product` 分组 |
| `skein-finisher.md` | 加「查 product wiki 候选」步骤 (调 `skein-spec finish-candidates <tid>`, 三路降级), 回传加 `spec_candidates` 字段 |
| `skein-checker.md` | 「一致性核查」步骤改调 `skein-spec analyze <id> --json` (五类只读候选检查), 不再手工枚举冲突对; JSON 输出 `consistency.conflicts`→`consistency.analyze_candidates` |
| `skein-dedup.md` | 查重判据段加一句可选 `skein-spec recall --src product` 辅助信号 (主体判据/归并/DAG 逻辑不动) |
| `skein-researcher.md` | bootstrap 模式五维扫描加「第六项 product overview」(README/docs 提炼产品定位, 产 product namespace 候选, 无源留空不硬猜) |
| `skein-setup.md` | 术语 core/recall → namespace(`rules`/`product`/`map`/`external`)×inclusion; 加「旧结构识别」段 (检出 `spec/core/` 走 migration-v2 两阶段流程, 非本流程手工分层, 回传单独标出供 main AskUserQuestion); JSON `spec` 字段改四 namespace 计数 + 加 `legacy_structure` |
| `skein-clean.md` | 加硬门「不碰 spec 迁移快照」(`.skein/spec/.archive/<ts>/` 是可回滚快照, 不属清理范围) |
| `skein-executor.md` | `spec.py recall`/`spec.py sediment` 旧脚本路径措辞改 `skein-spec` CLI 命名, 与其余 agent 一致 |

### 8.2 三批来源不明改动的裁决

| 来源 | 内容 | 裁决 | 理由 |
|---|---|---|---|
| commit `1c58cdfd6` | `agents/*.md` frontmatter 加 `hooks: SubagentStart/Stop` | **不采纳** | 与 d4 验收硬规「git diff 确认 hooks 键未出现在 diff 中」直接冲突; 本轮 9 个 agent 改动的 diff 已核实无 `hooks:` frontmatter 键 (仅有 `hooks.py` 脚本调用与「钩子」中文措辞, 非同一物) |
| commit `39b51fd7c` | `agents/*.md` 删 `skills: skein:skein-flow` frontmatter + 清代码围栏空行 | **不采纳** | 出自同一批质量不可信来源 (main 已实测发现其把 skein-flow/SKILL.md 正文截断丢内容); 本轮 9 个 agent 现有 frontmatter 本就无 `skills:` 键需删, 该批改动与 d4 范围无关, 不引入 |
| `stash@{1}` | `plugin.json` desc 6→9 agent / agents 数组加 recaller / commands 数组加 dedup / serve 命令改 `bin/skein` | **部分参考, 未采纳原文, 自行在 worktree 重新实现** | desc/agents 数组/commands 数组三处诉求合理, 已自行核对现状 (agents 数组确实缺 `skein-recaller.md`, commands 数组确实缺已存在的 `commands/skein-dedup.md`) 后重写, 未 cherry-pick; **serve 命令改 `bin/skein` 不采纳** — 不在 d4 范围 (措辞/agent 数组, 非 monitor 命令), 且改跑脚本入口越界 |

### 8.3 质量门

`claude -p --bare` 端点本 session 持续 `ConnectionRefused` (d1/d2/d3/s7 均撞到), main 已裁定并入 d5 重跑, 本轮**未验证**, 照实上报。待验清单 = 8.1 表全部 9 个 agent 文件 + `plugin.json`。

### 8.4 pytest

worktree 内跑 `python3 -m pytest plugins/tools/skein/scripts/tests -q` → **407 passed**(与本 worktree 正确基线一致; 过程中 `test_docs_commands.py` 一度因措辞 `` `skein-spec migrate` `` 被误判为不存在的 CLI 子命令报 2 条失败, 已改措辞为「migration-v2 两阶段流程」修复, 复跑转绿)。
