# PRD — cortex 清理 v2 legacy / 去版本号

## 背景

上一任务 (`05-12-cortex-namespace`) 把 vault 结构升级到双 namespace (知识库 + 记忆体系 L0-L4), 但保留了 v2 legacy 兼容路径:
- `presets/seed/` 下 9 个 legacy 桶 (`概念/实体/领域/来源/问题/临时/归档/moc/仪表盘`)
- `lint/schemas.py` LYT 保留 legacy 中文 8 桶 + 编号目录 (`10_concepts/...`)
- `cortex-install/SKILL.md` 含 v2→v3 兼容/迁移段落 (`schema_v3_pending`, "双轨保留")
- `presets/_structure.json` 有 `version: "3.0"` 字段, description 含 "v3 双 namespace"
- `seed/仪表盘v3/` 用 v3 后缀避开与 legacy `仪表盘/` 冲突

## 目标

**彻底删 legacy, 不要版本号 / 迁移 / 兼容概念。一切按当前最新结构。**

### 不在范围
- 不动 templates/ / cron wrappers / skills (除 cortex-install SKILL)
- 不动 mcp/

## 设计

### 删除清单

**目录** (`plugins/tools/cortex/presets/seed/`):
- `概念/`
- `实体/`
- `领域/`
- `来源/`
- `问题/`
- `临时/`
- `归档/`
- `moc/`
- `仪表盘/` (legacy v2 版, 9 文件)

### 重命名

- `presets/seed/仪表盘v3/` → `presets/seed/仪表盘/`

### 改 `_structure.json`

- 删 `version` 字段
- description 去掉 "v3" / "v2 升级" 字眼, 只描述当前结构
- seed_files: `src: "seed/仪表盘v3/..."` → `src: "seed/仪表盘/..."` (12 项)
- 保留 44 seed_files 项数不变

### 改 `lint/schemas.py`

LYT.root_dirs 删:
- 8 中文 legacy 桶: `概念/实体/领域/来源/问题/仪表盘/临时/归档` (仪表盘是新 v3 也用的名, 保留)
- 编号 legacy: `10_concepts/20_efforts/30_domains/40_anchors/50_calendar/60_journal/70_attachments/80_archive/90_inbox`
- `MOC/`

保留 (当前结构 + 系统层):
- `_meta`, `_templates`, `_assets`
- `知识库`, `记忆体系`, `仪表盘`, `归档`
- `folds`, `log`, `locales`, `sessions`
- `.obsidian`, `.trash`, `.git`

注意: `仪表盘` 和 `归档` 既是 legacy 也是当前结构顶层名, 保留。

LYT.root_files: 保持当前 (含 主页.md / 焦点.md / hot.md / index.md / README.md / dashboard.md / index-map.md / home.md / topics-moc.md / projects-moc.md)。
- 删 `home.md / topics-moc.md / projects-moc.md` (legacy MOC 三件套, 已被 主页.md 取代)
- 删 `dashboard.md / index-map.md` (legacy, 仪表盘/ 替代)

### 改 `cortex-install/SKILL.md`

删段落:
- "v3 设计总览" 标题改为 "设计总览" (去版本号)
- "检测既有 vault 的 schema 版本 (兼容老 vault)" 段落整段删
- `schema_v3_pending` 字段不写 `_meta/version.json`
- `_meta/version.json` 只写 `{"preset": "lyt", "created": ISO, "lang": "zh-CN"}`, 不写 schema 字段
- 删所有 "v2" / "v3" / "升级" / "迁移" / "兼容" 字眼
- 错误处理段删 "v2→v3 兼容模式分支"

保留:
- 流程 1-7 (解析 vault / lang / 写共享根 / 写业务结构 / git auto-sync / 回报 / cron)
- preset=lyt 固定

### 改 `_meta/memory-policy.yaml` (presets/seed/_meta/)

不动 (本任务范围外, 不涉版本号)。

### 不改

- `templates/_index.md` 含 legacy 引用? 检查; 若有删
- `mcp/cortex_mcp.py` (不涉版本号)
- skills/cortex-{memory,recall,...} (不涉)
- cron wrappers (不涉)
- presets/seed/_meta/memory-policy.yaml (不涉)
- presets/seed/root/{主页,焦点}.md (不涉)
- presets/seed/知识库/ + 记忆体系/ (当前结构, 不动)
- 其他 SKILL 不动

## 验收

- [ ] `ls plugins/tools/cortex/presets/seed/` 仅含 `_meta/ root/ 仪表盘/ 知识库/ 记忆体系/` (5 项, 无 legacy 9 个, 无 v3 后缀)
- [ ] `_structure.json` 无 `version` 字段, JSON 合法, 44 seed_files 全部 src 存在
- [ ] `lint/schemas.py` LYT.root_dirs 不含 8 中文 legacy / 编号 legacy / MOC
- [ ] `cortex-install/SKILL.md` 全文搜不到 `v2 / v3 / schema_v3_pending / 兼容 / 迁移 / 升级`
- [ ] 217 python tests 无回归
- [ ] git status clean after commit

## 风险

| 风险 | 缓解 |
|------|------|
| 已有 v2 vault 跑 lint 报 vault-structure-violation | 用户接受 — "不要兼容" 是显式约束。已有 vault 用户手动迁或 lint 跳过 |
| _meta/version.json 字段被其他代码读 | grep 检查; 若有 hard-coded "schema" 字段读取也一并删 |

## 子任务 (单 wave, 单 agent)

机械改 + 删, 不需分 wave。单 trellis-implement 执行。
