# product namespace + amend + finish 回写 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [x] **本轮全部新增价值都在这个 task** —— 前面三个是地基, 这个是 wiki 本体
- [x] 区分 delta 与 state: `task/<tid>/prd.md` 是**变更请求 (delta)**, 做完就归档; `spec/product/` 是**系统现状 (state)**, 随 task 完成被**更新**而非追加
- [x] 落地 `amend` —— 规则可以只增, **wiki 页面必须能被改写**。余额逻辑改了是修那一页, 不是在页尾追加「2026-07 更新: 现在改成…」(那样读者要自己做时序推理, 读三段才知现状)
- [x] 落地 **finish 回写**: task 的 delta 收敛进 wiki 的 state。这是整套设计的枢纽 —— 做对了 wiki 才活得起来, 做不对它就是又一个开局写完就烂掉的文档目录, 也就是所有手写 wiki 的死法
- [x] `product` 判据只报告不自动删 —— 时间型 stale 对 wiki 有害, 一个稳定功能的描述两年不改仍完全正确, 按 180 天自动归档等于**删对的知识**
- [x] 成功长什么样: 跑完一个 task, `spec/product/` 对应功能域的页被正确更新到当前真值, 且「改哪一页」这个判断有机械依据而非靠猜

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [x] 范围内: `product` namespace 落地 (按功能域切页 + `overview.md` 约定) + `amend` 命令 + finish 阶段的候选页反查 + `product` 判据只报告
- [x] 范围内: `spec.py finish-candidates <tid>` (给定 task 的 diff, 反查候选 product 页) —— 供 finish 阶段消费
- [x] 范围外: `skein-flow` / `skein-specer` / `skein-finisher` 的**提示词改造** (归 `spec-skills-agents-adapt`); 本 task 只提供 CLI 能力与脚本侧反查
- [x] 范围外: `map` namespace (归 `spec-map-namespace`); `analyze` 一致性核查 (归 `spec-prd-analyze`)
- [x] 约束: 依赖 `spec-model-core` 已落地
- [x] 约束: **`product` 页禁自动 archive / 禁自动删章节** —— 只报告, 处置交人或交 `amend`
- [x] 约束: `amend` 必须可逆 —— 改写前旧版进 `.archive/<ts>/`, 走既有归档机制
- [x] 约束: 纯 stdlib

## 验收标准
可执行、可核对的完成断言 (逐条):

### product namespace
- [x] `spec/product/<功能域>/` 按**功能域**切页 (非代码模块、非用户旅程); 每域固定一页 `overview.md` (该域是什么 / 边界 / 与其他域关系)
- [x] `init` 时建 `spec/product/` 空目录; 无 product 页时全部命令行为与无该 namespace 时一致 (零回归)
- [x] `product` 页 frontmatter 支持 `anchors` 列表, 且 `reindex` 把 anchors 写进 `product/index.md` 索引列
- [x] `recall "<q>" --src product` 只返回 product 命中

### amend (wiki 改写)
- [x] `amend --topic <ns>/<cat>/<topic> --section "<章节名>" --body-file <path>` 改写既有章节正文, 章节标题与前后其他章节保持不变
- [x] `amend` 前自动 archive 该页旧版到 `.archive/<ts>/`; `restore <ts>` 能取回改写前内容
- [x] `amend` 目标章节不存在 → 报错退出并列出该页现有章节名, **禁静默改成追加** (静默追加会让 wiki 退化成日志)
- [x] `amend` 后自动 reindex (index / FTS / backlinks 同步)
- [x] `amend --section` 可改 `## 标题` 本身 (`--rename-section`), 反链随之更新不断链

### finish 回写候选反查
- [x] `finish-candidates <tid>` 读该 task 的 git diff 触及文件列表 → 反查 `anchors` 命中的 product 页 → 输出候选页清单 (带命中的 anchor 与置信度)
- [x] anchors 无命中时降级: 按 task 的 `prd.md` 关键词跑 `recall --src product` 产候选, 并标注「弱候选 (关键词匹配, 非 anchors)」
- [x] 两路皆无命中 → 如实输出「无候选 product 页, 可能是新功能域」并建议新建页, **禁硬凑一页去改**
- [x] 输出为机器可读格式 (`--json`), 供 `skein-finisher` / `skein-specer` 直接消费

### product 判据 (只报告)
- [x] `maintain` 对 `product` **不套用** `STALE_DAYS` 时间判据
- [x] `product` 页的 anchors 路径失效 → 报为问题项, 但 `maintain --apply` **不 archive 它**
- [x] `product` 的问题项不写入 `.pending-fix` (不触发 auto-fix 自动改)
- [x] `maintain` 输出明确区分「可自动修」与「只报告」两类, 后者列出需人判断的原因

### 兜底
- [x] 新增用例覆盖: amend 改写/可逆/章节不存在报错/rename 反链跟随 / finish-candidates 三种命中路径 / product 不自动 archive / product 不写 pending-fix
- [x] `python3 scripts/skein.py doctor --quality` 通过

## 索引
- [x] 详细设计: [design.md](design.md)
- [x] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [x] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-product-wiki`)
