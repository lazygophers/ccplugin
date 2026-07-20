# spec-memory-extend — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 用户确认 (2026-07-20, AskUserQuestion 4 问)

1. **记忆模块** (全选 3): A-MEM-lite 反链+孤立检测 + recall FTS5 BM25 升级 + sleep-time 巩固隐喻 (维持 maintain --apply 当 sleep cycle, 纯理念背书无新码)
2. **CORE_BUDGET 默认** = 1000 (接受批量降级现 core)
3. **config 加载**: 复用 `Skein.config()` + `_yaml_load` (CONFIG_DEFAULTS 加 spec_core_budget)
4. **external 检索**: FTS5 (跨 recall+external 两层), external 仅 CLI 不入 hooks

## 调研背书 (research/00-summary.md)

- **A-MEM** (NeurIPS 2025, 890 引用) — 记忆自建链接形成演化图有效
- **FTS5 BM25** — 2025 社区共识「向量不必要时首选」(r/LangChain + memweave + Mem0 blog)
- **Letta Filesystem** 74% > Mem0 graph 68.5% (一手实验) — SKEIN「文件+检索+model 读全文」范式已验证不弱于向量
- **sleep-time compute** (arXiv 2504.13171, +18%) — maintain --apply 当 sleep cycle 隐喻背书
- **不引入向量/图 DB** (纯 stdlib 硬约束冲突, 且实证不优于文件+检索)
- FTS5 本环境已验证可用 (`sqlite3.connect` + `fts5` virtual table + `bm25()` 排序)

## 改动清单 (5 项)

### 1. CORE_BUDGET 移 config.yaml (默认 1000)

**现状** (spec.py:38): `CORE_BUDGET = 8000` 硬编码常量。

**修法**:
- spec.py 删 `CORE_BUDGET = 8000` 常量
- spec.py 加 `core_budget() -> int`: 读 `.skein/config.yaml` 的 `spec_core_budget` 键 (复用 skein._yaml_load), 缺失/非数字 → 默认 1000
- spec.py 内所有 `CORE_BUDGET` 引用改调 `core_budget()` (懒求值, 配置可热改)
- skein.py `CONFIG_DEFAULTS` 加 `"spec_core_budget": 1000` (skein.py:150)
- hooks.py:242 `from spec import CORE_BUDGET` 删; hooks.py:273 `"budget": CORE_BUDGET` 改调 `core_budget()`

**复用点**: skein._yaml_load (skein.py:126) 已支持平铺 key; Skein.config() (skein.py:191) 已有缺键自动回填机制。spec.py 直接 import 复用。

**副作用**: 默认 1000 vs 现 core 22 条 ~6600 字符 → 首次 `maintain --apply` 触发批量降级 ~85% core→recall (用户已确认接受)。

### 2. A-MEM-lite: 反向链接 + 孤立检测

**新增 `_rebuild_backlinks()` (spec.py)**:
```python
def _rebuild_backlinks(self) -> dict[str, list[str]]:
    """扫所有规则 body 的 [[slug]] → {target_stem: [referrer_rel,...]}。A-MEM-lite 反链表。"""
    backlinks: dict[str, list[str]] = {}
    for layer in LAYERS:
        for f in self._rule_files(layer):
            rel = f"{layer}/{f.parent.name}/{f.stem}"
            for m in re.finditer(r"\[\[([^\]]+)\]\]", _strip_frontmatter(f.read_text())):
                stem = m.group(1).split("|")[0].split("/")[-1].strip()
                backlinks.setdefault(stem, []).append(rel)
    return backlinks
```

**reindex 时写 `<layer>/backlinks.md`**: 每条规则的反链 (谁引用它), 供 model 检索看上下文。

**maintain 加判据 6 (孤立检测)**:
- 规则 stem 无入度 (反链表空) + status=active + created > STALE_DAYS → 候选归档/降级
- spec.py `_scan_findings` 加分支; maintain --apply 把孤立 active+stale 归档

### 3. recall 升级 FTS5 BM25

**新增 `_rebuild_fts()` (spec.py)**:
```python
import sqlite3  # stdlib, 无新依赖
def _rebuild_fts(self) -> None:
    db = self.root / ".recall.db"
    con = sqlite3.connect(db)
    con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS rules USING fts5(stem, category, title, keywords, body, layer)")
    con.execute("DELETE FROM rules")
    for layer in ("recall", "external"):  # core 不入 FTS (已常驻), 仅按需层
        for f in self._rule_files(layer):
            txt = f.read_text()
            meta = _frontmatter(txt)
            con.execute("INSERT INTO rules VALUES (?,?,?,?,?,?)",
                        (f.stem, f.parent.name, meta.get("title",""), meta.get("keywords",""),
                         _strip_frontmatter(txt), layer))
    con.commit(); con.close()
```

**recall 命令升级** (spec.py:199):
- 优先 FTS5 BM25 排序 (`WHERE rules MATCH ? ORDER BY bm25(rules)`)
- FTS5 MATCH 语法对特殊字符敏感 → 失败 fallback 现有 grep (`_scan_findings` 模式)
- reindex 时一并 `_rebuild_fts()`
- `.recall.db` 衍生文件, `.gitignore` 排除

### 4. external 层 (不注入 hooks, 纯手动)

**LAYERS 扩三层** (spec.py:41):
```python
LAYERS = ("core", "recall", "external")
```

**external 特性**:
- 目录 `.skein/spec/external/<类目>/*.md` (同 frontmatter 约定)
- **不加 SessionStart/SubagentStart hook** (与 core 区别, 与 recall 也区别 — recall 有 subagent 提示)
- 仅 `spec.py recall <query>` 跨 recall+external 两层检索 (FTS5)
- reindex 三层; maintain 体检含 external (stale/断链/孤立)
- **external 是终点层 — maintain --apply 不降级到 external, 也不从 external 降出** (sediment 可写 external, 但 degrade 目标只 core→recall 单向)
- index.md 顶层表加 external 行

**sediment --layer external**: 已支持 (LAYERS 元组扩三层后, `--layer` choices 自动含 external)。

### 5. skein-spec SKILL.md 加「planning 寻找时优先找 spec」纪律

**位置**: skein-spec/SKILL.md recall 章节顶部 (现 line 30 附近)。

**加内容** (正向表述, 复用现有 recall 命令):
```markdown
## 寻找纪律 (planning/调研/找方案时)

**动手前优先跑 `skein-spec recall "<关键词>"`** — 现有规则沉淀比凭记忆重推快且准。
顺序: recall spec (core 已常驻无需 recall) → vault → 项目本地 (Read/Grep) → 外部搜索。
recall 命中 → model 读全文判相关 → 相关的注入 task 上下文。
```

## subtask 拆解

| # | subtask | 文件 | deps |
|---|---|---|---|
| st1 | CORE_BUDGET 移 config + 删硬编码 + hooks 改调 | skein.py / spec.py / hooks.py | 无 |
| st2 | A-MEM-lite 反链+孤立 (backlinks.md + maintain 判据6) | spec.py | 无 |
| st3 | recall FTS5 BM25 + .gitignore | spec.py | 无 |
| st4 | external 层 (LAYERS 三层 + recall 跨层 + index) | spec.py | st3 (FTS5 索引复用) |
| st5 | skein-spec SKILL.md 寻找纪律 | SKILL.md | 无 |
| st6 | test (test_spec.py 覆盖: config 读取 / backlinks / FTS5 / external 三层 / 孤立判据) | test_spec.py | st1-st5 |

st1/st2/st3/st5 改不同区域可并行; st4 依赖 st3 (FTS5); st6 依赖全部。

**简化合并** (减 subtask 数): st1+st3 合 (都改 spec.py 配置/检索区); st2+st4 合 (都改 spec.py LAYERS/索引/判据)。→ 实际 4 subtask:
- st1: config 迁移 (skein.py + spec.py + hooks.py)
- st2: A-MEM 反链 + external 层 + LAYERS 三层 (spec.py)
- st3: FTS5 BM25 recall (spec.py + .gitignore)
- st4: SKILL.md 寻找纪律 + test (SKILL.md + test_spec.py)

st2 依赖 st3 (external 入 FTS5); st1/st3 并行; st4 依赖 st1-st3。

## 验证

- `uv run pytest plugins/tools/skein/scripts/tests/test_spec.py` 全绿 (新加 test)
- `uv run mypy plugins/tools/skein/scripts/spec.py` clean
- `uv run python plugins/tools/skein/scripts/spec.py maintain` 报告新判据 (孤立节点)
- `uv run python plugins/tools/skein/scripts/spec.py recall "git"` FTS5 BM25 返回排序结果
- `uv run python plugins/tools/skein/scripts/spec.py sediment --layer external ...` 写 external 成功
- `skein config` 显 `spec_core_budget: 1000`
- claude -p 质检门 (改了 SKILL.md, CLAUDE.md 强制)

## 不碰 (YAGNI)

- 向量 DB (依赖冲突 + 实证不优)
- 图 DB (依赖冲突)
- 神经科学算法落地 (仅隐喻, 无 agent 可落地实现)
- external 层专属 hook (用户明确不入 hooks)
- FTS5 tokenizer 中文分词 (现默认 unicode tokenizer 足够, 词形变化场景英文为主; 中文 recall 仍可 grep fallback)
