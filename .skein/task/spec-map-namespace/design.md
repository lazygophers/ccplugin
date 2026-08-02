# map namespace: 骨架现算 + anchors 断链 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 1. 混合设计: 骨架现算 + 语义沉淀

| 层 | 内容 | 产生方式 | stale 风险 |
|---|---|---|---|
| **骨架** | `git ls-files` 目录树 + 每文件顶层符号名 + 行数 | 脚本现算, **不落盘** | **零** — 每次现算 |
| **语义** | 模块职责一句话 / 入口点 / 数据流 / 坑 | AI 沉淀成 `map` namespace 页, 带 `anchors` | 有, 但被 `maintain` 断链判据抓到 |

**为什么混合而非二选一**:
- 纯生成式: 纯 stdlib 只能做到目录级 + 正则符号, 抓不出「这个模块干嘛」— 那需要读懂代码
- 纯沉淀式: 质量高但会 stale, 且要人/AI 持续维护整棵树

拆开后各取所长: 机械的部分永不 stale, 需要理解的部分才沉淀, 且失效可检测。

## 2. 明确拒掉的两个主流做法

| 拒 | 主流做法 | 理由 |
|---|---|---|
| **符号级 FTS5 索引** | Serena / mcp-language-server | codebase 变动频率比规则高一到两个量级 → 索引必然 stale → 维护 = file watcher + 增量 reindex + 失效判定。换来的东西 `rg` 0.05s 就给了, 且永不 stale |
| **PageRank 重要度排序** | aider repomap | YAGNI。目录树 + 符号名已够 AI 定位。且 aider 那套依赖 tree-sitter, 违反纯 stdlib 铁律 |

**真正缺的不是「搜代码」** —— rg / LSP / octocode 都在手上。缺的是**规则 ↔ 代码位置的绑定**: 规则里记了「exec 端点必须走 argv 白名单」, 但没记它在哪个文件。`anchors` 补的是这个。

## 3. 骨架生成

```
map --skeleton
  ↓
① git ls-files              # 自动排除 gitignore, 零配置
   └─ 非 git 仓 → Path.rglob + 既有排除范式 (__pycache__/.mypy_cache/.ruff_cache/...)
② 按目录分组建树
③ 逐文件正则抓顶层符号 + 计行数
④ 输出文本, 不写盘
```

**符号正则** (按扩展名分派):

| 语言 | 模式 |
|---|---|
| Python | 行首 `def ` / `class ` / `async def ` |
| JS/TS | 行首 `function ` / `class ` / `export function ` / `export const ` |
| Go | 行首 `func ` / `type ` |

⚠️ **必须留 `ponytail:` 注释**: 正则非 AST —— 装饰器、嵌套定义、多行签名会抓不准。ceiling 明确, 升级路径 tree-sitter。这是刻意接受的天花板, 不是疏漏。

**性能**: 只读文件头部行做正则 (顶层符号必在行首, 无需读全文做 AST), 1000 文件 < 3s。

## 4. `anchors` 强弱断链

| 写法 | 失效判定 | 级别 |
|---|---|---|
| `path/to/file.py` | 文件不存在 | **强断链** |
| `path/to/file.py:symbol` | 文件不存在 | **强断链** |
| `path/to/file.py:symbol` | 文件存在但符号没了 | **弱断链** |

区分的理由: 文件没了几乎肯定要改 anchors; 符号没了可能只是改名 (正则抓不准也可能是误判) —— 弱断链只报告, 不作为 archive 依据。

**符号存在性检测复用骨架抓取逻辑** —— 同一个正则, 一处实现两处用。

## 5. archive 策略按 namespace 分

| namespace | anchors 失效 | 理由 |
|---|---|---|
| `map` | **可 archive** | 骨架现算兜底, 语义页失效无损 —— 丢了还能靠骨架定位 |
| `product` | **只报告** | 需求真值不能自动删, 丢了没人发现 |

⚠️ **与 `spec-product-wiki` p4 有逻辑重叠** —— 两个 task 都要碰「anchors 失效按 namespace 分处置」。约定: **判据表的单一实现归 `spec-model-core` s6 的 `maintain` 分表**, 本 task 与 p4 只是把自己 namespace 的行填进那张表, 禁各写一份判定。

## 6. 关键取舍

| 取舍 | 决定 | 理由 |
|---|---|---|
| 建符号索引 vs rg | **不建** | 索引必 stale, rg 已覆盖且永不 stale |
| tree-sitter vs 正则 | **正则 + 标 ceiling** | 纯 stdlib 铁律; 正则够定位, 不够精确但明确标出 |
| 骨架落盘 vs 现算 | **现算** | 落盘就有 stale 问题, 而这是骨架唯一的优势所在 |
| 文件清单来源 | `git ls-files` | 自动继承 gitignore, 零配置; 非 git 仓才降级 |
| 顶层地图放哪 | `map/` 下一页 `inclusion: always` | 每次开工都要用且极短; 不占 namespace 独立性 |
| PageRank 排序 | 不做 | YAGNI |

## 7. 测试接缝 (seam)

**唯一接缝 = `map` 命令方法 + `anchors` 检测函数**, `tmp_path` 造小型文件树直调。

- 文件清单来源需可注入 (参数传清单) —— 否则测试要造真 git 仓, 接缝被迫下移
- 三语言符号抓取各一个最小样本文件即可, **不追求覆盖所有语法变体** (ceiling 已明确标出, 测试不该假装它精确)
- 骨架不落盘用例: 跑完断言临时目录内文件集合无变化

## 8. 已知风险

| 风险 | 缓解 |
|---|---|
| 正则漏抓/误抓符号 | 已标 ceiling; 影响面仅「地图不够全」, 不影响正确性; 升级路径明确 |
| 与 p4 的 anchors 判定重复实现 | 判据表单一实现归 `spec-model-core` s6, 本 task 只填行 (见 §5) |
| 大 monorepo 骨架输出过大挤爆上下文 | 骨架现算, 可加深度/目录过滤参数; 顶层地图页才是常驻的那份, 骨架按需跑 |
| `map` 页 anchors 大量失效后被批量 archive | archive 可逆 (`restore <ts>`); 且骨架兜底不丢定位能力 |

## 9. k5 收尾留痕 (mypy --strict 清零)

- map.py 13 处 + index.py 1 处, 实测与派发时给出的分布一致
- 修法: `dict`→`dict[str, object]` 补泛型参数 (4处); `_parse_frontmatter` 返回值统一标注 `dict[str, str | list[str]]` 并显式声明局部变量, 修掉 `list→str`/`str无append`/`object不可索引` 一串——根因是 `meta: dict = {}` 被 mypy 按首次赋值推断成 `dict[str, str]`, 后续赋 list 类型冲突; 不是双类型运行时 bug, 纯标注缺失
- `_merge_with_map_semantic` 里 `merged["semantic"]` 同理: 顶层 dict 字面量类型被推窄, 改为局部 `semantic: dict[str, list[dict[str, object]]]` 变量收集完再一次性组装返回值
- index.py:388 `anchor_counter: Counter[str] = Counter()` 补类型参数
- line 71 `# type: ignore[attr-defined]` 删除 (无谓, self.root 已由 TYPE_CHECKING 块声明为 Path)
- 结果: `mypy --strict plugins/tools/skein/scripts/skeinlib/` → `Success: no issues found in 47 source files`; `pytest plugins/tools/skein/scripts/tests` → 367 passed, 0 failed
- 未调低严格度配置, 未加新 type: ignore
