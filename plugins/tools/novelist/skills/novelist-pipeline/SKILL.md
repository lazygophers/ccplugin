---
name: novelist-pipeline
description: "批量写小说的流水线编排: 默认 mode=write 两流水线并行批量写(Writer 流 ‖ 检测定稿流, 每章 write→三环并行检测(check/humanize/proofread)→fix串行改→定稿)。加 mode 入参支持 review(评审)/humanize(去AI味)/proofread(校对)/polish(润色=三环收尾)/rewrite(重写)/outline(大纲)。载体: write 默认 Workflow(workflow.js), 其余默认 trellisx subagent 编排(main DAG 调度派 novelist 系列 skill, 并发上限2); --workflow/--no-workflow 覆盖。当用户说'批量写N章/写到第N章/连续写多章/逐章写/评审N章/校对N章/润色N章/去AI味N章/重写N章/出大纲'时调用。"

user-invocable: true
argument-hint: "[mode] [写到第N章 | 写N章] [--workflow | --no-workflow]（mode 缺省=write；startChapter 自动取进度下一章）"
arguments: target
disable-model-invocation: true
---

# novelist-pipeline — 多场景批量编排

默认 **mode=write**: 用 **Workflow 工具**批量写多章, **两流水线并行**(Writer 流逐章写, 检测定稿流逐章跑收尾链 + 评分门控, 两流并行)。加 **mode** 入参切换到其它场景(评审/校对/去AI味/润色/重写/大纲), 此时**默认走 trellisx subagent 编排**(main DAG 调度, 派 Agent 各执行 1 章)。

## 入参

```
/novelist-pipeline [mode] [写到第N章 | 写N章] [--workflow | --no-workflow]
```

- **mode**(可缺省, 缺省=`write`): `write` / `review` / `humanize` / `proofread` / `polish` / `rewrite` / `outline`
- **target**(`$target`, 复用原语义): 写到第几章(绝对终点, 含「到」) / 写几章(相对数量) / 缺省单章。`outline` 模式 target = 路线图到第N章。
- **--workflow**: 强制该 mode 走 Workflow(workflow.js), 即便非 write
- **--no-workflow**: 强制走 subagent 编排, 即便 write
- 中文别名: 评审=review, 去AI味/去AI化=humanize, 校对=proofread, 润色=polish, 重写=rewrite, 大纲/路线图=outline

### 载体选择规则(默认 + 覆盖)

| 条件 | 载体 |
|---|---|
| mode=write 且无 --no-workflow | **Workflow**(默认) |
| mode=write 且 --no-workflow | subagent 编排 |
| mode≠write 且 --workflow | Workflow |
| mode≠write 且(无 flag, 默认) | **subagent 编排**(默认) |

## mode 路由表

| mode | 级 | 前置(路线图/世界观/预检) | pipeline 行为(逐章) | 子 mode 默认 | 统一 check | 载体默认 |
|---|---|---|---|---|---|---|
| `write`(默认) | 章 | 全跑 | write→三环→fix→定稿 | — | ✓ | **Workflow** |
| `review` | 章 | 跳 | check(detect 只查一致, 不修) | detect | ✓ | subagent |
| `humanize` | 章 | 跳 | humanize(去AI味+改) | fix | ✗ | subagent |
| `proofread` | 章 | 跳 | proofread(校对+改) | fix | ✗ | subagent |
| `polish` | 章 | 跳 | 三环(check+humanize+proofread)→fix→定稿 | — | ✓ | subagent |
| `rewrite` | 章 | 跳 | rewrite(fix 模式A 报告修复; 入参可指 B/C) | fix(模式A) | ✓ | subagent |
| `outline` | 批 | 仅路线图(无世界观/预检) | outliner 生成路线图(无 write/收尾) | — | ✗ | subagent |

**排除**(非章节级, 不进 pipeline): character/worldview/craft/design/init/trending/lint — 一次性或被引用型, pipeline 调度无意义。

### 各 mode 报告/评分产出

| mode | 报告路径 | 评分 |
|---|---|---|
| write | 检查报告/校对报告/deaigc | 综合分(现有) |
| review | 元数据/检查报告/第N章.md + 统一-批.md | 一致性分 |
| humanize | 元数据/校对报告/第N章-deaigc.md | 人味分 |
| proofread | 元数据/校对报告/第N章.md | 文字分 |
| polish | 三报告全产 | 综合分 |
| rewrite | 重写后正文 + 元数据/检查报告/第N章.md | — |
| outline | 情节/第NNN-NNN章路线图.md | — |

## 入参 `$target`(二选一, 自然语言即可)

调用 `/novelist-pipeline <target>`, `$target` 即字符串:
- **写到第几章**(绝对终点): `写到第 40 章` / `到 40` → `endChapter = 40`
- **写几章**(相对数量): `写 5 章` / `5` → `count = 5`, 脚本算 `endChapter = startChapter + 5 − 1`
- **缺省**(空): 只写 1 章

`startChapter` **恒为进度下一章**, 不由入参决定。`$target` 含「到」字判为绝对终点, 否则判为数量。

## 激活时执行

1. **定位小说根目录** `root` — 当前工作目录即小说项目根(含 `章节/ 元数据/ 世界观/ 情节/` 等)。不确定 → `AskUserQuestion` 让用户确认路径。无目录环境 → 硬停, 提示先 `novelist-init`。
2. **读 `元数据/进度.md`** 确定下一章号 = `startChapter`。
3. **解析入参** — 拆出 `mode`(首个 token 若在 7 mode 内则为 mode, 否则缺省 write)、`--workflow`/`--no-workflow` flag、剩余即 `$target`(含「到」→ `endChapter`; 否则 → `count`; 空 → 单章)。中文别名先归一为英文 mode。
4. **选载体**(按上面「载体选择规则」表): 默认 write→Workflow, 其它→subagent; `--workflow`/`--no-workflow` 覆盖。
5. **(载体=Workflow)** 调 Workflow(脚本内含 mode 分支, 按 mode 跑对应 phase 子集, write 全流程):
   ```
   Workflow({
     scriptPath: "${CLAUDE_PLUGIN_ROOT}/skills/novelist-pipeline/workflow.js",
     args: { root, mode, startChapter, endChapter }   // mode 缺省 write; 或 { root, mode, startChapter, count }
   })
   ```
   > `root` **必传**(脚本不硬编码任何小说路径/设定); >5 章脚本内部自动分批。
6. **(载体=subagent 编排)** 见下面「subagent 编排路径」: main 按 mode 解析章节范围 → DAG 派 general-purpose Agent 各跑 1 章。
7. **等待完成通知** → 汇总输出: 每章明细 + 整体评分 + 预估耗时(Workflow 模式; subagent 模式按各 Agent 回传)。
8. **对需复审章节**单独 `novelist-rewrite` 修复重跑。

## subagent 编排路径(mode≠write 且 --no-workflow, 或非 write 默认)

main 作为编排者:

1. **解析 mode + target** → 算章节范围 `[startChapter, endChapter]`(复用 `$target` 逻辑)。
2. **DAG 调度**(并发上限 **2**, 引用 trellisx scheduling 语义): 各章写文件不相交 → 全可并行, 受并发上限约束。
   ```
   for 章 in DAG_order(并发上限 2):
     dispatch general-purpose Agent:
       prompt(6 字段自包含):
         - 目标: 对第 N 章执行 mode=<mode>, 调用 novelist-<skill> skill
         - 已知: 小说根 root, 章节文件路径, Active task 路径
         - 工作目录与范围: 仅该章文件
         - 输出格式: 报告/评分落 元数据/ 对应路径
         - 验收: 该章 mode 完成 + 报告产出
         - 失败处理: 标「需要:」回传 main 转达
   ```
   - mode→skill 映射: review→novelist-check(detect), humanize→novelist-humanize(fix), proofread→novelist-proofread(fix), polish→依次 check/humanize/proofread 三环(+fix+定稿), rewrite→novelist-rewrite(fix 模式A), outline→novelist-outline(批级路线图)
3. **统一 check**(若 mode 需要: review/polish/rewrite): 末尾串行派 1 个 Agent 跑 novelist-check 全批, 报告落 `元数据/检查报告/统一-第NNN-NNN章.md`。
4. **失败处理**: Agent 缺信息标「需要:」 → main 转达用户; 章节范围解析失败 → AskUserQuestion。

> 无 Workflow runtime 时, 所有 mode(含 write --no-workflow)都走本路径, 行为一致。

## write 架构(mode=write 时适用)

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
                                                       │ 不足 → fix(串行改同文件) → 重走三环 (无限, 直到达标)
   ⇒ 第N章在检测/fix/定稿时, 第N+1章已在 write(两流并行)
                                  │
后置(每批一次)：  统一 check（一个 agent 一次性审本批全部章节 + 与全书设定/前文冲突, 非逐章）
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

**2-4 三环并行检测**(正交只读, 无写冲突); 5 Fixer 按三环清单**统一改**(多修复串行改同文件); fix 后重走三环并行检测, 循环**无限**(`MAX_FIX_ATTEMPTS=Infinity`, 直到达标)。**Writer 流不等本章定稿即开写下一章(两流并行)**; 检测定稿流内逐章顺序定稿。

### 后置(每批一次): 统一检查

**一个 `novelist:continuity-auditor` agent 一次性审本批全部章节**(非逐章独立)——把本批这次变更的章节作为整体, 读全批正文 + 全书设定/前文/伏笔台账/进度, 核对: ① 本批章节**之间**矛盾 ② 违反规则.md ③ 人物一致 ④ 伏笔跨章追踪 ⑤ 与**前文**衔接/时间线 ⑥ 新设定与历史冲突。报告整批一份 `元数据/检查报告/统一-第NNN-NNN章.md`。

> **agentType 前提**: workflow.js 每个 agent() 用 `agentType` 指向本插件 `agents/` 下的专用 agent(共 8 个)——**需 novelist 插件已安装**, Agent 注册表才能解析这些 agentType。未安装时 Workflow 报 agent 解析失败, 应先装插件。

**文风**: Writer 写前必引用 `novelist-craft` 按题材+本章性质取叙事镜片。
**事实源**: 人物/世界观变更引用 `novelist-character`/`novelist-worldview` 回写。
**硬约束**: 一律从该小说的 `世界观/规则.md` 读取, 脚本不写死任何小说的具体设定。

## 定稿标准

定稿分 = 一致性×0.5 + 文字×0.2 + 人味×0.3(保留 1 位小数)。

**综合 ==100 且 一致性 ==100 → 定稿; 否则退回最弱环修复重评。**(满分零容忍门控, 阈值是 `workflow.js` 顶部常量 `PASS_*=100`; 加权 ==100 ⟺ 一致性/文字/人味三项全 ==100。)

## 评分契约(对应 `workflow.js`)

| 分量 | 来源 | 提取规则 | 缺省 | fix 触发 → 修复环 |
|---|---|---|---|---|
| 一致性 cScore | Checker 输出(18 子项) | 含「冲突」→80; 否则→100 | 100 | 含「冲突」 → fix-c |
| 文字 tScore | Proofer 输出(12 子项) | 首个 `(\d+)\s*分` | 90 | 含「逻辑矛盾/硬伤」 → fix-t |
| 人味 hScore | Humanizer 输出 | 首个 `(\d+)\s*分` | 90 | AI味「中/重」 → fix-h |

**角色输出硬格式**(不合则提取失败→落缺省→误判): Checker 结论行含「通过/有冲突」; Proofer 输出 `评分：N分`; Humanizer 输出 `人味评分：N分`+「轻/中/重」。

## 失败分支(触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 综合分 <100(分项未满分) | 退回最弱环修复重跑 | **无限重试**(`MAX_FIX_ATTEMPTS=Infinity`)直到达标==100——一直 fix 不停; 持久达不到满分需人工 kill |
| 一致性有冲突 | `novelist-check` 定位 → `novelist-rewrite` 修 | 冲突来自设定 → 先改设定再改正文 |
| 路线图生成/解析失败(schema 返回 chapters 为空) | **无限重试**直到拿到 chapters | (不跳批, 一直重试) |
| 多 workflow 冲突 | 立即停掉旧 workflow | 无法停 → 等结束后手动修索引 |
| 索引/进度被污染 | 对照章节目录重建 | 无法重建 → 回报用户 |
| agent 调用失败(网络/余额/瞬时 API) | `callAgent` **无限重试**(`MAX_AGENT_RETRIES=Infinity`)直到成功 | (永不放弃, 一直重试) |
| 无 Workflow 工具(非 Claude Code) / --no-workflow | 退化为 subagent 编排: main 派 Agent 逐章跑对应 mode(同样走每章收尾链) | 同样走每章收尾链 |

## 检查点

- **路线图确认**: 生成后暂停, 确认再写正文
- **未满分章节**: 综合分 <100(非满分)的章节必须人工审后再标定稿
- **每批结束**: 展示本批成绩摘要, 确认后再启动下一批

## 并行/串行约束(硬性)

- **两流水线并行**: Writer 流 ‖ 检测定稿流。第 N 章 write 完(草稿)即推入检测流, 第 N+1 章**立即开写**(基于第 N 章草稿)。两流并行换 throughput。
- **各流内部串行**: Writer 流逐章串行(write 读前章); 检测定稿流逐章串行(finalize 共享索引/进度, 防写冲突)。
- **收尾链检测/修改分离**: check/humanize/proofread 三环**只检测不改正文**(正交→**并行**, 无写冲突); 问题由 **fix 统一改**, 多 fix **串行**(都改同一章文件)。fix 后重走三环并行检测(无限, 直到达标)。
- 后置统一 check = **单 agent 一次性审整批**(读全批正文+全书设定/前文, 非逐章并行)。
- 禁止多个 pipeline 同时运行。
- 每批最多 5 章(`BATCH_SIZE=5`; 超过自动分批; 批间串行, 批内两流并行)。
- **全程无限重试(用户强制)**: fix 循环 / agent 调用 / 路线图生成三处均**无上限**(`Infinity`/`while(true)`), 一直重试到成功/达标。⚠️ 持久错误(余额耗尽/永久达不到阈值)会**死循环**, 需人工 kill workflow——这是用户明确要求的强制行为, 不设兜底。
- ⚠️ **草稿依赖风险**: 第 N+1 章基于第 N 章草稿写; 若第 N 章检测出致命冲突需重写 → 第 N+1 章可能要返工。这是 throughput 与一致性的权衡(已选 throughput)。

## 反例黑名单

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
| 统一检查报告 | `元数据/检查报告/统一-第NNN-NNN章.md`(整批一份, 一次性审本批+历史冲突) |
| 校对报告 | `元数据/校对报告/第NNN章.md`(proofer 每章写) |
| 去AI味报告 | `元数据/校对报告/第NNN章-deaigc.md`(humanizer 每章写) |
| workflow 脚本 | `${CLAUDE_PLUGIN_ROOT}/skills/novelist-pipeline/workflow.js` |

> 与 `novelist-write`(单章一站式)互补: write 是逐章入口, pipeline 是多章流水线批量。两者都走每章收尾链 + 评分门控, 共用 novelist 系列 skill/agent。
