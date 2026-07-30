# spec.py 模型层: namespace×inclusion 正交 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 1. 核心模型: 两维正交

```
spec/<namespace>/<category>/<topic>.md
      ↑ 内容类型        ↑ 功能分类     ↑ 一页, 内含多个 `## 章节` = 最小检索/引用单元
                                       frontmatter 声明 inclusion = 加载策略
```

| 维 | 取值 | 开闭 | 存放位置 |
|---|---|---|---|
| **namespace** | `rules` / `product` / `map` / `external` / 用户自加 | **开放** | 目录名 (物理事实) |
| **inclusion** | `always` / `auto` / `fileMatch` / `manual` | **封闭四值** | 文件 frontmatter |

**为什么 inclusion 放 frontmatter 而非目录**: Cursor rules 与 Kiro steering 均如此 (文件平铺 + frontmatter 决定加载)。放目录会导致「同一主题的硬规与长尾经验被强制分在两个文件」, 读者要读两处才知全貌。

**为什么 inclusion 是封闭集**: Cursor 与 Kiro 独立设计收敛到同一组四值, 证据充分。给只有四种实现的东西留开放扩展点是过度设计。

## 2. 关键取舍

| 取舍 | 决定 | 理由 |
|---|---|---|
| namespace 白名单 vs 目录扫描 | **目录扫描** (`NAMESPACES` 仅作 init 建目录的默认清单) | 满足「自由加分类」; 白名单会让加 namespace 变成改代码 |
| `always` 页是否入 FTS | **入** | `recall` 命令要能查到全库; 注入与检索是两件事, 不该耦合 |
| `degrade` 实现 | **改 frontmatter 一字段 + reindex**, 不移文件 | inclusion 脱离目录后, 跨层 git mv 已无意义; 顺带消掉 git mv 失败这一整类失败模式 |
| stale 判据 | **按 namespace 分表** | 时间型 stale 对 wiki 有害 — 稳定功能的描述两年不改仍正确, 按 180 天自动归档等于删对的知识 |
| `--layer` 兼容 | 保留一轮 deprecated alias (core→always / recall→auto) | 已有仓与 agent 提示词大量在用, 硬切会连带 9 个 agent 一起碎 |
| 预算键 | 新键 `spec_always_budget` 默认 8000, 旧键 fallback | 符合 core 规则「配置真值来源唯一 (CONFIG_DEFAULTS + yaml + env)」; 1000 是笔误 — `spec.py:47` 注释 `SUBAGENT_BUDGET_TOKENS = 2000 ≈ core_budget() 字符`, 2000 token ≈ 8000 字符可自证 |

## 3. 改动映射 (现状 → 目标)

| 位置 | 现状 | 目标 |
|---|---|---|
| `:48` `LAYERS` | `("core","recall","external")` | `NAMESPACES`(默认清单) + `INCLUSIONS`(封闭四值); 实际 namespace 由 `_scan_namespaces()` 目录扫描得 |
| `:49` `STALE_DAYS` | 全层通用 180 | 保留常量, 仅 `rules` namespace 使用 |
| `:100` `core_budget()` | `spec_core_budget`, 默认 1000 | `always_budget()`: `spec_always_budget` → 旧键 → 8000 |
| `:170` `_core_text_raw()` | 扫 `core/` 目录 | 扫全 namespace 筛 `inclusion == always` |
| `:188` `_core_index()` | 同上 | 同上 |
| `:261` `_recall_fts()` | 跨 `recall`+`external` | 全 namespace + `--src` 过滤 |
| `:393` `_rebuild_fts()` | 硬编码 `for layer in ("recall","external")` | 全 namespace; 表加 `namespace`/`inclusion`/`anchors` 列, `layer` 列保留一轮 |
| `:414` `_reindex_layer()` | 每层一 index | 每 namespace 一 index; 行加 `inclusion`/`anchors` 列 |
| `:891` `sediment` argparse | `--layer` required choices | `--namespace`(自由 str) + `--inclusion`(choices, 默认 auto) + `--globs` + `--anchors`; `--layer` deprecated alias |
| `:897` `--status` | `active/deprecated/superseded` | 加 `proposed` (供 plan 阶段沉淀未验证决策) |
| `:908` `degrade` | git mv 跨层 + 改 layer | 改 frontmatter 一行 + reindex |
| `:904` `maintain` | 判据全层通用 | 按 namespace 分表 + anchors 失效纳入断链判据 |
| `:911` `archive`/`restore` | `--layer` | `--namespace` (`--layer` alias) |

## 4. maintain 判据分表

| namespace | 过期信号 | 处置 |
|---|---|---|
| `rules` | 180 天未动且无引用 / keywords 重复 ≥3 / deprecated / superseded | archive (可逆) |
| `product` | **仅** anchors 失效 | **只报告, 禁自动 archive** (需求真值不能自动删) |
| `map` | anchors 失效 | archive (骨架现算, 语义页失效无损) |
| `external` | 仅 deprecated | archive |
| 全部 | `always` 页总字符超 `always_budget()` | `degrade` → `auto` (改字段) |
| 全部 | `inclusion: fileMatch` 缺 `globs` | 报为配置问题 |

## 5. 测试接缝 (seam)

**唯一接缝 = `Spec` 类的 CLI 命令方法层** (`sediment` / `reindex` / `recall` / `maintain` / `degrade`), 用 `tmp_path` 造临时 spec 库直调, 不 mock 文件系统、不起子进程。

- 复用现有 `scripts/tests/test_spec.py` 的既有接缝 (它已在这一层测), 不新建
- `always_budget()` 的 config 读取用真实临时 `config.yaml`, 不 monkeypatch
- 断言看**可观测输出**: index.md 文本 / `.recall.db` 查询结果 / 文件 frontmatter, 不断言内部私有方法调用

## 6. 已知风险

| 风险 | 缓解 |
|---|---|
| `_rules()` 等私有方法被 `hooks.py` 直调 (`cmd_stop_check` 调 `_scan_findings`) | 改签名前先 grep 全仓调用点; 保持 `_scan_findings` 对外行为不变 |
| `views_golden.json` 快照可能含 spec 结构 | 本 task 不动 prd 模板, 若快照仍破则同轮重生 |
| `--layer` alias 与新参数同时给 | 显式冲突检测: 二者同给即报错退出, 不猜意图 |
