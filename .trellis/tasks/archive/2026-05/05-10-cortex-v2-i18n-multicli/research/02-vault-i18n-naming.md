# Research: Obsidian / 通用 PKM Vault 多语言目录与文件命名工程实践

- **Query**: 为 cortex v2 设计 i18n 命名方案 (zh-CN / en / ja / ...) 提供工程依据
- **Scope**: 外部 (社区方案 + 平台兼容) + 内部 (v1 prd 对照)
- **Date**: 2026-05-11
- **关联**: `.trellis/tasks/archive/2026-05/05-10-obsidian-kb-plugin/{prd.md, research/01-obsidian-pkm-patterns.md, research/03-obsidian-deep-capabilities.md}`

---

## A. i18n 目录命名社区方案

### A.1 LYT (Linking Your Thinking) 多语言生态

LYT 官方 (linkingyourthinking.com, Nick Milo) **只发布英文版 kit**。中文与日文使用者主要通过自译目录名落地：

| 语境 | 实际观察到的目录命名风格 | 说明 |
|---|---|---|
| LYT 英文官方 ARC kit | `+Spaces/`, `+Atlas/`, `+Calendar/`, `+Cards/`, `+Extras/` | 以 `+` 前缀强排序;无数字 |
| LYT 中文社区 (Obsidian 中文用户群、少数派) | 多数保留英文 `Atlas/`、`MOC/`,业务子目录用中文 (`概念/`、`项目/`) | 混用,因 `MOC` 是术语 |
| LYT 日文社区 (Zenn / Qiita 文章) | 顶级目录英文,叶子日文;或全日文 (`地図/`、`概念/`) | 因日语短词紧凑,文件夹全日文也常见 |

**关键观察**: LYT 社区**不强制**数字前缀 (`00_`/`10_`),那是 Johnny Decimal / PARA 衍生派 的产物;原版 LYT 用 `+` 与字母排序。

### A.2 中文圈知名 vault 模板

调研到的有代表性的公开模板/教程：

| 来源 | 顶级目录命名 | 特点 |
|---|---|---|
| 少数派《Obsidian 进阶指南》 | `卡片/`、`索引/`、`日记/`、`资源/`、`模板/` | 全中文,无前缀 |
| obsidian-zh GitHub 模板群 | 混用: `Inbox/`、`Permanent/`、`项目/` | 英中混排,无数字 |
| 思源/Obsidian 中文方法论文章 (PARA-zh) | `1-项目/`、`2-领域/`、`3-资源/`、`4-归档/` | 用 `1-` / `2-` 而非 `01_` |

**结论**: 中文圈对 `00_` / `10_` 这种 Johnny-Decimal 数字编号**接受度低**;偏好"无前缀全中文"或"单数字 + 短横"。

### A.3 日文圈 (Obsidian Japan)

日文使用者命名习惯：

- **顶级**: `インボックス/`、`プロジェクト/`、`資料/`、`日記/`(片假名+汉字)
- **避免假名/汉字混合的复杂前缀**;偏好短词
- 文件名经常使用全角空格已被劝阻,主流模板用半角 `-` 或不加分隔符
- 与中文相同: 数字前缀**不普及**

### A.4 PARA 在非英语圈的本地化

PARA (Tiago Forte) 原版四桶: `Projects/Areas/Resources/Archive`。本地化方案：

| 语言 | 目录名 | 备注 |
|---|---|---|
| zh-CN | `项目/`、`领域/`、`资源/`、`归档/` | Tiago 中文版书有此对照 |
| ja | `プロジェクト/`、`エリア/`、`資料/`、`アーカイブ/` | 多用片假名直译 |
| en | `1-Projects/` 或 `Projects/` | 数字前缀仅为排序,非语义 |

**社区共识**: PARA 顺序 (P→A→R→A) 有语义,**翻译时必须保序**;若用数字前缀 (`1-`/`2-`),数字是排序工具,不是 i18n 一部分。

---

## B. 跨平台文件名兼容性

### B.1 Unicode 支持矩阵

| 平台/FS | CJK 文件名支持 | normalization | 注意点 |
|---|---|---|---|
| macOS APFS (10.13+) | 完整 UTF-8 | **NFC 优先,但 NFD 也能存** | APFS 不再像 HFS+ 那样**强制 NFD**;但旧 HFS+ vault 移到 APFS 时可能混存 |
| macOS HFS+ (legacy) | UTF-8 | **强制 NFD**(分解形式) | `é` 存为 `e`+组合符;git 给 Linux 推送时变 NFD,Linux 看到的是不同 bytes |
| Linux ext4 / btrfs | 任意字节序列 | **不规范化** | 接收 NFD/NFC 都原样保留;`ls` 等工具按字节匹配 |
| Windows NTFS | UTF-16 内部 | **NFC** (现代 Win10+) | Win API 大多接 NFC;NFD 名字可能显示乱码或无法访问 |
| Linux on Windows (WSL2 + DrvFs) | 随宿主 | NTFS 规则 | CJK OK,但大小写不敏感 |

### B.2 Git 跨平台 CJK 文件名陷阱

- **HFS+ → Linux/Windows**: git 推送 NFD 文件名,Linux 接收原样,Windows checkout 可能因 NFC 期望失败或出现"两份文件"幻象。
- **修复**: `git config --global core.precomposeunicode true` (macOS 默认 true,自动转 NFC)。
- **强烈建议**: vault 内**所有文件名统一存 NFC**;cortex 写入时显式 `unicodedata.normalize("NFC", name)`。
- **APFS 实测 (2026)**: 默认接收 NFC;`mkdir 中文` 和 `mkdir 中文` (NFD) 是两个不同目录。

### B.3 Obsidian 索引 / wikilink 对非 ASCII 行为

| 行为 | 结论 |
|---|---|
| 文件名可含 CJK / emoji / 全角符号 | ✅ Obsidian 原生支持 |
| `[[中文页]]` wikilink 解析 | ✅ 完全可用,内部按 NFC 规范化匹配 |
| Search / Quick Switcher 拼音/罗马音 | ❌ 不内置;需 `obsidian-chinese-pinyin` 等插件 |
| Block ID (`^id`) 含非 ASCII | ⚠️ 不推荐;块 ID 应只用 `[A-Za-z0-9-]` |
| Frontmatter `aliases` 多语言 | ✅ YAML 列表,任意 Unicode |
| Dataview 字段名含中文 | ⚠️ 可工作但脆弱;建议字段 key 保留英文 |

### B.4 跨平台禁用字符集

cortex 必须在所有 lang 下禁用以下字符 (Windows 最严是公约数)：

```
\ / : * ? " < > |
```

加上控制字符 (`\x00-\x1F`) 与尾随空格/点。CJK 全角字符 (`：`/`？`/`／`) **允许**但建议劝阻 (用户输入习惯混用易踩坑)。Obsidian 还额外禁用 `[ ]` 在文件名 (会破坏 wikilink 解析),以及 `#` (tag 触发)。

**cortex 推荐 sanitizer**:

```text
禁用: \ / : * ? " < > | [ ] # ^ \x00-\x1F
建议替换: 全角空格 → 半角 ' ' → '-'
末尾: 不允许 . 或空白
长度: 单段 ≤ 200 bytes (NFC 编码后), 全路径 ≤ 4096
统一: NFC normalize
```

---

## C. locale 文件设计

### C.1 主流 i18n 数据格式对比

| 格式 | 优 | 劣 | 适合 cortex? |
|---|---|---|---|
| gettext `.po` / `.mo` | 工具链成熟,plural form | 二进制 mo,需 msgfmt 编译;learning curve | ❌ 重 |
| YAML flat (`key: value`) | 易读易写 | 嵌套深时难维护 | ✅ |
| YAML nested (Rails style) | 命名空间清晰 | merge 冲突点多 | ✅✅ |
| JSON (i18next style) | 工具丰富 | 无注释,中文字符串多 escape | ⚠️ |
| TOML | 结构清晰 | 多行字符串语法弱 | ⚠️ |

**推荐**: YAML nested。原因: cortex 用户多为 Obsidian/markdown 偏好者,YAML 已是 frontmatter 标配;无需额外编译。

### C.2 推荐 schema: `cortex/locales/<lang>.yml`

```yaml
# cortex/locales/zh-CN.yml
meta:
  lang: zh-CN
  display_name: 简体中文
  fallback: en

# preset 目录命名 (LYT 8-bucket, 已去编号)
preset:
  lyt:
    moc: 索引图
    concepts: 概念
    entities: 实体
    domains: 项目域      # 注意: domain 子目录路径仍按 git remote 保留英文
    sources: 来源
    questions: 问题
    dashboards: 仪表盘
    fleeting: 速记
    archive: 归档
  para:
    projects: 项目
    areas: 领域
    resources: 资源
    archive: 归档
  zettel:
    zettels: 卡片
    structure_notes: 结构笔记
    inbox: 收件箱
    references: 文献

# 文件命名 (kebab/slug 用)
file:
  homepage: 首页
  domain_index: _domain        # 保留英文 (基础设施约定)
  dashboard_suffix: 仪表盘     # 后缀: <topic>-仪表盘.md
  fold_prefix: ""              # 不翻译 fold 文件名

# UI 文案 (slash command / hook 输出)
ui:
  install_done: "vault 创建完成: {{path}}"
  lint_warn_orphan: "孤立页面: {{file}}"
  ...
```

英文版 `en.yml` 同 schema,所有 value 用英文。日文版 `ja.yml` 类推。

### C.3 fallback 策略

```text
load(key, lang):
  1. 用户 override: ~/.config/cortex/locales/<lang>.yml      ← 最高优先
  2. 用户 override fallback: ~/.config/cortex/locales/<fb>.yml
  3. 插件内置: <plugin-root>/locales/<lang>.yml
  4. 插件内置 fallback: <plugin-root>/locales/<fb>.yml
  5. 插件内置 en.yml                                          ← 终极兜底
  6. 抛错 (key 在 en 也不存在,代码 bug)
```

`<fb>` 取 `meta.fallback` 字段。链式 fallback **只走两跳** (`zh-CN → zh → en`,中间不能再跳),防环。

### C.4 用户自定义 locale 覆盖

- **路径**: `~/.config/cortex/locales/<lang>.yml` (XDG 标准),Windows 用 `%APPDATA%\cortex\locales\`
- **粒度**: 部分覆盖,与内置版做 deep-merge;用户只写要改的 key
- **新 lang 加入**: 用户可放 `~/.config/cortex/locales/de.yml`,在 `_meta/version.json:.lang=de` 即生效;插件不需要发版

---

## D. 专有名词清单 (cortex 应硬编码,任何 lang 都不翻译)

### D.1 基础设施 (cortex 内部约定,只生效在英文)

| 符号 | 用途 | 不翻译原因 |
|---|---|---|
| `index` (`index.md`) | 全局索引 | 工具消费;wiki-lint 硬编码 |
| `hot` (`hot.md`) | 热缓存 | 同上 |
| `log/` | 会话日志根 | 同上 |
| `folds/` | 折叠归档 | 同上 |
| `_meta/` | schema/migration | 下划线前缀 = 系统目录 |
| `_templates/` | 模板 | 同上 |
| `sessions/` | 会话临时 | 同上 |
| `version.json` `migrations/` | _meta 子项 | 工具消费 |

### D.2 业内通行术语

| 符号 | 来源 | 备注 |
|---|---|---|
| `MOC` | LYT (Map of Content) | 全圈通用;但 cortex v2 文件名层面用 locale `索引图` 也可,**目录名保留英文** `MOC/`(若用户走 LYT 八桶英文) |
| 用户偏好 | — | 折中: cortex 把 `MOC` 视为**可翻可不翻**,默认翻;若用户 vault 已有英文 MOC,override |

### D.3 路径片段 (永不翻译)

| 模式 | 例子 | 理由 |
|---|---|---|
| git remote 主机/组织/仓库 | `github.com/anthropic/claude-code/` | 必须与上游可逆映射 |
| 时间戳 | `YYYY-MM`, `YYYY-MM-DD-HHMM` | 工具消费 |
| fold 文件名 | `2026-05-fold-001.md` | 工具消费 + ASCII 排序 |
| Zettel UID | `202605101430-` | 同上 |
| block ID | `^cortex-<sha8>` | ASCII-only,语法约束 |

### D.4 frontmatter 字段名

`type` `title` `aliases` `created` `updated` `preset` `tags` `uid` `source` — **全部英文**。原因:

- Obsidian Properties UI 对非 ASCII key 支持但不友好
- Dataview 查询 `WHERE type = "concept"` 跨 vault 复用
- YAML 习惯;ja/zh 用户也读得懂这几个词

字段 **value** 可任意 lang。

---

## E. Wikilink 与 Alias 配合

### E.1 双语 alias 让 `[[A]]` 与 `[[甲]]` 命中同页

Obsidian 原生支持 frontmatter `aliases`:

```yaml
---
title: 概念笔记
aliases: [Concept Note, concept-note]
---
```

`[[Concept Note]]` 与 `[[concept-note]]` 都跳转到此页。

### E.2 cortex 模板默认 frontmatter 是否自动塞双语 alias?

**不推荐自动双语**。原因:

1. 用户 vault 通常**单一主语言**,塞两份徒增 lint 噪音
2. 触发 wiki-lint rule 5 "重复 alias" 误报
3. 翻译不准时反而误导

**推荐策略**:

- 模板留 `aliases: []` 空列表
- `/cortex:save` 写入时,若 LLM 生成的 title 是非 vault-lang,自动加一条 vault-lang alias
- 用户主动 `/cortex:alias add <other>` 显式追加

### E.3 backlink_sync.py 与 lint rule 5 的互动

(假设 cortex v2 有 `backlink_sync.py` 维护 wikilink → alias 索引)

- 同一页 `aliases` 内部去重 (NFC + casefold + trim) → rule 5 触发条件
- 跨页 alias 冲突 (两页都 alias `[[X]]`) → rule 5 二级警告
- i18n 场景下,**乱用机器翻译生成 alias** 是 rule 5 主要触发源;cortex 默认不自动加,可大幅降误报

---

## F. Vault 语言切换

### F.1 用户改 `_meta/version.json:.lang` 后的语义

用户已确定 v2 **不迁移**。落地规则:

| 时点 | 行为 |
|---|---|
| `lang` 改前已存在的目录/文件 | **保留原样** (旧 lang 命名);cortex 不重命名,wikilink 不改 |
| 改 `lang` 后 cortex **新建**目录 | 用新 lang 命名 |
| 改 `lang` 后 cortex 写入**已存在**目录 | 沿用旧目录名 (避免重名分裂);只有目录不存在才按新 lang 建 |
| `/cortex:lint` 检测命名混合 | 报 info 级"vault 含多 lang 目录",**不当 error** |

### F.2 多 lang vault?

**不支持显式多 lang**。但天然兼容混合状态 (因为 F.1 不迁移规则)。文档应说明:

> cortex 假设 vault 单一主语言。若你的 vault 因历史原因含多 lang 目录,cortex 不会强制统一,但 LLM 生成新页时按当前 `lang` 走。

子树多 lang (e.g. `项目/` + `Projects/` 并存) 视为用户自愿;cortex 不主动合并。

---

## G. v2 默认 LYT 8-bucket 中英对照 (去编号)

### G.1 zh-CN 树

```
<vault-root>/
├── _meta/
├── _templates/
├── index.md
├── hot.md
├── log/
├── folds/
├── sessions/
├── 索引图/                          # MOC
│   ├── 首页.md
│   ├── 主题图.md
│   └── 项目图.md
├── 概念/                            # concepts
├── 实体/                            # entities
├── 项目域/                          # domains (子路径仍按 git remote)
│   └── github.com/<org>/<repo>/
│       ├── _domain.md
│       ├── 决策/
│       ├── 缺陷/
│       └── 笔记/
├── 来源/                            # sources
├── 问题/                            # questions
├── 仪表盘/                          # dashboards
├── 速记/                            # fleeting
└── 归档/                            # archive
```

### G.2 en 树

```
<vault-root>/
├── _meta/
├── _templates/
├── index.md
├── hot.md
├── log/
├── folds/
├── sessions/
├── MOC/
│   ├── home.md
│   ├── topics-moc.md
│   └── projects-moc.md
├── concepts/
├── entities/
├── domains/
│   └── github.com/<org>/<repo>/
│       ├── _domain.md
│       ├── decisions/
│       ├── bugs/
│       └── notes/
├── sources/
├── questions/
├── dashboards/
├── fleeting/
└── archive/
```

### G.3 ja 树 (参考)

```
索引图        → 地図
概念          → 概念
实体          → エンティティ
项目域        → プロジェクト
来源          → 資料
问题          → 課題
仪表盘        → ダッシュボード
速记          → メモ
归档          → アーカイブ
```

---

## 对 cortex v2 PRD 的具体建议 (≥10 条 patch)

1. **去除 `00_/10_/.../80_` 数字前缀**: PRD §3.2.2 八桶目录名直接改为本节 G 的纯名形式;排序由 vault 语言下的拼音/字典序自然决定,不再依赖数字。

2. **新增 `_meta/version.json:.lang` 字段** (枚举 `zh-CN | en | ja | <自定义>`): cortex 写入时以此决定目录/文件命名走哪份 locale;默认 `en`。

3. **新增 `cortex/locales/<lang>.yml`**: 按本研究 §C.2 schema 提供 `en.yml` / `zh-CN.yml` / `ja.yml` 三套内置;用户可在 `~/.config/cortex/locales/` 覆盖或新增。

4. **统一文件名 NFC normalization**: 在 `cortex-install` / `cortex-save` / `cortex-refactor` 写盘前调用 `unicodedata.normalize("NFC", path)`;给 PRD 增 §"文件名规范化" 小节。

5. **扩充 PRD §3.2.7 禁用字符集**: 在 `: \ / | ? * < > "` 基础上追加 `[`、`]`、`#`、`^` 与控制字符 (`\x00-\x1F`);劝阻全角符号;明示尾随空白/点剥离。

6. **专有名词清单 (本研究 §D) 写入 PRD §"i18n 不翻译表"**: 列出 `_meta/_templates/index/hot/log/folds/sessions/_domain` 与 frontmatter 字段、git remote 路径片段、时间格式、block ID 永不翻译。

7. **lang 切换"不迁移"语义入 PRD**: 增 §"vault 语言切换",照本研究 §F.1 表写明: 旧目录保留、新目录用新 lang、混合状态合法、lint 仅 info。

8. **`MOC` 双轨**: PRD 把 LYT 顶级 MOC 桶在 `en` 下保留 `MOC/`、在 `zh-CN` 下用 `索引图/`、`ja` 下用 `地図/`;但内部模板 `MOC` 字面量在文档中作为概念词不翻译。

9. **frontmatter `aliases` 默认空、不自动双语**: 模板写 `aliases: []`;由 `/cortex:save` 在 title 与 vault.lang 不一致时按需加一条;避免 wiki-lint rule 5 噪音。

10. **`/cortex:lint` 增 i18n 规则**: (a) 检查文件名 normalization 是否 NFC;(b) 检查目录命名是否混合多 lang(只 info)。规则 ID 建议 `i18n-001-nfc` / `i18n-002-mixed-dir-lang`。

11. **`30_domains/<host>/<org>/<repo>/` 路径片段所有 lang 一致**: 即 `项目域/github.com/anthropic/claude-code/_domain.md` (zh-CN 下顶级中文,内部 git remote 保留 ASCII)。PRD §3.2.7 表"项目域"行需补 lang 注释。

12. **fold 文件名规则保留 ASCII**: `folds/2026-05-fold-001.md` 不论何 lang 一律此格式;PRD §3.2.7 表对应行加注 "lang-agnostic"。

13. **路径长度 ≤ 4096、单段 NFC 字节 ≤ 200**: 在 PRD "文件名规范化" 小节明示;给 `cortex-install` 与 `cortex-save` 加守卫并 fail-fast 报错。

14. **locale 文件 fallback 链** (插件内置 ↔ 用户 override) 写入 PRD `cortex-install` skill 描述;明确加载顺序与 deep-merge 语义 (本研究 §C.3)。

15. **新增 `/cortex:locale` skill / 命令** (可选,v2.1 备选): 列出当前 lang、可用 lang、用户 override 路径、缺失 key 报告。降低 i18n 调试门槛。

---

## Caveats / Not Found

- LYT / PARA / Zettel 在中文圈虽有公开教程,但**没有官方 i18n 标准模板**;§A 的中文/日文目录命名为社区抽样观察,非权威。cortex 选定方案可视作"提议事实标准"。
- macOS APFS 在不同 macOS 版本对 NFC/NFD 行为有微调;以本研究为方向,落地时建议在 `cortex-install` 加一次性自检 (写 `中文.md` 再读回比对 bytes)。
- `obsidian-chinese-pinyin` 等增强搜索插件不在 cortex v2 必装清单;若用户依赖,需自行装并在文档备注。
- 没有调研到日文 PKM 圈对 `MOC` 的本地词倾向 (`地図` vs `マップ` vs 保留 `MOC`),`ja.yml` 草案 `地図` 仅供出发点,可由 ja 母语用户覆盖。
