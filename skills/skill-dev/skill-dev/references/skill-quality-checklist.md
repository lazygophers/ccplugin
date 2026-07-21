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

---

调用时机: 流程 A Phase 4 (装配) 对照「信息分层 / leading words / 6 failure modes 编写期项」自检; 流程 B Phase 2 (诊断) 对照「6 failure modes 演化期项 + pruning」找退化根因。
