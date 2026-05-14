# cortex-ingest — 目录布局 + 分级评分

> SKILL.md §1.1 (4 层目录) / §1.2 (拒交硬条件) / §5 (分级评分制度) 的详细规范。

---

## 1.1 4 层目录组织 (最大细致度, 强制)

落档 `知识库/项目/<host>/<org>/<repo>/` 必按 **4 层粒度**铺开 — 主题 / 模块 / 文件 / 符号, 各层为独立子目录:

```
知识库/项目/<host>/<org>/<repo>/
├── _index.md                       # 主条目: 架构总览 + 全文件清单覆盖表 + 4 层导航
├── 主题/                           # 第 4 层 — 总览类 (强制 ≥ 4)
│   ├── 架构.md
│   ├── 决策.md
│   ├── 陷阱.md
│   ├── 依赖.md
│   └── (大 repo) 配置.md / 错误码.md / 测试.md / 功能.md / API.md
├── 模块/                           # 第 3 层 — 按 top-dir 拆 (≤50 可选, >50 强制)
│   ├── <top-dir-1>.md
│   └── ...
├── 文件/                           # 第 2 层 — 关键源文件 (一文件 → 一 .md)
│   ├── <key-file-1>.md             # 职责 / API / 依赖 / 陷阱
│   └── ...
└── 符号/                           # 第 1 层 — 函数/类/接口级
    ├── api/                        # public API surface
    │   ├── _index.md               # 清单表
    │   └── <module>-<symbol>.md    # 每入口 1 .md: 签名 + 摘要 + 调用例 + 调用方
    └── 常量.md                     # 全局变量 / 模块级 const
```

按 repo 文件数 R (按 `references/exclude.md` 排除清单 prune 后) 分级, 每级**最低产出**:

| repo 文件数 R | **强制 .md 下限** | 必产 4 层 |
|---|---|---|
| R ≤ 50 | **≥ 15 .md** | `_index` + 主题/(≥4) + 模块/(可选) + 文件/(**全部源码文件**) + 符号/api/(**全部 public API**) |
| 50 < R ≤ 500 | **≥ 40 .md** | 同上 + 模块/(每 top-dir 1 .md, 强制) + 文件/(核心 ≥50% 源码) + 符号/api/(全部 public) |
| R > 500 | **≥ 100 .md** | 同上 + 模块/(每 top-dir + 二级 hot dir) + 文件/(每 entry point + 5+ 核心) + 符号/api/(全部 public + private hot) + 主题/{API,配置,错误码,测试} 各独立 |

R 取自 `find <repo> -type f` 应用排除规则 (`-prune`) 后的计数。

`_index.md` = 主条目 (架构总览 + **4 层导航表** + **全文件清单覆盖表**); 各子目录 .md = 细节深挖。**禁止**把整个仓库压一个文件, 也不允许只铺一层 (例如只有 主题/ 缺 文件/ 符号/)。

> large repo 符号级 .md 数千个时, `符号/api/` 改二级目录 `符号/api/<module>/<name>.md` 避免单层 .md 爆炸。

---

## 1.2 拒交硬条件 (落档后必 verify, 不通过则继续补, 严禁提交)

```bash
ROOT="知识库/项目/<host>/<org>/<repo>"
ALL_MD=$(find "$ROOT" -name '*.md' | wc -l)            # 全部 .md (含子目录)
TOPIC_N=$(ls "$ROOT/主题/" 2>/dev/null | grep -c '\.md$')
MOD_N=$(ls "$ROOT/模块/" 2>/dev/null | grep -c '\.md$')
FILE_N=$(ls "$ROOT/文件/" 2>/dev/null | grep -c '\.md$')
SYM_N=$(find "$ROOT/符号/api/" -name '*.md' 2>/dev/null | wc -l)
```

- 4 层非空: `主题/` ≥ 4 + `文件/` ≥ 1 + `符号/api/` ≥ 1 (含 `_index.md`); R > 50 时 `模块/` ≥ 1
- `ALL_MD < 下限` (15 / 40 / 100 按 §1.1) → 拒交, 继续补
- 只有 `_index.md` 或只有主层 (无 4 层子目录) → **视为偷工, 直接拒交**
- 6 类抽取维度缺任一 (见 `references/extract.md` §7) → 拒交, 补对应维度
- 不达标禁止给用户最终报告, AI 必须自决继续补直至通过

---

## 5. 分级评分制度

每个 ingest 落档需评:

| 维度 | 取值 | 规则 |
|------|------|------|
| `score` (质量) | 1-5 | 5=权威官方 / 高 star (>10k) / 主流标准; 4=活跃维护 / >1k star; 3=有维护 / 普通; 2=个人项目 / 实验性; 1=废弃 / 不推荐 |
| `maturity` | draft / review / stable / deprecated | 按上游 release 状态或 README 标注判定; 含 `pre-alpha` / `WIP` → draft; 有 release / 有版本号 → stable; archived → deprecated |
| `tags[关注度]` | freq/<high\|mid\|low> | 自动: 含 README badges (CI/coverage/downloads) + commit 近 30 天频率, 按 `bash ~/.cortex/scripts/search.sh` 命中次数定 |

`score` + `maturity` 写入 frontmatter; freq tag 自动追加。lint 规则 `frontmatter-schema-violation` 强制存在性 (缺即 error)。
