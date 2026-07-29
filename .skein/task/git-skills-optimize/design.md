# 按 writing-great-skills 优化 skills/ 全部 13 个 skill — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 执行形状：先试点后推广，同一 task 内两段

grill 后用户裁定 scope 扩到全部 13 个，但**不打平**：`skills/git/` 4 个仍作试点先跑，收敛出 checklist，剩余 9 个再照 checklist 推。DAG 上体现为 `git 四份 → checklist → 其余九份`，checklist 是硬关口而非事后产物。

| 组 | skill | 备注 |
| --- | --- | --- |
| git (试点) | git-commit / git-merge / git-pr / git-rebase | 8 references, 447 行 |
| design | design-color / design-uiux | 各 ~12 与 ~25 references，全 task 最大两份，INDEX.md 分平台 (app/cli/html/tui) |
| code-quality | architecture-design / clean-code / perf-optimization | clean-code 只有一份 research 索引 |
| project | oss-license / promo-posts | 各 4-5 references |
| skill-dev | plugin-dev / skill-dev | skill-dev 自身已带 3 份 checklist 类文件，改它时格外注意 duplication |

## 关键取舍

**取舍 1 · 四个 skill 全保持 model-invoked（用户定）** — 官方文档对有副作用的命令类 skill 推荐 `disable-model-invocation: true`，但那把 context load 换成 cognitive load（Matt: 你自己成了索引）。用户裁定全不上：模型仍可自主触发，常驻开销改由**剪 description** 来降（一 branch 一 trigger + 去掉 body 已有的身份复述）。这同时守住 PRD 约束「对外行为语义不变」——改触发方式就是改语义。

**取舍 2 · merge↔rebase 的去重只做「冲突判定」一处，不做全域合并** — 两份 `references/conflict-resolution.md` 结构同构但**语义相反**（merge 里 `--ours`=当前分支；rebase 里 `--theirs`=当前分支）。合并成一份共享文件是错的：把最易错的方向判定塞进一个带条件分支的文件，等于把 footgun 藏进 progressive disclosure 后面。做法反过来——**把方向对照做成一张显式反转表，两份文件各自保留自己那半，并互相 context pointer 指认「另一半是反的」**。真正可去重的是两份文件里与方向无关的部分（实质改动判据 / 前置检查 / 冲突循环骨架），这部分收敛到单一真值源。

`recovery.md` 一对**不去重**——merge 侧是 abort/reset/revert/ff，rebase 侧是 backup/reflog/force-with-lease，是真实差异，不是 duplication。

**取舍 3 · leading word 选定** — 四份统一引入两个词锚定行为：
- **反转 (inversion)** — 专指 `--ours`/`--theirs` 在 merge 与 rebase 下含义对调。一个词替掉现在两份文件里各自散着的长解释。
- **不可逆 (irreversible)** — 锚定 rebase/force-push/`git rm --cached` 这类「做了收不回」的动作，替掉现在散在硬规里的各种「必须先备份」「必须先确认」措辞。

**取舍 4 · negation 全面转正向，只留三条硬 guardrail** — 现有四份充斥 `禁 git add -A` / `不 push` / `禁全盘 --ours` 这类否定句。按 Matt：否定命名了那个不该做的动作，反而让它更可及。改法是**说正向配方**（「逐个 `git add <path>`，路径来自上一步 status 输出」），只有真无法正向表达的保留为禁令，且每条必须配「改做什么」。保留的三条：不主动 push / 疑似密钥即停 / rebase 前必建备份分支。

## 诊断与改写计划 (逐 skill)

四份共有的改写动作（每份都做）：

| 动作 | 判据 |
| --- | --- |
| description 剪枝 | leading word 前置；删掉 body 已复述的身份句；中文同义触发词按下方「取舍 5」实测定夺 |
| frontmatter 清标 | `name` 与目录名一致；删 `arguments:` 数组（与 `argument-hint` 同一信息写两处，single source of truth 直接判它），保留 `argument-hint` |
| 步骤补完成判据 | 每步末尾一句 checkable 且 exhaustive 的完成条件，防 premature completion |
| negation 转正向 | 见取舍 4 |
| 逐句 no-op + relevance 测 | 整句删，不修词；删除项记入 checklist |

| skill | 主要病灶 | 改写动作 |
| --- | --- | --- |
| `git-commit` | 四条硬规全是否定式；「高频噪声速判表」与 `references/noise-and-ignore.md` 有 duplication | 删非标字段；硬规转正向（保留「不主动 push」「疑似密钥即停」两条 guardrail 并配正向配方）；速判表收敛到 references 单一真值源，SKILL.md 只留 context pointer |
| `git-merge` | 与 rebase 的冲突处理段 duplication；`--ours` 语义只在本地说清，未指认反转 | 引入**反转**表并指向 rebase 侧；「用户说都以当前为准 ≠ 全盘 `--ours`」这条是真 guardrail，保留但配正向做法；共有冲突骨架收敛 |
| `git-pr` | 四步工作流里「识别平台」与「生成内容」两块可 branch 化（gh vs glab 是两条 branch，各自只需自己那半）；失败处理表 7 行有 no-op 行 | 平台差异下沉 `references/platform-and-content.md`，SKILL.md 留分叉指针；失败表逐行跑 no-op 测 |
| `git-rebase` | 同 merge 的 duplication；「不可逆」概念散在三条硬规里 | 引入**不可逆** leading word 统摄备份/远端最新/拿不准即停；**反转**表本侧半 + 指回 merge |

**取舍 5 · 中文同义触发词「实测定夺」而非照方法论删（用户定）** — 现有 description 末尾都挂着「触发词:「提交」「commit」「把改动交了」」这类列表。Matt 判同义改写为 duplication 该 collapse，但中文口语触发是否真靠这些同义词撑着，没数据。做法：**拿 `git-commit` 当实验组**，删同义词后用「把改动交了」这类口语跑质量门，看还触不触发；降了就把同义词还回去，不降才对其余 12 份照删。方法论服从实测，不拿触发率赌。

**取舍 6 · predictability 用「三跑一致」证（用户定）** — PRD 原写「predictability 可观察地提升」不可测。改为可执行基准：每份改写后**同一 prompt 连跑 3 次质量门，主流程描述一致**才算过。代价是质量门调用量 x3，而端点本就抖（见下），需重试循环兜。

**取舍 7 · checklist 并入既有文件，不新建** — 用户选的落点是 skill-dev。但 `skills/skill-dev/references/` 这个路径不存在（`skill-dev/` 是组目录，下辖 `plugin-dev/` 与 `skill-dev/`），且 `skills/skill-dev/skill-dev/references/` 下已有 `skill-quality-checklist.md` / `validation-checklist.md` / `optimization-log.md` 三份 checklist 类文件。再落第四份就是本 task 正在消灭的那个 duplication。做法：**并入 `skill-quality-checklist.md`**，新增一节承载 writing-great-skills 维度与实测踩坑，与既有内容对不上的地方一并收敛。

## 质量门

项目 CLAUDE.md 记的命令对带 YAML frontmatter 的文件**跑不通**（`---` 被当 CLI 选项，且 stderr 混入 jq）。本次一律用 stdin 形式：

```bash
cat <SKILL.md> | claude -p "<问题>" --output-format stream-json 2>/dev/null \
  | jq -r 'select(.type=="result" and .subtype=="success") | .result'
```

端点抖动，需重试循环。每份至少问两问：**触发场景 + 主流程**，且主流程那问**连跑 3 次要答得一致**（取舍 6）；merge/rebase 额外问 **`--ours`/`--theirs` 指哪个分支**（改写前基线：两份均答对，这是回归红线，答错即改写失败）。

## 并行安全

14 个 subtask 各自独立目录，零文件重叠。DAG 两处收束：
- `s5`（checklist）`depends_on` git 四份 —— 它要汇的是四份的实测记录。
- `s6..s14`（其余九份）全部 `depends_on s5` —— 拿 checklist 当输入，不各自重推方法论。
- `s14`（skill-dev）额外 `depends_on s13`，且它改的正是 s5 写入的那个文件所在的 skill，防两边对同一份 checklist 各写各的。
