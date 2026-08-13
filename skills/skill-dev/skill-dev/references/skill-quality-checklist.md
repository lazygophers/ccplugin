# skill 质量根德 checklist

> 补 ask-matt `/writing-great-skills` 的核心方法论要点, 落 skill-dev 流程 A/B 通用参考。与 anti-patterns.md (22 反模式) / dimensions.md (9 维 rubric) / validation-checklist.md (发布前) 互补 — 本文件是「写 skill 的元纪律」, 那几份是「具体红线 / 打分 / 发布门」。

## predictability 是根德

skill 的首要价值是 **predictability** (可预测) — 同样输入, 每次产出同样质量的输出。**不是 cleverness** (一次惊艳), 不是 **coverage** (覆盖所有边角)。可预测 > 聪明 > 全面。

落到写法: 宁可确定性高但保守的指令, 不要「视情况灵活发挥」的高上限措辞。flexibility 是 predictability 的敌人 (dimensions.md dim5 红灯: 「灵活把握/根据情况」≥3 处扣分)。

## 信息分层 (progressive disclosure 的三层落点)

progressive disclosure 已是主旨 (SKILL.md Phase 2 + dimensions.md dim7), 具体三层:

| 层 | 装什么 | 何时读 |
|---|---|---|
| **in-skill step** (SKILL.md 正文) | 每轮常驻的核心指令 / 工作流 / 硬护栏 | 每轮自动加载 |
| **in-skill reference** (`references/` 下) | 渐进披露的实质细节 (词表 / rubric / 反模式全表) | 模型按需 reach |
| **external reference** (外链 / 文档 URL) | 跨 skill 复用的权威一手资料 | 仅作来源指针, 不内联 (避免跨文件维护漂移) |

原则: 能 in-skill step 解决就别拆 reference; reference 只装「有它更好, 没它主流程仍跑」的实质细节; external 仅作来源标注非功能依赖 (见 skein「零外部 skill 硬依赖」同源纪律)。

## 何时 split skill

| 拆分信号 | 判据 |
|---|---|
| **by invocation** | 两个 skill 的触发条件互斥 (不同用户会说的词 / 不同时机) → 拆 |
| **by sequence** | 同一用户意图但分阶段 (先 A 后 B, A 的产出是 B 的输入) → 可拆成 A→B 链, 各自独立 invoke |

反例 (不该拆): 仅「内容太长」就拆 → 先试 progressive disclosure (拆 reference) + token 控制 (CJK 密度意识), 拆 skill 是最后手段 (dimensions.md dim7: 引用嵌套 ≤ 5 层)。

## pruning (修剪纪律)

skill 上线后**熵增是常态** — 每次加规则比删规则容易, 漂移成 sprawl (见下)。pruning 两把刀:

- **single source of truth** — 同一规则跨段 / 跨 skill 复述 3+ 次 → 措辞漂移 → 逻辑分叉 (anti-patterns.md #16)。pruning 时把规则收到**单一 canonical 段**, 其余段改指针引用。
- **no-op test 逐句** — 逐句问「删掉这句, skill 行为会变差吗?」答「不会」即删。no-op 句典型: 重复陈述已知 / 解释 Claude 已知的事 (anti-patterns.md #6) / 装饰性总结 (「综上」「换句话说」)。

## leading words (触发词前置)

description 里**触发词必须前置** — 用户会说的词放 description 开头, 让 harness 的匹配器最早命中。delay trigger word = 误触发 / 不触发。

- 正: `Processes marketing campaign data from CSV/Excel...` (动词 + 对象前置)
- 反: 「Helps with various tasks related to...」(空话开头, 触发词藏在尾部)

description 项目底线 < 512 字符 (dimensions.md dim1), 前置 = 把最稀缺的注意力预算花在触发匹配上。

## 6 failure modes (skill 质量退化的六种死法)

> dim9 (反例与黑名单) 评「反例成章 + 正向化」, 这里补「skill 整体演化时会踩的六种退化模式」— 编写 / 维护时反向自检。

| failure mode | 症状 | 解药 |
|---|---|---|
| **premature completion** | skill 主体没写完就收尾 (核心工作流缺步骤 / 缺失败分支) | validation-checklist.md 全勾才算完; 反拷问暴露漏洞 |
| **duplication** | 同一规则跨段复述 (Iron Law + 反例 + 自欺表 + 流程各述一遍) | single source of truth, 单 canonical 段 + 指针引用 |
| **sediment** | 规则只加不减, 历史决策堆成沉淀层无人清 | pruning (no-op test 逐句) 定期清; 区分「仍有效」vs「过时但没人敢删」 |
| **sprawl** | skill 膨胀到多职责 / 多触发域混杂 | by invocation 拆分; description 收窄到单一 use case |
| **no-op** | 句子删了不影响行为 (装饰 / 重复 / 解释已知) | no-op test 逐句删除 |
| **negation** | 「不要做 Y」黑名单让被禁行为更可用 (命名即召唤) | 默认正向表述, 仅必要硬护栏留反例配正例 (Negation 铁律, dimensions.md dim9 已覆盖) |

前 5 个 (premature completion / duplication / sediment / sprawl / no-op) 是 skill **演化期**退化模式; negation 是**编写期**红线。

## negation 转正向 (仅真 guardrail 留否定式)

默认改正向表述: 「不要做 Y」把被禁行为命名得更可及 (negation 死法本身)。改法是**说正向配方**——把「禁 X」换成「做 Z, Z 来自哪一步产出」这种可执行动作句, 而非停在「别做 X」。

只有真正的 **硬 guardrail** (破坏性 / 不可逆 / 安全类) 才保留否定式, 且**必须配正向配方**, 不能只留一句禁令收尾。判据: 拿掉这句禁令, 后果是否不可逆/不可挽回——是则留, 否则转正向。

## 改写动作清单 (git 试点共有动作, 供其余 9 份直接套用)

四个 git skill (git-commit/git-merge/git-pr/git-rebase) 改写时反复用到的 5 个动作, 每份改写逐条过一遍:

| 动作 | 判据 | 操作 |
|---|---|---|
| description 剪枝 | leading word (触发词) 前置; body 已有的身份复述句删掉 | 一 branch 一 trigger, 中文同义触发词列表照删 (见下方实测) |
| frontmatter 清标 | `name` 与目录名一致 | 删非标 `arguments:` 数组 (与 `argument-hint` 同一信息写两处), 保留 `argument-hint` |
| 步骤补完成判据 | 每个工作流步骤末尾有 checkable 且 exhaustive 的完成条件 | 防 premature completion, 缺则补一句「何时算这步做完」 |
| negation 转正向 | 逐条硬规过一遍 | 非真 guardrail 全部转正向配方; 真 guardrail 保留但补「改做什么」 |
| 逐句 no-op + relevance 测 | 整句问「删掉它, skill 行为会变差吗」 | 答「不会」→ **整句删, 不修词**; 删除记录写入下方「实测删除项」 |

保持语义不变的前提: 触发场景/硬规/失败兜底的**实际效果**改写前后一致, 只改表达与结构 (剪枝不是删功能)。

## 质量门验证法 (stdin 命令 + 三跑一致)

项目 CLAUDE.md 记的质量门命令对带 YAML frontmatter 的 SKILL.md **跑不通**, 改写后验证一律用以下 stdin 形式:

```bash
cat <SKILL.md 路径> | claude -p --bare "<问题>" --output-format stream-json 2>/dev/null \
  | jq -r 'select(.type=="result" and .subtype=="success") | .result'
```

跑不通的三个原因 (CLAUDE.md 原命令 `claude -p "$(cat ...)" ...` 踩的坑):

| 缺哪部分 | 后果 |
|---|---|
| 用 `"$(cat ...)"` 插值而非管道 | frontmatter 的 `---` 被解析成 CLI 选项, 报 `error: unknown option '---'` |
| 缺 `2>/dev/null` | stderr 的 connector 警告混进 jq, 报 `Invalid numeric literal` |
| 缺 `--bare` | skein hook 注入把 prompt 劫持成 exec mode, 或非 Anthropic 路由报 `API Error 400` |

端点仍会抖动 (偶发空返回/超时), 需**重试循环**兜底; 空返回不等于「改写失败」的结论, 重试后有正常返回才能下判断。

**predictability 验法 = 三跑一致**: 每份改写后, 同一个「主流程是什么」的 prompt **连跑 3 次质量门**, 三次的主流程描述必须一致才算过 (代价是调用量 ×3, 靠上面的重试循环兜端点抖动)。merge/rebase 额外必答对 `--ours`/`--theirs` 方向判定题 (两者语义相反, 改写前基线均答对, 答错即回归)。

## 实测记录 (git 试点 s1-s4, 直接引用不重跑)

### 中文同义触发词实测 (git-commit, s1)

结论已定, 其余 skill **照删不重推**: description 里的中文同义触发词列表整段删, 只留一 branch 一 trigger。

| 版本 | prompt | 调用次数 | 命中次数 |
|---|---|---|---|
| baseline (含同义词列表) | 把改动交了 | 3 | 3 |
| baseline (含同义词列表) | 暂存并提交 | 3 | 3 |
| deleted (删同义词列表) | 把改动交了 | 3 | 3 |
| deleted (删同义词列表) | 暂存并提交 | 3 | 3 |

6/6 → 6/6, **触发率未下降**——同义词列表是 no-op, 按上方「逐句 no-op 测」整段删。

### 实测删除项样本

| skill | 删的是什么 | 为什么删 (no-op/duplication) |
|---|---|---|
| git-commit | 非标 `arguments:` 数组 + 中文同义触发词列表 | 前者与 `argument-hint` 重复信息两处写; 后者见上方实测 6/6→6/6 |
| git-commit | 「高频噪声速判表」内联 | 与 `references/noise-and-ignore.md` duplication, 收敛到 references 单一真值源, SKILL.md 只留 context pointer |
| git-merge | 「比 rebase 安全」等比较句 | 与新引入的反转 (inversion) leading word 冗余, 方向说明已被反转表统一承载 |
| git-merge | 「诚实边界」段内与 step3 重复的方向警告 | no-op (信息已在 step3 说过一遍) |
| git-merge | `references/conflict-resolution.md` §poison 表内的重复条目 | 合并去重, §core 收敛前置检查/实质改动判据/冲突循环骨架为单一真值源, 供 git-rebase 引用 |
| git-rebase | `references/conflict-resolution.md` 内 §poison 表整段 | 改指 git-merge 单一真值源, 本侧只留 §direction 反转表 + §rerere (真实差异不去重) |
| git-pr | 失败处理表 3 行 (未推远端/自建 GitLab 域名/RTK wrapper 改写) | 与硬规或 references 逐句重复, no-op 测判定后整行删 |
| git-pr | body 内对 description 的身份复述句 | duplication, 改为核心矛盾陈述 |

**禁合并的反例** (真实差异, 不去重):
- `git-merge`/`git-rebase` 的 `references/recovery.md` 一对不合并——merge 侧 abort/reset/revert/ff 与 rebase 侧 backup/reflog/force-with-lease 是真实差异, 不是 duplication。
- 两份 `conflict-resolution.md` 的方向判定 (`--ours`/`--theirs`) 不合并成共享文件——merge 与 rebase 语义相反, 合并等于把 footgun 藏进 progressive disclosure 后面。做法是显式**反转 (inversion)** 表 + 两侧互指 pointer, 而非共享一份带条件分支的文件。

---

调用时机: 流程 A Phase 4 (装配) 对照「信息分层 / leading words / 6 failure modes 编写期项 / negation 转正向 / 改写动作清单」自检; 流程 B Phase 2 (诊断) 对照「6 failure modes 演化期项 + pruning」找退化根因; 改写后验证走「质量门验证法」跑 stdin 命令 + 三跑一致。
