# sediment 沉淀流程 (task finish 阶段, skein-specer 异步) — 判定门 + 自动写盘

## 1. 判定门 (任一正向触发即沉淀)

正向 (任一命中):
- ① 新命令式契约 (MUST/禁, 后续同类任务会再踩)
- ② 踩坑 ≥2 轮 (根因可写可验证契约, 非一次性 bug)
- ③ 反复 ≥2 task (grep 可验)
- ④ 跨任务可复用决策 (选型/架构边界/API 约定)
- ⑤ 验收基准 (可复用断言)

排除 (命中则不沉淀): 一次性 bug / 本 task 私有细节 / 已有规则覆盖。

- 判定归 model (语义判断, 脚本做不了)。全无增量则跳过, 禁硬凑。
- 结论一句话交代: 触发哪项 → 沉淀 / 全否 → 跳过。

## 2. 定 namespace × inclusion + 归类 (触发后)

两个维度正交, 分开判 (混判是最常见的错):

- **namespace** (放哪个目录, 内容分类): 「决策/踩坑, 为什么这样改」→ **rules**; 「当前需求现状, 不叠历史决策链」→ **product** (过时用 amend 改写, 见下文); 「代码结构/职责/数据流说明」→ **map**; 「外部长文档全文」→ **external**。sediment 的默认落点是 **rules** (finish 阶段踩坑绝大多数是决策/规则); product/map 走各自专属流程 (product 见 `finish-candidates` + SKILL.md「product wiki」章节, map 走 `skein-spec map` 现算 + 人写语义页)。
- **inclusion** (怎么加载, frontmatter 字段, 与 namespace 无关): 硬约束 / 命令式契约 / 后续必再踩 → **always** (常驻, 软预算 `spec.always_budget`, 超则告警降级); 长尾 / 上下文密集 / 偶尔相关 → **auto** (默认落点, 按需召回); 特定路径触发 → **fileMatch** (加 `globs` 字段); 极冷门参考 → **manual**。拿不准 → 默认 auto (不轻易增 always 常驻负担)。
- **类目**: 归到 git / test / arch / build / style / domain / ops 之一 (无合适则新取名或 `misc`)。类目决定沉淀落哪个子目录 + 索引归类, 与 namespace/inclusion 是第三个独立维度 (只用于 rules 内部再分组)。

> 常见误判: 把 namespace 当「层级」按重要性分 (❌ core 更重要 = rules, recall 次要 = product) —— namespace 只管内容属于哪一类, 不代表优先级; 优先级/常驻与否只由 inclusion 决定。

## 3. 自动写盘 (判定门通过即写, 无需逐次询问用户)

执行主体是 **skein-specer (异步 fire-and-forget)**: task finish 闭环后被派发, 自主跑判定门 + namespace×inclusion 归类 → 直接写盘, 不走 AskUserQuestion, main 不等待回传 (finish 已闭环)。skein-specer 逐项输出沉淀 trace (namespace/inclusion + 标题 + 触发项), 回传到达后 main 只补 output trace 供审阅, 不硬停等批 —— 记忆积累是高频动作, 每次询问是噪声。误沉淀可靠 `skein-spec reindex` 前手动删文件 / 后续 sediment 调 inclusion 纠正 (低成本可逆)。

> 全局 / 批量动作仍前置征同意 (非「每次」): bootstrap 冷启动播种、reconstruct 整库重建 各自跑前一次 `AskUserQuestion`, 一次覆盖整轮, 内部候选自动写。

## 4. 写盘命令

```
skein-spec sediment --namespace rules --inclusion always|auto --category git --topic merge \
  --title "契约标题" --keywords "worktree,merge" --body-file <正文.md>
```

把规则作为 `## <title>` 章节**追加**进 `<namespace>/<category>/<topic>.md` (不存在则建; frontmatter 只留 title/category/keywords/status/inclusion, fileMatch 另加 globs, 可选 anchors, 无时间字段) + **自动 reindex** (重建各 namespace index + 顶层 index + 正反链, 否则新规则漏检)。

粒度硬规: 文件夹 = 类目, 文件 = 主题 (文件名即主题), `## <规则标题>` = 一条规则。同主题规则并入同一文件, **禁一条规则一个文件**。`--topic` 缺省回落类目同名主题。关联写 `[[主题#规则标题]]` wikilink → `backlinks.md` 自动出正链 (→) 与反链 (←)。

## 升降级 (可选, 按需再加)

always↔auto 频率驱动自动升降级暂不实现 (YAGNI)。手动改: 编辑规则文件 frontmatter 的 `inclusion:` 一行 + `skein-spec reindex`; 或 `skein-spec degrade <cat>/<name>` (always→auto)。**搬文件不改加载策略** — 目录 = namespace(内容类型), inclusion 是 frontmatter 字段, 两者正交。换类目/namespace 才需要移动文件。

## status 转态 (proposed → active / superseded)

`sediment --status` 四值: `active`(默认) / `proposed` / `deprecated` / `superseded`。plan 阶段沉淀的未验证决策 (grill/design 推出但当轮 check 没验过) 落 `proposed`, 供 `analyze` 的置信度检查识别。

- **proposed → active** (决策后续被验证成立): **无法**靠再跑一次默认 `sediment` 达成 —— `write.py` 只在显式传**非** `active` 值时才覆盖既有 status (防常规追加意外抹掉 deprecated/superseded 标记), 传 `--status active` 等同默认值, 不生效。改法: 直接 Edit 该主题文件 frontmatter 的 `status:` 行, 再跑 `skein-spec reindex`。spec 规则文件不在 PreToolUse 硬阻名单 (只挡 task.json/task.md), 直接 Edit 允许。
- **proposed → superseded** (决策被新方案取代): 跑 `sediment --namespace <ns> --category <cat> --topic <同 topic> --status superseded ...` 显式传非 active 值, 正常覆盖写盘 + 自动 reindex, **无需**手改 frontmatter。
- 只换状态字段用上述两条; 正文也要同步改写走 `amend`。

## 5. amend vs sediment 抉择树

同是「写盘更新记忆」, 两条命令语义不同, 选错会把现状 wiki 写成无限堆叠的历史日志:

```
这条内容是 ——
├─ 新踩的坑 / 新决策, 不否定已有条目 (rules 常态)?
│   └─ sediment (追加新章节, 旧条目原样保留)
└─ 旧结论已过时, 系统现状只该有一份真值 (product wiki 常态)?
    └─ amend --topic <ns/cat/topic> --section <章节名> --body-file <正文>
        ├─ 目标章节存在 → 改前先 archive 旧版本(可逆), 其余章节/frontmatter 逐字不动
        └─ 目标章节不存在 → 报错列现有章节名 (❌ 静默追加, 走 sediment 才是建新章节)
```

- **rules namespace 几乎总用 sediment** — 决策历史本就该保留 (「为什么当初这样选」本身是有价值的记忆), 追加是常态。
- **product namespace 现状过时几乎总用 amend** — 需求现状只有一份真值, 旧版本经 amend 内部 archive 保留可逆, 但主文件不再展示矛盾的新旧版本并存。
- 边界情况: product 页**新增一个此前没有的章节** (如新功能域第一次记录) 用 sediment 建页/建章节 (不是「改写」, 是「首次落盘」); 只有「改写已存在的现状描述」才用 amend。
- 命令语法与写盘细节见 SKILL.md「amend」章节, 本节只管抉择, 不重复语法。
