# map namespace: 骨架现算 + anchors 断链 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] 给 AI 一份代码地图, 免去每次开工重新摸一遍代码结构 —— 这是真实的重复成本
- [ ] **骨架现算, 语义沉淀** 的混合设计:
      - 骨架 (目录树 + 每文件顶层符号 + 行数) 由脚本**现算不落盘**, 永不 stale
      - 语义 (模块职责一句话 / 入口点 / 数据流 / 坑) 沉淀成 `map` namespace 的规则页, 带 `anchors`
- [ ] **不建代码符号索引** —— codebase 变动频率比规则高一到两个量级, 索引必然 stale, 维护它要 file watcher + 增量 reindex + 失效判定, 换来的东西 `rg` 0.05 秒就给了
- [ ] 真正缺的不是「搜代码」, 是**规则 ↔ 代码位置的绑定**: 规则里记了「exec 端点必须走 argv 白名单」, 但没记它在哪个文件
- [ ] 成功长什么样: `skein-spec map` 一条命令输出骨架 + 语义合并的地图; 语义页的 `anchors` 失效自动被 `maintain` 断链判据抓到 (可检测的 stale, 而非静默的)

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: `map` namespace 落地 + `spec.py map [--skeleton]` 骨架生成 + `recall --src code` + `anchors` 路径失效纳入断链判据
- [ ] 范围外: **符号级 FTS5 索引** —— 明确不做 (理由见目标)
- [ ] 范围外: **PageRank / 重要度排序** (aider repomap 那套) —— YAGNI, 目录树 + 符号名已够 AI 定位
- [ ] 范围外: 语义页的**内容生产** (归运行时 `skein-specer` 的 sediment); 本 task 只提供结构与命令
- [ ] 约束: 依赖 `spec-model-core` 已落地
- [ ] 约束: **纯 stdlib, 禁引 tree-sitter** —— `spec.py` 模块 docstring 立了纯 stdlib 铁律, tree-sitter 是编译依赖
- [ ] 约束: 正则抓符号不是 AST, 装饰器/嵌套/多行签名会抓不准 —— 必须留 `ponytail:` 注释写清这个 ceiling 与升级路径 (tree-sitter)
- [ ] 约束: 文件清单走 `git ls-files` (自动排除 gitignore, 零额外配置); 非 git 仓降级 `Path.rglob` + 已有排除范式

## 验收标准
可执行、可核对的完成断言 (逐条):

### 骨架现算
- [x] `spec.py map --skeleton` 输出: 目录树 + 每文件顶层符号名 + 行数, **不写任何文件**
- [ ] 文件清单来自 `git ls-files`; 非 git 仓 (无 git 二进制或非仓) 降级 `rglob` 且复用既有衍生文件排除范式 (`__pycache__` / `.mypy_cache` / `.ruff_cache` 等)
- [ ] 符号抓取覆盖: Python (`def` / `class` / `async def`) + JS/TS (`function` / `class` / `export function` / `export const`) + Go (`func` / `type`)
- [ ] 抓取代码处有 `ponytail:` 注释, 写明「正则非 AST, 装饰器/嵌套/多行签名抓不准, 升级路径 tree-sitter」
- [ ] 大仓性能: 1000 文件规模下 `map --skeleton` < 3s
- [ ] `map` (不带 `--skeleton`) 输出骨架 + `map` namespace 语义页合并的地图

### map namespace
- [ ] `spec/map/<category>/<topic>.md` 语义页, frontmatter 带 `anchors` 列表
- [ ] `init` 建 `spec/map/` 空目录; 无 map 页时 `map` 命令只输出骨架 (零回归)
- [ ] `recall "<q>" --src code` 返回: map 语义页 BM25 命中 + 命中页的 anchors 汇总
- [ ] `always` 顶层地图约定: `map/` 下可放**一页** `inclusion: always` 的极简顶层地图 (顶层目录 → 职责一行), 因这条每次开工都要用且极短

### anchors 断链
- [ ] `maintain` 断链判据扩到 `anchors`: 路径不存在即报为断链问题项
- [ ] `map` namespace 的 anchors 失效 → `maintain --apply` **可** archive (骨架现算, 语义页失效无损)
- [ ] `product` namespace 的 anchors 失效 → **只报告不 archive** (与 `spec-product-wiki` 一致, 两 task 若都实现需保持同一处逻辑不重复)
- [ ] anchors 支持 `path` 与 `path:symbol` 两种写法; `:symbol` 部分失效 (文件在但符号没了) 报为**弱断链**, 与文件整个不存在的强断链区分

### 兜底
- [ ] 新增用例覆盖: 骨架现算不落盘 / 三语言符号抓取 / 非 git 仓降级 / anchors 强弱断链 / map 可 archive 而 product 不可 / recall --src code
- [ ] `python3 scripts/skein.py doctor --quality` 通过

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-map-namespace`)
