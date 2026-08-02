# 自动迁移 migrate 两阶段 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 1. 为什么分两阶段

迁移工作里有两类性质完全不同的判断:

| 类 | 例 | 谁做 | 确定性 |
|---|---|---|---|
| **机械重排** | `core/git/merge.md` → `rules/git/merge.md` + `inclusion: always` | 脚本 | 100% |
| **语义分拣** | 旧 `recall/arch/http.md#端点约定` 是「规则」还是「系统现状描述」 | AI | 需读全文判断 |

混在一起做, 要么脚本瞎猜 (错搬), 要么全交 AI (慢且不可靠地重复做确定的事)。所以拆开: 脚本先把确定的做完并**产候选降低 AI 负担**, AI 只判候选。

## 2. 阶段 1 — 机械迁移 (幂等, 可逆)

```
migrate --stage=1
  ↓
① archive <ts>            # 全库快照, 复用既有可逆归档机制
② 扫 spec/{core,recall,external}/**/*.md
③ 按映射表重排 + 注入 frontmatter   # 复用 restructure --map 作底层
④ 撞名章节级合并
⑤ 迁移 config.yaml 键
⑥ mkdir spec/product spec/map
⑦ reindex
```

**映射表**

| 源 | 目标路径 | 注入 frontmatter | 删除 frontmatter |
|---|---|---|---|
| `core/<cat>/<topic>.md` | `rules/<cat>/<topic>.md` | `namespace: rules` + `inclusion: always` | `layer` / `created` / `updated` |
| `recall/<cat>/<topic>.md` | `rules/<cat>/<topic>.md` | `namespace: rules` + `inclusion: auto` | 同上 |
| `external/<cat>/<topic>.md` | 原地 | `namespace: external` + `inclusion: manual` | 同上 |

**撞名合并**: core 与 recall 存在同 `<cat>/<topic>` 时合并进一页 —— 这是本次迁移的实质收益 (同主题的硬规与长尾经验现在被强制分在两个目录两个文件, 读者要读两处才知全貌)。合并后靠 `##` 章节区分内容、靠 frontmatter 区分加载。

⚠️ **合并页的 inclusion 冲突**: 一页只能有一个 `inclusion`, 但合并来源一个是 `always` 一个是 `auto`。取舍 → **合并页取 `always`** (保守: 宁可多注入也不丢硬规), 并在报告里列出该页, 提示后续可 `degrade` 拆分。

**幂等判定**: 检测 `spec/rules/` 存在且 `spec/core/` 不存在 → 报「已是新结构」直接返回, 零文件变更。

**配置迁移**: 仅当 `spec_core_budget` 等于旧默认值 `1000` 时改写为 `spec_always_budget: 8000`; 用户显式设过其他值则**平移原值**, 不覆盖用户意图。

## 3. 阶段 2 — 候选启发式打分 (只产报告, 不动盘)

脚本对迁移后 `rules/` 的每个**章节**打分, 产候选清单:

| 信号 | 权重倾向 |
|---|---|
| 含 `MUST` / `禁` / `铁律` / `必须` / `严禁` / `一律` | → `rules` (命令式, 强) |
| 有反例表 (`❌` / `禁/改为` 表格) | → `rules` (**最强信号** — 反例表是命令式契约特征) |
| 含 `现在` / `当前` / `流程是` / `行为是` / `目前` 且无命令式词 | → `product` 候选 |
| 描述模块职责 + 正文含文件路径 | → `map` 候选 |
| 以上皆无 | 不列入候选 (保持不动) |

**输出即结束** —— 脚本不搬。搬动归 `skein-specer` 读全文判定后走 `amend`。

理由: 启发式必然有假阳性, 而**误搬比误留难纠** (误留只是分类不佳, 误搬会让规则从 `always` 掉出常驻注入, 静默失效)。保守优先。

## 4. 关键取舍

| 取舍 | 决定 | 理由 |
|---|---|---|
| 迁移引擎自研 vs 复用 | **复用 `restructure --map` + `archive`/`restore`** | 两个机制已实现且已测; 重写等于给同一件事写第二套实现 |
| 阶段 2 自动搬 vs 只报告 | **只报告** | 启发式有假阳性, 误搬导致硬规静默掉出常驻注入 |
| 撞名合并页取哪个 inclusion | **取 `always`** | 宁可多注入 (可后续 degrade), 不可丢硬规 |
| 幂等实现 | 目录存在性探测, 非版本号标记文件 | 少一个需要维护的状态文件; 目录是物理事实 |
| 用户改过的 budget 值 | **平移不覆盖** | 覆盖用户显式配置违反最小惊讶 |

## 5. 测试接缝 (seam)

**唯一接缝 = `migrate` 命令方法**, 用 `tmp_path` 造一个旧结构 spec 库 (core/recall/external + config.yaml) 直调, 断言迁移后的文件树与 frontmatter。

- 不 mock 文件系统, 不起子进程
- 幂等用例 = 同一临时库连调两次, 第二次断言零变更 (比对文件 mtime 集合与内容 hash)
- 可逆用例 = 迁移前记录全库内容 hash → migrate → restore → 断言 hash 集合一致

## 6. 已知风险

| 风险 | 缓解 |
|---|---|
| 老仓 frontmatter 格式不齐 (缺 title / keywords 是列表形式) | 迁移只增删指定字段, 不校验其余; 不合法项列入报告交人, 不阻断迁移 |
| 撞名合并丢内容 | 合并前 archive 快照; 章节标题也撞时加后缀并存而非覆盖 |
| `restore` 撞名不覆盖新规则 (既有行为) | 回滚用例需断言 `restored-` 前缀并存语义, 而非期待完全覆写 |
| 阶段 2 启发式对中文命令式词汇漏判 | 词表同时含中英; 漏判的结果是「保持不动」, 属安全侧失败 |
