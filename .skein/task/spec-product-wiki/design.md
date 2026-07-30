# product namespace + amend + finish 回写 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 1. delta vs state — 整套设计的核心区分

```
task/<tid>/prd.md          spec/product/<域>/*.md
   ↑ 变更请求 (delta)          ↑ 系统现状 (state)
   一次性, 做完归档            长期演化, 被 amend 更新
   「这次要改什么」             「系统现在是什么」
```

关系类比 git: delta 是 commit, state 是工作树。**finish 就是 apply** —— 把这次的 delta 收敛进 state。

⚠️ 反面: 若把 product 做成「索引历史 prd.md」, 那是在检索一堆历史 delta, 读不到当前真值。

## 2. 粒度: 按功能域切页

| 切法 | 问题 |
|---|---|
| 按代码模块 (`scripts/skein.py` 一页) | 重构一次全失效; 且这是 `map/` 的职责, 会重复 |
| 按用户旅程 (「建 task 到完成」一页) | 跨域, 一个 task 的 delta 要改三页, 回写时判不准改哪页 |
| **按功能域** (`task-lifecycle/` `spec-memory/` `cli/`) | ✅ 一个 task 的改动通常落在一个域内 → **回写时「改哪页」好判** |

每域固定一页 `overview.md` (该域是什么 / 边界 / 与其他域关系), 其余按需切细节页。

**选这个切法的唯一理由**: 这套设计唯一真正的失败模式是**回写判不准该改哪页** —— 判不准就会退化成到处追加, wiki 变成日志, 然后就是所有手写文档的死法。按功能域切是让「改哪页」尽可能机械的切法。

## 3. `amend` — wiki 改写

```
amend --topic product/task-lifecycle/state-machine --section "状态流转" --body-file /tmp/new.md
  ↓
① archive 该页旧版 → .archive/<ts>/     # 可逆
② 定位 `## 状态流转` 章节边界 (到下一个 `## ` 或 EOF)
③ 替换该章节正文, 其余章节与 frontmatter 逐字不动
④ reindex (index + FTS + backlinks)
```

**目标章节不存在 → 报错退出并列出现有章节名。禁静默降级成追加。**

这条是硬规: 静默追加正是 wiki 退化成日志的机制 —— 每次「找不到就追加」, 三个月后一页里有五段互相矛盾的描述, 读者要做时序推理才知道哪段是现状。

`--rename-section` 改 `## 标题` 本身时, 需同步更新指向该章节的 `[[topic#章节]]` 反链, 否则制造断链。

## 4. finish 回写: 「改哪一页」怎么判

三路降级, 从机械到启发式, 全部**只产候选不自动改**:

| 路 | 依据 | 置信度 | 输出标注 |
|---|---|---|---|
| ① anchors 反查 | task 的 git diff 触及文件 ∩ product 页的 `anchors` | 高 | `anchors 命中: <file>` |
| ② 关键词召回 | task 的 `prd.md` 关键词 → `recall --src product` | 弱 | `弱候选 (关键词匹配, 非 anchors)` |
| ③ 皆无命中 | — | — | `无候选, 可能是新功能域, 建议新建页` |

**③ 必须如实报告, 禁硬凑一页去改** —— 硬凑会把无关的域污染成拼盘, 比不写更糟。

`finish-candidates <tid> --json` 输出机器可读格式, 由 `skein-finisher` 勘察时调、`skein-specer` 消费后走 `amend`。**脚本只给候选, 判定与改写归 AI** —— 同 `migrate` 阶段 2 的分工原则: 脚本做确定的, AI 做判断的。

## 5. `product` 判据: 只报告

| 判据 | rules | product |
|---|---|---|
| 180 天 stale | ✅ 用 | ❌ **不用** |
| keywords 重复 ≥3 | ✅ archive | ❌ 只报告 |
| anchors 失效 | 可选 | ✅ **只报告** |
| deprecated/superseded | ✅ archive | 只报告 |
| 写 `.pending-fix` | ✅ | ❌ 不写 |

**为什么时间判据对 wiki 有害**: 一个稳定功能的描述可以两年不动还完全正确。按 `STALE_DAYS = 180` 它会被自动归档 —— 这是在删对的知识。规则不同: 规则久不用可能已过时; 现状描述久不改说明功能稳定, 恰恰是**更可信**。

**为什么 product 不自动修**: 需求真值只有人 (或读了 diff 的 AI) 知道该改成什么。自动 archive 一页 product = 静默丢掉一块系统知识, 且没人会发现丢了。

## 6. 关键取舍

| 取舍 | 决定 | 理由 |
|---|---|---|
| product 页粒度 | 按功能域 | 让 finish 回写「改哪页」的判断尽可能机械 |
| amend 找不到章节 | **报错**, 禁追加 | 静默追加 = wiki 退化成日志的机制 |
| finish 回写自动改 vs 产候选 | **产候选** | 改写需读 diff 判语义, 脚本做不了; 但候选反查是机械的, 脚本该做 |
| product 自动归档 | **禁** | 误删知识不可察觉, 是最贵的失败 |
| amend 可逆 | 旧版进 `.archive/<ts>/` | 复用既有机制; wiki 正文只留当前真值, 历史交 git + archive |
| 新功能域无候选时 | 如实报「建议新建」 | 硬凑污染无关域, 比不写更糟 |

## 7. 测试接缝 (seam)

**唯一接缝 = `amend` / `finish-candidates` 命令方法**, `tmp_path` 造 spec 库直调。

- `finish-candidates` 的 git diff 输入需可注入 —— 用参数传文件列表而非内部直调 git, 这样测试不必造真 git 仓 (**这是选这个接缝的关键**: 若内部硬调 `git diff`, 测试就得起真仓, 接缝会被迫下移)
- amend 可逆用例: 记录改前内容 hash → amend → restore → 断言 hash 一致
- product 不自动 archive 用例是**回归重点** —— 误删知识是最贵的 bug

## 8. 已知风险

| 风险 | 缓解 |
|---|---|
| 回写判不准该改哪页 → 退化成到处追加 | 按功能域切页 + anchors 反查 + amend 找不到章节即报错 (三重防线) |
| anchors 维护成本 (代码挪了要改 anchors) | 失效自动被 `maintain` 断链判据抓到并报告 —— 是**可检测的 stale**, 不是静默的 |
| product 页越写越长无人清理 | `maintain` 报页大小; 但**不自动清** —— 长而正确胜过短而残缺 |
| 新功能域反复被判「无候选」→ 页永不建立 | `finish-candidates` 输出明确建议新建路径; specer 判定门允许新建 product 页 |
| 与 `to-spec`「禁写文件路径, 会很快过期」冲突 | 不冲突: 那条反对的是**静默 stale** (路径写在 PRD 正文没人查)。anchors 是**可检测的** —— 失效即被 maintain 报出。且骨架路径归 `map` 现算, product 只存语义 |
