# spec-memory-extend — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] spec 记忆系统扩展: (1) CORE_BUDGET 从硬编码常量移至 config.yaml 用户可配置 (默认 1000); (2) 新增记忆模块 (A-MEM-lite 反链+孤立检测 + recall FTS5 BM25 召回升级); (3) 新增 external 外部记忆层 (不注入 hooks, 纯手动 CLI 检索); (4) skein-spec SKILL.md 加「planning/调研时优先 recall spec」纪律。
- [ ] 用户价值: 记忆预算用户可调; recall 召回精确度提升 (BM25 > 子串 grep); 反链+孤立检测发现孤岛规则; external 层存放不常驻不自动召回的外部资料; 寻找纪律固化「先查 spec」减少凭记忆重推。
- [ ] 成功: config.yaml 可配 spec_core_budget; recall 返 BM25 排序; maintain 报孤立节点 + 反链; sediment --layer external 写成功; SKILL.md 含寻找纪律。

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] **范围内**: spec.py 改动 (LAYERS 三层 / FTS5 / backlinks / core_budget 函数); skein.py CONFIG_DEFAULTS 加键; hooks.py stop-check budget 动态读; skein-spec SKILL.md 加段; test_spec.py 覆盖。
- [ ] **范围外 (非目标)**: 向量 DB / 图 DB (依赖冲突); 神经科学算法落地 (仅隐喻); external 层专属 hook (用户明确不入 hooks); FTS5 中文分词 (默认 unicode tokenizer 够用)。
- [ ] **已知约束**: 纯 stdlib 硬约束 (禁 pyyaml/向量 DB/LLM-runtime); sqlite3 FTS5 本环境已验证可用; 复用 skein._yaml_load 解析 config; 默认 1000 首次 maintain --apply 触发批量降级现 core (用户已确认接受)。

## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] config.yaml 含 `spec_core_budget: 1000` (CONFIG_DEFAULTS 回填)
- [ ] spec.py 删 `CORE_BUDGET = 8000` 常量, 改 `core_budget()` 函数动态读 config
- [ ] hooks.py stop-check budget 字段动态调 core_budget()
- [ ] recall 命令返 FTS5 BM25 排序结果, MATCH 失败 fallback grep
- [ ] `.recall.db` 衍生文件入 .gitignore
- [ ] reindex 产 `<layer>/backlinks.md`
- [ ] maintain 报孤立节点 (无入度+active+stale)
- [ ] LAYERS 扩三层, sediment --layer external 写成功
- [ ] recall 跨 recall+external 两层检索
- [ ] degrade 单向 core→recall (external 终点层)
- [ ] skein-spec SKILL.md 含「寻找纪律」段 (recall 优先顺序)
- [ ] `uv run pytest plugins/tools/skein/scripts/tests/test_spec.py` 全绿
- [ ] `uv run mypy plugins/tools/skein/scripts/spec.py` clean
- [ ] claude -p 质检门识别 SKILL.md 召回纪律正确

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) + research/00-summary.md (5 维调研 + 选型)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-memory-extend`)
