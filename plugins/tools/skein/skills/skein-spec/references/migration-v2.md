# migrate — 旧两层结构 (core/recall) → namespace × inclusion

**定位**: 把仓库里还停留在旧 `spec/core/` + `spec/recall/` 两层结构的规则库, 迁移到 `rules/product/map/external` namespace × inclusion 新结构。`skein-setup` 在已初始化仓检出 `spec/core/` 存在时提示跑本迁移; `init` 对全新仓直接建新结构目录, 不经过本流程。

> **复用不新造**: 迁移不新增 CLI 命令, 全走既有 `mv` + frontmatter 编辑 + `skein-spec reindex`。namespace 是目录 (内容分类), inclusion 是 frontmatter 字段 (加载策略) —— 两者正交, 迁移本质是「把旧的层级目录语义拆成两个独立维度」。

## 两阶段全流程

### 阶段 1 — 机械改名 (无损, 可脚本化)

旧结构里「层」同时编码了两件事 (常驻与否 + 隐含的内容重要性), 新结构把它拆开: 层 → namespace 固定为 `rules`, 常驻与否 → inclusion 字段。

| 旧路径 | 新路径 | frontmatter 变更 |
|---|---|---|
| `spec/core/<cat>/<topic>.md` | `spec/rules/<cat>/<topic>.md` | 补 `inclusion: always` |
| `spec/recall/<cat>/<topic>.md` | `spec/rules/<cat>/<topic>.md` | 补 `inclusion: auto` |
| `spec/external/<cat>/<topic>.md` (若已存在) | 不动, 已是新结构的 external namespace | 补 `inclusion: manual` (若缺失) |

步骤:
1. `mv spec/core/* spec/rules/` (类目子目录结构不变, 只是父层名从 `core` 改 `rules`)。
2. `mv spec/recall/* spec/rules/` — **若 core 与 recall 有同名类目/主题文件**先人工核对再合并 (机械 mv 会覆盖, 禁盲目覆盖)。
3. 逐文件 frontmatter 补 `inclusion:` 字段 (原 core 来源补 `always`, 原 recall 来源补 `auto`), 其余字段 (title/category/keywords/status) 不动。
4. `skein-spec reindex` 重建 `rules/index.md` + 顶层 index + 正反链。
5. 校验: `skein-spec list` 确认条数 = 迁移前 core+recall 条数之和, 无丢失。

阶段 1 完成后规则库**功能等价**于旧结构 (同样内容, 同样加载行为), 只是路径和 frontmatter 变了 —— 可作为独立提交先落盘, 阶段 2 出问题也不影响已迁移的可用性。

### 阶段 2 — 语义分拣 (需判断, 逐条过一遍)

阶段 1 后所有内容都堆在 `rules` namespace, 但旧库里混杂着本该属于 product/map 的内容 (旧结构没有这两个 namespace 概念, 只能塞进 core/recall)。阶段 2 把这些分拣出去:

- **该归 product** 的信号: 内容描述「系统当前是什么样」而非「为什么这样改/踩过什么坑」(现状快照 vs 决策记录)。典型误放: 「登录流程现状是 xxx」被当成 recall 规则存了下来。
- **该归 map** 的信号: 内容是「某模块职责/数据流说明」而非可执行的约束或决策。典型误放: 「`services/payment/` 目录职责是 xxx」被当成 core/recall 存了下来。
- 判据同 [sediment-workflow.md](sediment-workflow.md) §2 的 namespace 判定标准, 不重复定义。

处置:
1. 逐条扫 `rules/` 全部文件, 按上述信号标 candidate (人工或派 skein-researcher 辅助扫, 不强制)。
2. 命中 product 信号 → 用模板 [templates/product.md.tmpl](templates/product.md.tmpl) 重写正文结构, `skein-spec sediment --namespace product ...` 落盘到新位置, 原 rules 条目 `skein-spec archive` (可逆) 移除。
3. 命中 map 信号 → 同理用 [templates/map.md.tmpl](templates/map.md.tmpl), 落盘 `--namespace map`。
4. 拿不准的 → 留在 rules, 不强行分拣 (宁可漏分不误分, 后续 finish sediment/amend 自然修正)。
5. 分拣完 `skein-spec reindex`。

阶段 2 **无硬性完成线** — 不要求一次性分拣干净, 可随着后续 sediment/amend 逐步修正; 阶段 1 才是迁移的强制门槛 (功能不能因迁移而回归)。

## 触发与确认

- `skein-setup` 检出 `spec/core/` 目录存在即提示「检测到旧两层结构, 是否迁移」, `AskUserQuestion` 征同意 (改动全库路径, 非破坏性动作也需确认)。
- 用户拒绝 → 旧结构继续可用 (`skein-spec` 各命令仍兼容旧路径读取, 只是新写入统一走新结构), 不阻塞正常使用。

## 失败 & 回滚

| 情况 | 处理 |
|---|---|
| core/recall 同名文件冲突 | 人工核对内容差异后手动合并, 禁盲目覆盖 |
| 阶段 1 后条数对不上 | 校验 mv 是否漏文件 (隐藏文件/非 `.md` 资源), 补跑 |
| 阶段 2 分拣错 namespace | `amend`/`sediment` 可改写或重新落盘, 原 archive 副本仍在 `.archive/<ts>/` 可核对 |
| 迁移中途中断 | 阶段 1 与阶段 2 分开提交, 从未完成的阶段续跑, 不需要整体重来 |

## 反例

| 禁 | 改为 |
|---|---|
| 阶段 1、2 混着做, 改名同时判断内容归属 | 分阶段, 阶段 1 先保证功能等价 (无损), 阶段 2 再语义分拣 |
| core/recall 撞名文件直接 mv 覆盖 | 先人工核对差异 |
| 强求阶段 2 一次分拣干净 | 拿不准的留 rules, 后续 sediment/amend 自然修正 |
| 迁移不问用户直接跑 | `AskUserQuestion` 征同意 (全库路径改动) |
