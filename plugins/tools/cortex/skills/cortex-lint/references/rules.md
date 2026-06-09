# 7 规则详情 (R1-R7)

每条规则: 定义 / 级别 / 是否 autofix / 检测策略。路径/目录/级别映射等结构性事实**不在此处复制**, 仅给出权威源指针。

## 权威源

- 顶层布局 + 三模块路径 + 必备目录: `cortex-schema/references/topology.md`
- 三模块命名规则: `cortex-schema/references/knowledge-modules.md`
- frontmatter 字段 + 模板: `cortex-schema/references/templates.md`
- memory 5 级物理树 + level↔dir 映射: `cortex-schema/references/memory-levels.md`

## R1 — wikilink 死链 (warn)

- **定义**: `[[X]]` 必须能解析到 vault 内某个 `.md` 文件名 (basename, 去 `.md`) 或某文件 frontmatter 的 `aliases` 列表项。
- **级别**: warn (死链不能猜, 由用户决定建页 / 删链 / 改名)。
- **autofix**: 否。
- **检测**: 遍历所有 `.md`, 正则抓 `[[([^\]|#]+)`, 与全局 `name → file` 索引比对; aliases 也注入索引。

## R2 — frontmatter 必备字段 (error)

- **定义**: 每个 `.md` 的 frontmatter 必备字段集合按 type 分桶定义, 权威清单见 `cortex-schema/references/templates.md`。
- **级别**: error。
- **autofix**: 是 (R2 推断规则见 `fixers.md`)。
- **检测**: 解析 yaml frontmatter, 对照 templates.md 中该 type 的必备集合; 缺一即一条 Violation, 字段名进 msg。

## R3 — 命名规则 (warn)

- **定义**: 三模块命名/层级约定权威见 `cortex-schema/references/knowledge-modules.md`。lint 只做形式检测:
  - 领域模块: 路径段数过少 (平铺到模块根) → 报警。
  - 脚本模块: basename 必须 kebab-case (小写 + 短横线)。
- **级别**: warn (重命名会断 wikilink, 不自动改, 仅提示)。
- **autofix**: 否。
- **检测**: 路径段计数 + basename 正则 `^[a-z0-9]+(-[a-z0-9]+)*\.\w+$`; 详细规则以 cortex-schema 为准。

## R4 — 目录同构 (error)

- **定义**: vault 根必须含齐必备目录。**必备目录清单由 `cortex-schema/references/topology.md` (顶层 + 三模块) + `cortex-schema/references/memory-levels.md` (memory 5 级) 共同定义**, 缺失则 R4 报 error + autofix mkdir。
- **级别**: error。
- **autofix**: 是 (mkdir, 见 `fixers.md`)。
- **检测**: `os.path.isdir` 对照上述权威源拼出的清单, 缺一报一条。

## R5 — 孤儿页 (warn)

- **定义**: 满足以下两条同时:
  - 无任何其它文件的 wikilink 指向自己 (basename / alias 均无入链)
  - 文件 mtime > 30 天
- **级别**: warn (可能是历史档案, 用户审批是否归档 / 删除)。
- **autofix**: 否。
- **检测**: 构建反向 wikilink 图 (R1 已建索引), 取入度=0 的节点, 再过 mtime 阈值。

## R6 — 等级语义一致 (error)

- **定义**: memory 路径段 `<N>-<suffix>` 必须与文件 frontmatter `level` 字段严格相等; 且 `<suffix>` 必须匹配权威映射; 反写直接 error。
- **级别**: error (语义反写会让整个记忆树检索失真)。
- **autofix**: 否 (用户决定是路径错还是字段错)。
- **权威映射**: 见 `cortex-schema/references/memory-levels.md` (含反写防呆清单)。
- **检测**: 正则抓 memory 路径段 + 读 frontmatter level, 与 memory-levels.md 映射表三方对照; 任何不在该表内的 `L*-*` 组合视为反写。

## R7 — 脚本目录用途分离 (warn)

- **定义**: 脚本用途分离权威见 `cortex-schema/references/knowledge-modules.md`。lint 落实检测:
  - 项目级 `<target>/.cortex/scripts/` 出现 → 报错 (项目脚本应入仓 `scripts/`, 不进 cortex)。
  - vault 内部脚本模块文件 frontmatter `type` 应为 `vault-script` 或缺省。
  - 路径写成英文 (非中文三模块名) 视为错位。
- **级别**: warn。
- **autofix**: 否。
- **检测**: 路径存在性 + frontmatter type 比对; 三模块中文名以 cortex-schema 为准。
