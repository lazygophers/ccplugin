---
name: novelist-pipeline
description: "两流水线并行批量写小说: Writer 流 ‖ 检测定稿流(第N章 write 完进检测时第N+1章已开写); 每章 write→三环并行检测(check/humanize/proofread)→fix串行改→定稿。前置 outline→worldview→precheck, 后置统一 check。用 Workflow 工具调度, 调用 novelist 系列 skill/agent 完成每章闭环。当用户说'批量写N章/写到第N章/连续写多章/逐章写'时调用。入参二选一: 写到第几章(endChapter)或写几章(count); startChapter 恒为进度下一章, 缺省单章。"
when_to_use: 需要一次性批量编写多个章节(连续写 N 章 / 写到第 N 章)并自动跑完整收尾链时。触发词: 批量写, 流水线, 连续写, 写到第, 写N章, pipeline, 批量章节。
user-invocable: true
argument-hint: "[写到第N章 | 写N章]（缺省=单章；startChapter 自动取进度下一章）"
arguments: target
disable-model-invocation: true
---

# novelist-pipeline — 两流水线并行批量写作

用 **Workflow 工具**批量写多章, **两流水线并行**: Writer 流逐章写(写完即推检测), 检测定稿流逐章跑收尾链 + 评分门控, 两流并行(第N章检测时第N+1章已在写)。**依赖 Claude Code 的 Workflow 编排能力**(无 Workflow 的 runtime 退化为 `novelist-write` 逐章手动循环, 行为一致)。

## 入参 `$target`(二选一, 自然语言即可)

调用 `/novelist-pipeline <target>`, `$target` 即字符串:
- **写到第几章**(绝对终点): `写到第 40 章` / `到 40` → `endChapter = 40`
- **写几章**(相对数量): `写 5 章` / `5` → `count = 5`, 脚本算 `endChapter = startChapter + 5 − 1`
- **缺省**(空): 只写 1 章

`startChapter` **恒为进度下一章**, 不由入参决定。`$target` 含「到」字判为绝对终点, 否则判为数量。

## 激活时执行

1. **定位小说根目录** `root` — 当前工作目录即小说项目根(含 `章节/ 元数据/ 世界观/ 情节/` 等)。不确定 → `AskUserQuestion` 让用户确认路径。无目录环境 → 🔴 STOP, 提示先 `novelist-init`。
2. **读 `元数据/进度.md`** 确定下一章号 = `startChapter`。
3. **解析 `$target`** — 含「到」→ `endChapter`; 否则 → `count`; 空 → 单章。
4. **调 Workflow**(脚本内含前置 outline→worldview→precheck, 无需手动分调):
   ```
   Workflow({
     scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/novelist-pipeline/workflow.js",
     args: { root: "<小说根目录绝对路径>", startChapter, endChapter }   // 或 { root, startChapter, count }
   })
   ```
   > `root` **必传**(脚本不硬编码任何小说路径/设定); >5 章脚本内部自动分批。
5. **等待完成通知** → 检查结果: 哪些章定稿、哪些需复审。
6. **对需复审章节**单独 `novelist-rewrite` 修复重跑。

## 架构

**两流水线并行**: Writer 流 ‖ 检测定稿流。第 N 章 write 完(草稿)即进检测链, **同时**第 N+1 章开始 write。用 throughput 换"基于前章草稿写下一章"的小风险(前章若检测出致命冲突重写, 下一章可能返工——已接受)。

```
前置(每批一次，串行)：  outline(路线图) → worldview(更新设定) → precheck(一致性预检)
                                  │
两流水线并行(批内)：
   Writer 流(逐章串行写, 读前章草稿):  写1 → 写2 → 写3 → ...
                                        │(写完即推, 不等收尾)
   检测定稿流(逐章串行, 共享索引):      └→ 第N章: ┌─ check    ┐
                                                  ├─ humanize ┤ 三环并行检测(只读不改) → 评分
                                                  └─ proofread┘
                                                       │ 达标 → finalize(定稿+索引)
                                                       │ 不足 → fix(串行改同文件) → 重走三环 (≤10次)
   ⇒ 第N章在检测/fix/定稿时, 第N+1章已在 write(两流并行)
                                  │
后置(每批一次)：  统一一致性 check（全批章节并行，只读）
```

> **两级串行 + 一级并行**: ① Writer 流内部逐章串行(write 读前章) ② 检测定稿流内部逐章串行(共享索引/进度) ③ 两流之间并行(write 与检测重叠)。三环检测在检测流内再并行。

## 角色职责(关联 novelist skill/agent, 全部从小说自己的文件读设定)

### 前置(串行, 每批一次)

| 角色 | agentType | 引用 skill | 职责 | 产出 |
|---|---|---|---|---|
| Outliner | `novelist:outliner` | novelist-outline | 读大纲/分卷/主线/伏笔 生成本批路线图 | `情节/第NNN-NNN章路线图.md` |
| Worldview | `novelist:worldbuilder` | novelist-worldview/character | 更新本批涉及的世界观/人物设定 | `世界观/` `人物/` 对应文件 |
| Pre-checker | `novelist:continuity-auditor`(预检模式) | novelist-check | 路线图一致性预检(与主线/伏笔对齐, 可改路线图) | 通过 / 修正路线图 |

### 每章闭环(检测定稿流内, 顺序硬性)

| 序 | 角色 | agentType | 只做 | 不做 |
|---|---|---|---|---|
| 1 | Writer | `novelist:chapter-writer` | 按四要素 + `novelist-craft` 镜片写正文 | 不管校对/一致性 |
| 2 | Checker(检测) | `novelist:continuity-auditor` | 查一致性, **只检测返回清单不改正文** | 不管文字/风格 |
| 3 | Humanizer(检测) | `novelist:humanizer` | 检 AI 味(匀质/陈词/模板腔)+人味分, **只检测不改** | 不管一致性/错别字 |
| 4 | Proofer(检测) | `novelist:proofreader` | 检错别字/语法/标点+质量分, **只检测不改** | 不管一致性/AI味 |
| 5 | Fixer | 对应环 agent | 按三环清单**统一改**正文(多 fix 串行) | 不改风格/不重写 |
| 6 | Finalizer | `novelist:indexer` | 更新索引 + 同步事实源 → 才进下一章 | 不修复/不重写 |

🔴 **2-4 三环并行检测**(正交只读, 无写冲突); 5 Fixer 按三环清单**统一改**(多修复串行改同文件); fix 后重走三环并行检测, 循环 ≤10 次(`MAX_FIX_ATTEMPTS`)。**Writer 流不等本章定稿即开写下一章(两流并行)**; 检测定稿流内逐章顺序定稿。后置统一检查用 `novelist:continuity-auditor`(只读)。

> 🔴 **agentType 前提**: workflow.js 每个 agent() 用 `agentType` 指向本插件 `agents/` 下的专用 agent(共 8 个)——**需 novelist 插件已安装**, Agent 注册表才能解析这些 agentType。未安装时 Workflow 报 agent 解析失败, 应先装插件。

**文风**: Writer 写前必引用 `novelist-craft` 按题材+本章性质取叙事镜片。
**事实源**: 人物/世界观变更引用 `novelist-character`/`novelist-worldview` 回写。
**硬约束**: 一律从该小说的 `世界观/规则.md` 读取, 脚本不写死任何小说的具体设定。

## 🔴 定稿标准

定稿分 = 一致性×0.5 + 文字×0.2 + 人味×0.3(保留 1 位小数)。

**综合 ≥85 且 一致性 ≥85 → 定稿; 否则退回最弱环修复重评。**(阈值是 `workflow.js` 顶部常量, 可按需调严。)

## 🔴 评分契约(对应 `workflow.js`)

| 分量 | 来源 | 提取规则 | 缺省 | fix 触发 → 修复环 |
|---|---|---|---|---|
| 一致性 cScore | Checker 输出 | 含「冲突」→80; 否则→95 | 95 | 含「冲突」 → fix-c |
| 文字 tScore | Proofer 输出 | 首个 `(\d+)\s*分` | 90 | 含「逻辑矛盾/硬伤」 → fix-t |
| 人味 hScore | Humanizer 输出 | 首个 `(\d+)\s*分` | 90 | AI味「中/重」 → fix-h |

**角色输出硬格式**(不合则提取失败→落缺省→误判): Checker 结论行含「通过/有冲突」; Proofer 输出 `评分：N分`; Humanizer 输出 `人味评分：N分`+「轻/中/重」。

## 🔴 失败分支(触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 综合分 <85(分项不足) | 退回最弱环修复重跑 | 连续 10 次不过 → 标「需复审」回报; 仍低 → 人工 |
| 一致性有冲突 | `novelist-check` 定位 → `novelist-rewrite` 修 | 冲突来自设定 → 先改设定再改正文 |
| 路线图生成/解析失败(schema 返回 chapters 为空) | 重试 1 次 | 仍失败 → ❌ 明确报错跳过本批(非静默), 回报用户 |
| 多 workflow 冲突 | 立即停掉旧 workflow | 无法停 → 等结束后手动修索引 |
| 索引/进度被污染 | 对照章节目录重建 | 无法重建 → 回报用户 |
| agent 返回 null/异常 | 重试该 agent | 仍异常 → 标该章需人工 |
| 无 Workflow 工具(非 Claude Code) | 退化: 用 `novelist-write` 逐章手动循环 | 同样走每章收尾链 |

## 🔴 检查点

- **路线图确认**: 生成后暂停, 确认再写正文
- **低分章节**: 综合分 <85 的章节必须人工审后再标定稿
- **每批结束**: 展示本批成绩摘要, 确认后再启动下一批

## 并行/串行约束(硬性)

- 🔴 **两流水线并行**: Writer 流 ‖ 检测定稿流。第 N 章 write 完(草稿)即推入检测流, 第 N+1 章**立即开写**(基于第 N 章草稿)。两流并行换 throughput。
- 🔴 **各流内部串行**: Writer 流逐章串行(write 读前章); 检测定稿流逐章串行(finalize 共享索引/进度, 防写冲突)。
- 🔴 **收尾链检测/修改分离**: check/humanize/proofread 三环**只检测不改正文**(正交→**并行**, 无写冲突); 问题由 **fix 统一改**, 多 fix **串行**(都改同一章文件)。fix 后重走三环并行检测(≤10 次)。
- 仅后置统一 check 全批并行(只读)。
- 禁止多个 pipeline 同时运行。
- 每批最多 5 章(`BATCH_SIZE=5`; 超过自动分批; 批间串行, 批内两流并行)。
- ⚠️ **草稿依赖风险**: 第 N+1 章基于第 N 章草稿写; 若第 N 章检测出致命冲突需重写 → 第 N+1 章可能要返工。这是 throughput 与一致性的权衡(已选 throughput)。

## ⛔ 反例黑名单

| # | 禁做 | 改为 |
|---|---|---|
| 1 | 跳过收尾链标「定稿」 | 三环全过才定稿 |
| 2 | 无路线图直接批量写 | 先产路线图再写 |
| 3 | 多 workflow 同时改索引 | 索引更新串行 |
| 4 | 不更新事实源就下一章 | 定稿后同步索引+进度+人物/情节 |
| 5 | **硬编码某本小说的路径/设定** | `root` 入参传; 设定一律读该小说 `世界观/规则.md` 等 |
| 6 | agent 异常低分不审直接标定稿 | 异常分数必须人工复核 |
| 7 | 让用户自己分别调 write/check/humanize | 本 skill 一站式编排, 用户只调 pipeline |
| 8 | 检测定稿流并发改同一章 / finalize 并发改索引 | 检测定稿流逐章串行(共享索引/进度); 仅三环检测内部并行(只读) |

## 文件约定

| 内容 | 路径(相对小说根 `root`) |
|---|---|
| 正文 | `章节/第NNN章-标题.md`(三位零填充) |
| 章节索引 | `章节/_索引.md` |
| 进度 | `元数据/进度.md` |
| 路线图 | `情节/第NNN-NNN章路线图.md` |
| 世界观硬约束 | `世界观/规则.md` |
| 伏笔台账 | `情节/伏笔.md` |
| 一致性检查报告 | `元数据/检查报告/第NNN章.md`(checker 每章写) |
| 统一检查报告 | `元数据/检查报告/统一-第NNN章.md`(unified 写) |
| 校对报告 | `元数据/校对报告/第NNN章.md`(proofer 每章写) |
| 去AI味报告 | `元数据/校对报告/第NNN章-deaigc.md`(humanizer 每章写) |
| workflow 脚本 | `${CLAUDE_PLUGIN_ROOT}/skills/novelist-pipeline/workflow.js` |

> 与 `novelist-write`(单章一站式)互补: write 是逐章入口, pipeline 是多章流水线批量。两者都走每章收尾链 + 评分门控, 共用 novelist 系列 skill/agent。
