# Implement — novelist 检测门控满分 + 维度细分 + 检测修复合并入参模式

执行顺序： references 清单先（事实源） → SKILL.md（引用清单） → agents（对齐） → workflow.js → pipeline SKILL.md → 质检 → 自检。每步后 `git add`。

## Step 0 — 前置

- [ ] `python3 ./.trellis/scripts/task.py current` 确认 task 激活（task.py start 在 1.4 review gate 后）
- [ ] 工作目录：`/Users/luoxin/persons/lyxamour/ccplugin/plugins/tools/novelist`

## Step 1 — proofread references（事实源先行）

文件：`skills/novelist-proofread/references/proofread-checklist.md`

- [ ] 5 维逐项 → 12 子项表（design §3）
- [ ] 报告格式补「子项编号」字段：`[子项编号 类别] 位置 ...`
- [ ] 边界红线保留（只改文字层 / 风格保留 / 基准待定）
- [ ] detect vs fix 行为说明：detect 只产报告不改正文；fix 报告+就地改
- [ ] `git add`

## Step 2 — proofread SKILL.md

文件：`skills/novelist-proofread/SKILL.md`

- [ ] frontmatter `argument-hint: "[mode: detect|fix] [校对范围; 缺省=最近章]"`；`arguments: [mode, 校对范围]`
- [ ] description 加 mode 说明（detect 只读报告 / fix 就地改），保持 < 512 字符
- [ ] when_to_use 加 `detect, fix` 触发词，< 128 字符
- [ ] 校对维度表 5 行 → 12 子项表（或保留 5 维 + 子项列）
- [ ] 工作流 step 1 加 mode 解析（首 token detect/fix）
- [ ] step 3 派 proofreader 按 mode 给不同授权（detect=只读 / fix=可 Edit）
- [ ] step 5 门控 `质量分 == 100`（零错误），原文 `>95` 改 `==100`；补「连续 3 次未满分 → STOP 转人工」
- [ ] 失败模式 + 反例黑名单保留并加「detect 模式误改正文」一条
- [ ] `git add`

## Step 3 — check references

文件：`skills/novelist-check/references/conflict-rubric.md`

- [ ] 六维核对清单 → 18 子项表（design §4），每子项一行（维度/子项/缺陷例）
- [ ] 严重度分级表 🟢 行处理改为「🟢 也阻断满分（零容忍）」
- [ ] 单条冲突报告格式补「子项编号」
- [ ] `git add`

## Step 4 — check SKILL.md

文件：`skills/novelist-check/SKILL.md`

- [ ] frontmatter `argument-hint: "[mode: detect|fix] [检查范围; 缺省=全书]"`；`arguments: [mode, 检查范围]`
- [ ] description 加 mode（detect 只读 / fix 派 chapter-writer 单点修），< 512 字符
- [ ] when_to_use 加 `detect, fix`，< 128 字符
- [ ] 审查维度 6 行 → 18 子项表
- [ ] 工作流 step 1 加 mode 解析
- [ ] step 2 派 continuity-auditor 按 mode（detect=只读报告 / fix=允许单点 Edit 修正）
- [ ] step 3 门控 `健康分 == 100`（零冲突含 🟢），原 `>95` 改 `==100`
- [ ] 新增 step「mode=fix 修复路径」：单点冲突 → auditor Edit；段落级 → 派 chapter-writer（与 rewrite 模式 A 边界，design §2）
- [ ] 失败模式加「连续 3 次未满分 → STOP 转人工」
- [ ] `git add`

## Step 5 — rewrite references

文件：`skills/novelist-rewrite/references/rewrite-modes.md`

- [ ] 模式判定表加 mode 列：detect=诊断建议 / fix=执行（A/B/C）
- [ ] 加「mode=detect 诊断模式」段：只读扫描，输出「建议重写章清单 + 理由 + 建议 A/B/C」
- [ ] 三模式归入 mode=fix
- [ ] `git add`

## Step 6 — rewrite SKILL.md

文件：`skills/novelist-rewrite/SKILL.md`

- [ ] frontmatter `argument-hint: "[mode: detect|fix] [模式: 报告修复/从第N章起/第A-B章]"`
- [ ] description 加 mode（detect 诊断 / fix 执行 A/B/C），< 512 字符
- [ ] when_to_use 加 `detect, fix`，< 128 字符
- [ ] step 1 判模式前加 mode 解析（detect → 诊断分支；fix → A/B/C）
- [ ] step 4 棘轮定稿分 `== 100`（原 `>95`），补「连续 3 次未满分 → STOP」
- [ ] `git add`

## Step 7 — agents 对齐

文件：`agents/proofreader.md`
- [ ] 校对五维 → 12 子项表
- [ ] 工作方式加 mode（detect 只读产报告 / fix 就地 Edit）
- [ ] `git add`

文件：`agents/continuity-auditor.md`
- [ ] 审查六维 → 18 子项
- [ ] 模式表加「审查-detect / 审查-fix（单点 Edit）/ 预检」三态
- [ ] fix 模式边界：单点事实修正可 Edit；段落级重写交 chapter-writer
- [ ] `git add`

文件：`agents/chapter-writer.md`
- [ ] 加「被 rewrite 模式 A/B/C 与 check mode=fix 共用」段
- [ ] `git add`

## Step 8 — workflow.js

文件：`skills/novelist-pipeline/workflow.js`

- [ ] L39 `PASS_TOTAL = 95` → `100`
- [ ] L40 `PASS_CONSISTENCY = 95` → `100`
- [ ] L41 `PASS_HUMANNESS = 95` → `100`
- [ ] checker prompt（235-）增「18 子项核对」
- [ ] proofread prompt（273-）增「12 子项核对」
- [ ] fixer（282-）prompt 对齐 mode=fix
- [ ] computeScores 注释更新（满分门控语义）
- [ ] `node --check skills/novelist-pipeline/workflow.js` 语法验
- [ ] `git add`

## Step 9 — pipeline SKILL.md

文件：`skills/novelist-pipeline/SKILL.md`

- [ ] 门控阈值说明 `>95` → `==100`（与 workflow.js 一致）
- [ ] `git add`

## Step 10 — 质检（项目 CLAUDE.md 硬规）

对三 SKILL.md 跑：

```bash
cd /Users/luoxin/persons/lyxamour/ccplugin
for s in novelist-proofread novelist-check novelist-rewrite; do
  f="plugins/tools/novelist/skills/$s/SKILL.md"
  echo "=== $s ==="
  claude -p "读取 $f，回答：(1) 这个 skill 的 mode 入参是什么？detect 和 fix 分别做什么？(2) 通过门控的分数阈值是多少？(3) 它有几个检测子项维度？" \
    --output-format stream-json | jq -r 'select(.type=="result" and .subtype=="success") | .result'
done
```

- [ ] 三 skill 均正确识别 mode=detect|fix + 阈值==100 + 子项数（12/18/3模式）
- [ ] 返回非空且有意义
- [ ] description / when_to_use 字符数校验（< 512 / < 128）

## Step 11 — 自检 + 完成

- [ ] 9 AC 逐项核对
- [ ] `git status` 确认 11 文件全 staged
- [ ] 自检行输出（EXEC.md 格式）
- [ ] 非平凡发现落 memory（满分门控设计 / mode 入参统一模式 / check fix vs rewrite 模式 A 边界）
- [ ] task.py finish

## 失败处理

- 任一质检返回错误识别 → 回对应 SKILL.md 修正 frontmatter / 维度表措辞，重跑。
- workflow.js `node --check` 失败 → 回滚该文件改动重写。
- description 超限 → 压缩冗余句，保持触发词。

## 回滚点

每 Step 后 git add，整任务可 `git revert` 回滚。无破坏性操作。
