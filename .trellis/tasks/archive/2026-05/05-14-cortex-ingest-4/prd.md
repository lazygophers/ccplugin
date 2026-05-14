---
title: cortex ingest 最大细致度 — 函数/文件/模块/主题 4 层 + 全维度抽取
status: planning
priority: P2
owner: nico
created: 2026-05-14
---

# 背景

上一 task `05-14-cortex-ingest` 加了 §1.1 分级 + §4.7 覆盖度自检, 但仍是"目录级丰富 + 80% 文件覆盖"语义。

用户要求**最大细致度** — repo ingest 应**全方位抽取**:

- 粒度: 函数/类/接口 + 文件 + 模块/目录 + 主题 (4 层全做)
- 类别: 公开 API surface + 配置 schema + 错误码 + 测试用例 + 功能模块 + 全局变量/常量
- 排除: 严格白名单外 (node_modules/vendor/dist/build/locks/binary/.git/.venv 等 + 临时/备份/压缩包)

# 设计

改 `skills/cortex-ingest/SKILL.md` 强化 §1 + §4 + 加 §7 抽取维度清单 + §8 排除清单。`commands/ingest.md` 同步 self-check 加 4 层 + 6 类完备度检查。

## 1. SKILL.md §1.1 升级 — 4 层目录组织

按 repo 文件数分级, 但每级**强制 4 层目录** (不再是"≥6/10/20 .md" 单维度):

```
知识库/项目/<host>/<org>/<repo>/
├── _index.md                       # 主条目: 架构总览 + 全文件清单覆盖表 + 4 层导航
├── 主题/                           # 第 4 层 — 总览类 (强制 ≥ 4)
│   ├── 架构.md
│   ├── 决策.md
│   ├── 陷阱.md
│   ├── 依赖.md
│   └── (大 repo) API.md / 配置.md / 错误码.md / 测试.md
├── 模块/                           # 第 3 层 — 按 top-dir 拆 (≤50 文件可选, >50 强制)
│   ├── <top-dir-1>.md
│   ├── <top-dir-2>.md
│   └── ...
├── 文件/                           # 第 2 层 — 关键源文件 (≤50 全部, 50-500 选核心, >500 仅入口)
│   ├── <key-file-1>.md             # 一源文件 → 一 .md (职责/API/依赖/陷阱)
│   └── ...
└── 符号/                           # 第 1 层 — 函数/类/接口级 (公开 API 强制, 私有可选)
    ├── api/                        # public API surface 索引
    │   └── <module>-<symbol>.md   # 签名 + 摘要 + 调用例 + 调用方
    └── ...
```

| repo 文件数 | 最低产出 |
|---|---|
| ≤50 | `_index` + 主题/(≥4) + 模块/(可选) + 文件/(全部源码文件) + 符号/api/(全部 public API) — 总 ≥ **15 .md** |
| 50-500 | + 模块/(每 top-dir 1 .md) + 文件/(核心 50% 源码) + 符号/api/(全部 public) — 总 ≥ **40 .md** |
| >500 | + 模块/(每 top-dir + 二级 hot dir) + 文件/(每 entry point + 5+ 核心) + 符号/api/(全部 public + private hot) + API/配置/错误码/测试 各自独立 — 总 ≥ **100 .md** |

## 2. SKILL.md 新 §7 抽取维度清单 (6 类强制)

每个 repo ingest **必须**产出以下 6 类:

| # | 维度 | 落档 |
|---|------|------|
| 1 | **公开 API surface** (func/class/interface/exported var) | `符号/api/_index.md` (清单表) + `符号/api/<module>-<name>.md` (每入口 1 .md: 签名 + 摘要 + 调用例 + 调用方) |
| 2 | **配置 schema** (依赖名+版本 / scripts / env vars / build flags) | `主题/配置.md` (pyproject/package.json/Cargo.toml/go.mod 全字段) |
| 3 | **错误码 / 异常 / panic message** | `主题/错误码.md` (rg 抽 `errors\.New` / `raise` / `panic\(` / `throw` / 自定义 Error 类) |
| 4 | **测试用例** (input/expected) | `主题/测试.md` (rg 抽 test 函数, 列覆盖功能 + 关键 assert) |
| 5 | **功能模块清单** (用户视角的功能) | `主题/功能.md` (从 README features + cmd/ + 路由/handler 推) |
| 6 | **全局变量/常量** | `符号/常量.md` (rg 抽 `const` / `CONSTANT_CASE` / 模块级 var) |

self-check 加 6 类存在性验证 (缺即拒交)。

## 3. SKILL.md 新 §8 强制排除清单

ingest 前 build file tree **必须**排除:

```
排除规则 (find -prune):
- 构建产物: node_modules/ vendor/ dist/ build/ __pycache__/ target/ .next/ .nuxt/ out/
- Lock 文件: package-lock.json yarn.lock pnpm-lock.yaml go.sum Cargo.lock Pipfile.lock poetry.lock
- 二进制: *.{png,jpg,jpeg,gif,webp,svg,ico,mp4,mov,avi,mp3,wav,ttf,woff,woff2,eot,otf,pdf 除非 docs/}
- 系统/IDE: .git/ .venv/ .env/ .idea/ .vscode/ .DS_Store __MACOSX/ Thumbs.db
- 临时/备份: *.{bak,swp,tmp,old,orig,backup,~} *.swp.* .vscode-test/
- 压缩包: *.{zip,tar,gz,tgz,xz,bz2,rar,7z}
```

self-check 计 R (file count) 时**先剔除以上**, 再算 M/R ≥ 0.8。

## 4. commands/ingest.md self-check 升级

步骤 6 加:
- 4 层目录验证 (`ls 主题/ 模块/ 文件/ 符号/api/` 各非空)
- 6 类维度验证 (主题/{架构,决策,陷阱,依赖,配置,错误码,测试,功能}.md + 符号/api/ + 符号/常量.md 存在性)
- 排除清单先生效 (find -prune)
- 不通过: 拒交, 列缺哪类继续补

## 5. agents/cortex-researcher.md description 同步

description 加 "ingest 抽取强制 4 层 (主题/模块/文件/符号) + 6 类维度 (API/配置/错误码/测试/功能/常量)"

# 验收

1. SKILL.md §1.1 含 4 层目录结构 + 分级表 (≤50/50-500/>500 ≥15/40/100)
2. SKILL.md §7 抽取维度清单 6 类
3. SKILL.md §8 强制排除清单
4. commands/ingest.md self-check 步骤 6 升级含 4 层 + 6 类验证
5. agents/cortex-researcher.md 同步
6. GLM 自检 (CLAUDE.md §代码质量检查规范) 识别 "4 层" + "6 类" + "排除 node_modules"
7. pytest 314 pass

# 不做

- 不改 python `ingest_file.py` (抽取算法在 AI workflow 层)
- 不为单网页/单论文/单 PDF 加细致度 (仍单文件落档)
- 不强制 private API 全抽 (>500 才包含 hot private)

# 风险

- 中型 repo (50-500) ≥40 .md 是否过严? → 自检允许 "缺哪类继续补" 而非一次产出, AI 分批落档
- 函数级 .md 数量 (large repo 数千 public API) → 用 `符号/api/<module>/<name>.md` 二级目录避免单层 .md 爆炸
