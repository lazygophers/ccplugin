# 7 规则详情 (R1-R7)

每条规则: 定义 / 级别 / 是否 autofix / 检测策略。

## R1 — wikilink 死链 (warn)

- **定义**: `[[X]]` 必须能解析到 vault 内某个 `.md` 文件名 (basename, 去 `.md`) 或某文件 frontmatter 的 `aliases` 列表项。
- **级别**: warn (死链不能猜, 由用户决定建页 / 删链 / 改名)。
- **autofix**: 否。
- **检测**: 遍历所有 `.md`, 正则抓 `[[([^\]|#]+)`, 与全局 `name → file` 索引比对; aliases 也注入索引。

## R2 — frontmatter 必备字段 (error)

- **定义**: 每个 `.md` 的 frontmatter 必须含:
  - `type` (恒必填)
  - `domain` 类: 还要有 `area`
  - `rule` / `memory` 类: 还要有 `level`
  - `project` 类: 还要有 `source`
- **级别**: error。
- **autofix**: 是 (R2 推断规则见 `fixers.md`)。
- **检测**: 解析 yaml frontmatter, 比对必备字段集合; 缺一即一条 Violation, 字段名进 msg。

## R3 — 命名规则 (warn)

- **定义**:
  - `领域/<area>/...`: 至少 2 级 (area + 文件), 不允许 `领域/foo.md` 平铺。
  - `脚本/...`: 文件名 kebab-case (小写 + 短横线), 不允许 `BadCamelCase.sh` / `snake_case.py`。
- **级别**: warn (重命名会断 wikilink, 不自动改, 仅提示)。
- **autofix**: 否。
- **检测**: 路径段计数 + basename 正则 `^[a-z0-9]+(-[a-z0-9]+)*\.\w+$`。

## R4 — 目录同构 (error)

- **定义**: vault 根必须含齐:
  - `memory/L0-core/` `memory/L1-long/` `memory/L2-mid/` `memory/L3-short/` `memory/L4-inbox/`
  - `项目/` `领域/` `脚本/` (中文三模块目录)
- **级别**: error。
- **autofix**: 是 (mkdir, 见 `fixers.md`)。
- **检测**: `os.path.isdir` 对照清单, 缺一报一条。

## R5 — 孤儿页 (warn)

- **定义**: 满足以下两条同时:
  - 无任何其它文件的 wikilink 指向自己 (basename / alias 均无入链)
  - 文件 mtime > 30 天
- **级别**: warn (可能是历史档案, 用户审批是否归档 / 删除)。
- **autofix**: 否。
- **检测**: 构建反向 wikilink 图 (R1 已建索引), 取入度=0 的节点, 再过 mtime 阈值。

## R6 — 等级语义一致 (error)

- **定义**: `memory/L<N>-<suffix>/` 路径段中 `<N>` 必须与文件 frontmatter `level` 字段严格相等; 且 `<suffix>` 必须匹配权威映射 (见下); 反写直接 error。
- **级别**: error (语义反写会让整个记忆树检索失真)。
- **autofix**: 否 (用户决定是路径错还是字段错)。
- **权威映射**:
  | 路径段 | level 必须 |
  | --- | --- |
  | `memory/L0-core/` | `L0` |
  | `memory/L1-long/` | `L1` |
  | `memory/L2-mid/` | `L2` |
  | `memory/L3-short/` | `L3` |
  | `memory/L4-inbox/` | `L4` |
- 任何其它形如 `memory/L*-*/` (如 `L1-short` / `L3-long`) 都视为反写。
- **检测**: 正则抓路径段 + 读 frontmatter level, 三方对照。

## R7 — 脚本目录用途分离 (warn)

- **定义**:
  - 项目级 `<target>/.cortex/scripts/` 出现 → 报错 (项目脚本应入仓 `scripts/`, 不进 cortex)。
  - vault 内部 `<root>/.wiki/脚本/` 内文件 frontmatter `type` 应为 `vault-script` 或缺省。
  - 路径写成英文 `<root>/.wiki/scripts/` 视为错位 (中文三模块约定)。
- **级别**: warn。
- **autofix**: 否。
- **检测**: 路径存在性 + frontmatter type 比对。
