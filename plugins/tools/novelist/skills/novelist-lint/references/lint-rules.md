# novelist-lint 规则定义

7 规则基于 `docs/plugin-development.md` §重要规则 + §测试验证。每条含定义、违规示例、合规示例、修复命令。

## R1 — plugin.json 存在且 name 合规 (error)

**定义**: `.claude-plugin/plugin.json` 存在 + 合法 JSON + `name` 字段匹配 `^[a-z0-9-]+$`。

**违规**:
```json
{ "name": "Novelist Plugin" }   // 大写 + 空格, 不匹配
```
缺 `.claude-plugin/plugin.json` 文件也算。

**合规**:
```json
{ "name": "novelist" }
```

**修复**: 改 `name` 为 kebab-case; 补 plugin.json。

---

## R2 — commands/agents/skills 在插件根 (error)

**定义**: `commands/`、`agents/`、`skills/` 必须在插件根目录，不在 `.claude-plugin/` 内。

**违规**:
```
novelist/
├── .claude-plugin/
│   ├── plugin.json
│   └── skills/          # ✗ 误入
│       └── novelist-write/
└── ...
```

**合规**:
```
novelist/
├── .claude-plugin/
│   └── plugin.json
├── skills/              # ✓ 插件根
│   └── novelist-write/
└── ...
```

**修复**: `mv .claude-plugin/skills ./skills`

---

## R3 — skill 子目录 kebab-case + 含大写 SKILL.md (error)

**定义**: `skills/*/` 每个子目录名匹配 `^[a-z0-9-]+$`，且含文件 `SKILL.md`（精确大写）。

**违规**:
```
skills/Novelist_Write/        # 大写下划线
skills/novelist_write/        # 下划线非连字符
skills/novelist-write/
└── skill.md                  # 小写, 应 SKILL.md
```

**合规**:
```
skills/novelist-write/
└── SKILL.md
```

**修复**: `mv skills/Novelist_Write skills/novelist-write`; `mv skill.md SKILL.md`

---

## R4 — agents/*.md 文件名 kebab-case (error)

**定义**: `agents/*.md` 文件名 stem 匹配 `^[a-z0-9-]+$`。

**违规**: `agents/ChapterWriter.md`、`agents/chapter_writer.md`

**合规**: `agents/chapter-writer.md`

**修复**: `git mv agents/ChapterWriter.md agents/chapter-writer.md`

> 同步改 plugin.json 中 `agents` 数组引用的路径。

---

## R5 — 产物/临时文件不泄漏 (warning)

**定义**: 插件目录树内不出现：
- 文件: `.DS_Store`、`.darwin-results.tsv`、`*.pyc`、`*.pyo`
- 目录: `__pycache__`、`*.bak`

**违规**:
```
novelist/skills/.darwin-results.tsv   # 测试产物
novelist/.DS_Store                    # macOS 垃圾
novelist/scripts/__pycache__/         # 编译缓存
```

**修复**:
```bash
rm <path>
# 或加 .gitignore 防再进:
echo ".darwin-results.tsv" >> .gitignore
```

---

## R6 — plugin.json 路径真实存在 (error)

**定义**: plugin.json 中 `commands`/`agents`/`skills`/`hooks` 字段指向的路径必须真实存在。

**违规**:
```json
{
  "agents": ["./agents/old-name.md"],   // 文件已改名
  "skills": "./skills-missing/"          // 目录不存在
}
```

**合规**: 路径与实际文件/目录一致。

**修复**: 改 plugin.json 路径，或 `git mv` 文件对齐路径。

---

## R7 — skill frontmatter name 与目录名一致 (warning)

**定义**: 每个 `skills/<dir>/SKILL.md` 的 frontmatter `name:` 字段 == 目录名。

**违规**:
```
skills/novelist-write/SKILL.md
---
name: novelist-writing    # ✗ 与目录名 novelist-write 不一致
---
```

**修复**: 改 frontmatter `name` 对齐目录名（或反向）。

> 此规则为 warning：frontmatter name 是 skill 路由标识，与目录名不一致会导致路由歧义，但非致命。

---

## 与 scripts/check.py 的关系

本 lint **独立**于仓库根 `scripts/check.py`，不替代它：
- `check.py` 覆盖更广（plugin.json 格式、hooks 测试、name alignment、desktop versions），但有已知 bug（line 470 检查 `skills.bak` 而非 `skills`）。
- 本 lint 专注**目录结构/命名/产物泄漏**，规则明确可机器校验，覆盖 check.py 漏掉的 skills 目录校验（R3/R5/R7）。
- 两者可并用：`check.py` 查配置/hook，本 lint 查结构/命名。
