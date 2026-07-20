# 00 — SKEIN 记忆扩展选型总结

> 任务: 为 SKEIN 现有 core+recall 两层规则记忆补充新模块 + CORE_BUDGET 移 config.yaml。本文件汇总 5 维调研，给推荐方案与最小融入设计草案。SKEIN 硬约束: 纯 stdlib、无 yaml/vector/LLM-runtime 依赖、本地。

## 顶层结论

SKEIN 的 core+recall **已经是 2025 主流分层范式 + 独立验证够用的设计** (Letta 一手实验: 文件+grep+LLM 检索在 LoCoMo 达 74% 超 Mem0 graph 68.5%)。因此**不建议引入向量/图 DB** (依赖冲突 + 不必要)。三件该做的事:

1. (用户已指明) CORE_BUDGET 移 config.yaml，默认 **1000** — 纯 stdlib 可读 yaml 子集。
2. recall 检索从子串 grep 升级为 **SQLite FTS5 BM25** (sqlite3 是 stdlib)，纯 stdlib 可行。
3. 新增 **external 层** (不注入 hooks，手动检索) + A-MEM 式 **links/backlinks** 增强 (纯 stdlib)。

## 五维对比表

| 维 | 代表方案 | 机制 | 依赖 | 纯 stdlib 可行 | 可融入 SKEIN 形态 | 验证强度 | 推荐度 |
|---|---|---|---|---|---|---|---|
| 类脑/神经 | CLS / sleep-time compute | 双系统隐喻 + 离线巩固 | 理论/LLM | 理论是;sleep-time 需 LLM | 隐喻背书 + maintain 当 sleep cycle | CLS 顶刊 1118 引用;sleep-time arXiv | ⭐⭐⭐ (理念) |
| 向量/语义 | Mem0 / Letta / LangMem | embedding retrieve + LLM 抽事实 | 向量 DB + LLM | ❌ | 不引入;借鉴 memory_type 字段 | Mem0 自报94% vs 独立49% (冲突) | ⭐ (不融入) |
| 知识图谱 | Graphiti / Zep / GraphRAG | entity-relation 时态图 | Neo4j + LLM | ❌ | 借鉴时态双端 + 反向链接 (纯 stdlib 可做) | Zep arXiv DMR 超越;Letta 反证 | ⭐⭐ (仅借鉴时态/反链) |
| 分层多 store | MemGPT / Letta blocks / Claude subagent | core vs archival 分层 | (SKEIN 已是) | ✅ 已实现 | SKEIN 已对应;新增 external 层 | MemGPT 开创;Claude Code 实证 | ⭐⭐⭐⭐ (external 层) |
| 实证基准 | Letta Filesystem / A-MEM / LongMemEval | 文件+grep / Zettelkasten 链接 | (前者无;后者 LLM) | Letta ✅ A-MEM 部分 | BM25 升级 + links/backlinks | Letta 一手;A-MEM NeurIPS | ⭐⭐⭐⭐ (BM25+A-MEM-lite) |

## 推荐方案 (3 个, 纯 stdlib 可行)

### 推荐方案 1 — A-MEM-lite: links + backlinks + 孤立检测 (纯 stdlib, 零新依赖)

**为什么**: A-MEM (NeurIPS 2025, 890 引用) 证明「记忆自建链接形成演化图」有效；SKEIN 已有 `related` + `[[slug]]` wikilink + maintain 断链检测，只需补**反向链接表 + 孤立节点检测**即得 A-MEM 的核心收益 (查规则时看谁引用它 + 发现无入度的孤岛)。

**最小形态骨架** (≤20 行, 加在 spec.py maintain/reindex):

```python
def _rebuild_backlinks(self) -> dict[str, list[str]]:
    """扫所有规则 body 的 [[slug]] → {target_stem: [referrer_rel,...]}。纯 grep 式扫描。"""
    all_stems = {f.stem for layer in LAYERS for f in self._rule_files(layer)}
    backlinks: dict[str, list[str]] = {s: [] for s in all_stems}
    for layer in LAYERS:
        for f in self._rule_files(layer):
            rel = f"{layer}/{f.parent.name}/{f.stem}"
            for m in re.finditer(r"\[\[([^\]]+)\]\]", _strip_frontmatter(f.read_text())):
                stem = m.group(1).split("|")[0].split("/")[-1].strip()
                if stem in backlinks:
                    backlinks[stem].append(rel)  # ponytail: 不去重, 反链密度也是信号
    return backlinks
```
- 新 maintain 判据 6: **孤立节点** — 规则 stem 既无入度 (无人 `[[它]]`) 又 status=active 且 created>STALE_DAYS → 候选归档/降级。
- 写 `<layer>/backlinks.md` 供 model 检索时看上下文 (reindex 时生成)。
- 成本: O(N²) 扫描 (N=规则数), SKEIN 规模 (<1000) 完全可接受。

### 推荐方案 2 — recall 升级 FTS5 BM25 (纯 stdlib sqlite3)

**为什么**: SKEIN recall 现是子串 grep (line 199-213)，精确匹配漏召回 (词形变化、部分匹配)。BM25 是 2025 社区共识「向量不必要时首选」(r/LangChain + memweave + Mem0 blog 汇聚)。sqlite3 是 Python stdlib，FTS5 BM25 纯 stdlib。

**最小形态骨架**:

```python
import sqlite3  # stdlib
def _rebuild_fts(self) -> None:
    db = self.root / ".recall.db"
    con = sqlite3.connect(db)  # ponytail: sqlite3 stdlib, 无新依赖
    con.execute("CREATE VIRTUAL TABLE IF NOT EXISTS rules USING fts5(stem, category, title, keywords, body)")
    con.execute("DELETE FROM rules")
    for f in self._rule_files("recall"):
        meta = _frontmatter(f.read_text())
        con.execute("INSERT INTO rules VALUES (?,?,?,?,?)",
                    (f.stem, f.parent.name, meta.get("title",""), meta.get("keywords",""), _strip_frontmatter(f.read_text())))
    con.commit(); con.close()

def recall_bm25(self, query: str) -> list[str]:
    con = sqlite3.connect(self.root / ".recall.db")
    rows = con.execute("SELECT stem, category, bm25(rules) AS s FROM rules WHERE rules MATCH ? ORDER BY s LIMIT 10", (query,)).fetchall()
    con.close(); return [f"{cat}/{stem}" for stem, cat, _ in rows]
```
- 保留现 grep 作 fallback (FTS5 MATCH 语法对特殊字符敏感)。
- reindex 时一并重建 FTS 索引。
- 风险: .recall.db 是衍生文件，不入 git (加 .gitignore)；reindex 幂等可重建。

### 推荐方案 3 — 新增 external 层 (不注入 hooks)

**为什么**: 用户已知需求「新增 external 外部记忆层 (不注入 hooks)」。对应 MemGPT external files / archival 概念 — 存放**不常驻、不自动召回、手动检索**的外部资料 (长文档、链接、外部知识)。与 core (常驻) + recall (自动 grep) 正交。

**最小形态**:
- 目录: `.skein/spec/external/<类目>/*.md` (同 frontmatter 约定)。
- 不加 SessionStart/SubagentStart hook (与 core 区别)；仅 `spec.py recall-external <query>` 命令手动检索 (复用 FTS5 索引, 跨 recall+external)。
- LAYERS 元组扩为 `("core", "recall", "external")`；reindex 三层；maintain 体检含 external (stale/断链)，但**不触发降级到 core** (external 是终点层)。
- index.md 顶层表加 external 行。

## 与现有 core/recall 协作图

```
SessionStart hook → 注入 core 索引 (常驻)
SubagentStart hook → 注入 core 全文 (按 agent 类目) + recall 索引提示
planning 时 → spec.py recall <query>   # 现 grep → 升级 FTS5 BM25 (方案2)
            → spec.py recall-external   # 新增, 手动检索 external (方案3)
task finish → sediment 写规则 (core/recall/external 三选一) + 让 agent 填 links (方案1)
maintain   → 体检 6 判据 (现5 + 孤立检测方案1) + --apply sleep cycle (神经隐喻)
```

## 关于 CORE_BUDGET 移 config.yaml (用户需求1)

- 现状: spec.py line 38 `CORE_BUDGET = 8000` 硬编码；用户要移 config.yaml 默认 **1000**。
- 纯 stdlib 读 yaml 子集: 不引入 pyyaml 依赖，手写极简解析 (SKEIN config.yaml 只需支持 `key: int` 平铺)，或复用项目已有 config 读取机制 (需勘察 skein 是否已有 config 加载 — **需要: main 确认 SKEIN 是否已有 config.yaml 及其解析约定**)。
- 默认 1000 (用户指定) vs 现 8000: 下降 8 倍，意味着现 core 规则量需大幅降级到 recall — maintain --apply 会触发批量 degrade，需用户预期此副作用。

## 需要转 main 的开放问题

1. SKEIN 是否已有 config.yaml 加载约定? (决定 CORE_BUDGET 迁移是否复用现有 reader，还是 spec.py 自带极简 yaml 解析)
2. CORE_BUDGET 默认从 8000→1000 是否预期触发首次 maintain 批量降级现 core 规则? (需用户知晓)
3. external 层是否需要专属 hook (如 manual 召回命令) 还是仅文件系统 + 手动 grep?
4. FTS5 在目标环境 sqlite3 编译选项是否含 `--enable-fts5`? (macOS/主流 Linux 默认含；若不含则方案2 fallback 保持纯 grep) — **需要: main 确认部署环境 sqlite3 FTS5 可用性**

## 数据源声明

- 外部检索经 **WebSearch** (agent-reach 的 Exa 后端未配置，全网语义搜索不可用；GitHub/Twitter/Jina Reader 可用但本次未必要)。
- 未覆盖: Exa 语义全网搜索、Reddit/小红书/B站中文社区讨论 (agent-reach 后端未配置或非本调研重点)。
- 一手论文 (arXiv) + 一手厂商博客 (Letta/Neo4j/Mem0 docs) + 二手综述 (Graphlit/Atlan) + 社区 (r/LangChain/forum) 混合；每条来源在对应 0X.md 标了可信度档。
