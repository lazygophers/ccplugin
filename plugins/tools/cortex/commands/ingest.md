---
description: 深度分析当前目录摄取到 cortex vault (无入参; 自动识别 git repo / 普通项目)
---

# /cortex:ingest

[AUTO_MODE persistent: 禁询问, 禁中止, AI 自决执行]

**默认行为**: 深度分析**当前工作目录** ($PWD) 摄取到 cortex vault。

## 强制流程

1. 从 `~/.cortex/config.json` 读 `vault`
2. **判定目录类型** (按下表自决, 禁问):

   | 检测 | 类型 | 落档位置 |
   |------|------|---------|
   | `git remote get-url origin` 命中 `github.com[:/]<org>/<repo>` | **项目** | `知识库/项目/github.com/<org>/<repo>/{_index, 架构, 决策, 陷阱, 依赖, 笔记/, 决策/}` |
   | origin 命中 `gitlab.com` / 自建 GitLab (host 含 `gitlab`) | **项目** | `知识库/项目/<host>/<org>/<repo>/...` (同上结构) |
   | 有 `.git` 但 origin 非 github/gitlab | **项目** | `知识库/项目/<rel-host>/<rel-org>/<rel-repo>/...` (相对 $HOME 路径拆段, 不足 3 段补 `_local`) |
   | 无 `.git`, 有 `pyproject.toml` / `package.json` / `Cargo.toml` / `go.mod` | **项目** | 同上策略 |
   | 其余 (普通目录兜底) | **项目** | `知识库/项目/<rel-host>/<rel-org>/<rel-repo>/_index.md` (同上策略) |

3. **嵌套 git repo 检测** (强制):
   - `find $PWD -name .git -type d -not -path '*/node_modules/*'` 列全部 git repo
   - 若 ≥ 2 个 (父+子), **每个独立 ingest** 一份, 不合并, 不忽略
   - 顺序: 父先, 嵌套后, 各自落自己的 `知识库/项目/<host>/<org>/<repo>/`

4. **深度分析** (L1-L6 全做, 不允许跳层, 详见 cortex-ingest SKILL §4 深度处理):
   - L1 结构: `find -maxdepth 5` 全树
   - L2 文档: Read 全部 README*.md / docs/**.md / CHANGELOG / CONTRIBUTING / spec/*
   - L3 配置: Read pyproject/package.json/Cargo.toml/go.mod/Makefile/Dockerfile/CI
   - L4 入口码: Glob 语言入口 (main.* / index.* / app.* / cmd/**), Read 核心 50 行
   - L5 历史: `git log --oneline -50` + `git log --stat`, 关键 commit 提炼决策
   - L6 派生: 综合产出**目录主条目 index.md + ≥ 4 个子文档** (architecture / decisions / pitfalls / dependencies, 仓库越大子文档越多)

5. **落档** (强 folder-first; 详见 cortex-ingest SKILL §1 文件夹优先 + §3 强制 frontmatter):
   - git repo (github/gitlab/local) → `知识库/项目/<host>/<org>/<repo>/_index.md` + 子文档 (架构 / 决策 / 陷阱 / 依赖 / 笔记/ / 决策/)
   - 普通项目 (无 git 或私服 git) → `知识库/项目/<rel-host>/<rel-org>/<rel-repo>/_index.md` (相对 $HOME 路径拆段) + 子文档
   - frontmatter 必填: type / title / desc / created / updated / tags (≥10, 严禁占位) / source_url / version / when_to_read / score (1-5) / maturity (详见 SKILL §3)
   - tags 必含: `source/<kind>` + `topic/<domain>` + `stack/<lang>` (详见 SKILL §6)

6. **落档自检** (强制, 不通过则继续补, 严禁直接报告):

   ```bash
   ROOT="<落档根路径>"   # 知识库/项目/<host>/<org>/<repo>
   ALL_MD=$(find "$ROOT" -name '*.md' | wc -l)                                                   # 全部 .md
   TOPIC_N=$(ls "$ROOT/主题/" 2>/dev/null | grep -c '\.md$')
   MOD_N=$(ls "$ROOT/模块/" 2>/dev/null | grep -c '\.md$')
   FILE_N=$(ls "$ROOT/文件/" 2>/dev/null | grep -c '\.md$')
   SYM_API_N=$(find "$ROOT/符号/api/" -name '*.md' 2>/dev/null | wc -l)
   # R 先应用 §8 排除清单 (build 产物 / lock / 二进制 / 系统 IDE / 临时 / 压缩包) 再算
   R=$(find $PWD -type f \
        -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/vendor/*' \
        -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/__pycache__/*' \
        -not -path '*/target/*' -not -path '*/.venv/*' -not -path '*/.next/*' \
        -not -name '*.lock' -not -name 'package-lock.json' -not -name 'yarn.lock' \
        -not -name 'pnpm-lock.yaml' -not -name 'go.sum' -not -name 'Cargo.lock' \
        -not -name '*.png' -not -name '*.jpg' -not -name '*.jpeg' -not -name '*.gif' \
        -not -name '*.webp' -not -name '*.svg' -not -name '*.ico' \
        -not -name '*.mp4' -not -name '*.mov' -not -name '*.mp3' -not -name '*.wav' \
        -not -name '*.ttf' -not -name '*.woff*' -not -name '*.eot' -not -name '*.otf' \
        -not -name '*.zip' -not -name '*.tar' -not -name '*.gz' -not -name '*.tgz' \
        -not -name '*.bak' -not -name '*.swp' -not -name '*.tmp' \
        -not -name '.DS_Store' \
        | wc -l)
   M=$(grep -rhoE '`[^`]+\.[a-zA-Z0-9]+`|\[\[[^]]+\]\]' "$ROOT/" | sort -u | wc -l)              # 落档主体引用文件数
   ```

   a. **4 层目录验证** (各非空): `主题/` ≥ 4 .md + `文件/` ≥ 1 .md + `符号/api/` ≥ 1 .md (含 `_index.md`); 若 R > 50 则 `模块/` ≥ 1 .md
   b. **6 类维度验证** (缺即拒交):
      - `主题/架构.md` `主题/决策.md` `主题/陷阱.md` `主题/依赖.md` (基础 4 类, 强制)
      - `主题/配置.md` (配置 schema) / `主题/错误码.md` (异常 panic) / `主题/测试.md` (测试用例) / `主题/功能.md` (功能模块)
      - `符号/api/_index.md` (公开 API surface 清单)
      - `符号/常量.md` (全局常量)
   c. `ALL_MD ≥ 下限`: R ≤ 50 ⇒ ≥ 15 / 50 < R ≤ 500 ⇒ ≥ 40 + `模块/`强制 / R > 500 ⇒ ≥ 100 + `主题/{API,配置,错误码,测试}` 各独立
   d. `M / R ≥ 0.8` (主体引用覆盖 ≥ 80%, R 已 prune 排除清单; 详见 cortex-ingest SKILL §4.7 + §8)
   e. `_index.md` 含 "4 层导航表" + "文件清单覆盖" 表 (全 file path → cover_doc)
   f. 不通过: 列**缺哪层** (主题/模块/文件/符号) + **缺哪类** (API/配置/错误码/测试/功能/常量) → 补对应子文档 → 重测; 严禁直接跳到步骤 7
   g. **§9 知识图谱 4 类强制验证** (详见 cortex-ingest SKILL §9; 跳一类 = 拒交, websearch 仅 warn):

   ```bash
   # 9.1 Bases 数据库视图
   [[ -f "$ROOT/_db.base" ]] || { echo "FAIL: 缺 _db.base, 见 SKILL §9.1 模板"; exit 1; }

   # 9.2 Canvas 白板
   REPO_NAME=$(basename "$ROOT")
   CANVAS="$ROOT/_assets/canvases/$REPO_NAME.canvas"
   [[ -f "$CANVAS" ]] || { echo "FAIL: 缺 $CANVAS, 见 SKILL §9.2"; exit 1; }
   NODES=$(grep -c '"id"' "$CANVAS" 2>/dev/null || echo 0)
   [[ $NODES -ge 5 && $NODES -le 20 ]] || echo "WARN: canvas 节点数 $NODES 不在 5-20"

   # 9.3 Wikilink 网密度 (小 repo R ≤ 50 prorated ≥ 3, 否则 ≥ 5)
   MIN_LINKS=$([[ $R -le 50 ]] && echo 3 || echo 5)
   FLAG=0
   for md in $(find "$ROOT" -name '*.md'); do
     links=$(grep -c '\[\[' "$md" 2>/dev/null || echo 0)
     [[ $links -ge $MIN_LINKS ]] || { echo "FLAG wikilink<$MIN_LINKS: $md ($links)"; FLAG=1; }
   done
   [[ $FLAG -eq 0 ]] || { echo "FAIL: wikilink 密度不足, 补再测"; exit 1; }

   # 9.4 websearch 扩展 (容忍跳过, 仅 warn)
   [[ -f "$ROOT/主题/外部资料.md" ]] || echo "WARN: 主题/外部资料.md 未补 (websearch 跳过可接受)"
   ```

7. 摄取完成后 **直接给最终报告** (无问句):

   ```
   target_type: <repo|project>
   location: <落档根路径>
   files_ingested: <N>
   main_doc: <主条目路径>
   sub_docs: [<路径>, ...]
   ```

## 显式 args 走传统路径

若 wrapper 异常带入 args (url / file / git url / 远程 dir 等): auto-detect 类型, 按 cortex-ingest SKILL 标准流程处理 (url_security → fetch → html_sanitize → masking → save)。

## AUTO_MODE (shell wrapper 触发, persistent)

**核心原则**: "禁问" ≠ "中止". AI 必须**自决并执行直至任务完成**。遇歧义按推荐默认值执行; 工具不熟悉则尝试其他工具组合 (Bash/Edit/Write/MCP/WebSearch/WebFetch/Read 现有样本); 禁报"需人工"/"AI 不会"/"建议后续处理"。

### 严禁 (任一出现 = 契约违反)

| # | 禁止 |
|---|------|
| 1 | 任何"修复建议"/"建议"/"推荐操作" 章节/表格/列表 (`## 修复建议`, `\| 类型 \| 操作 \|`) |
| 2 | 用户确认问句 (`需确认?`, `是否执行?`, `要继续吗?`, `ok?`, 末尾问号) |
| 3 | AskUserQuestion 调用 (allowed-tools 已禁) |
| 4 | "下一步"/"后续"/"如需"/"可选" 导引 |
| 5 | "需人工"/"待人工"/"建议人工" 推卸辞令 |
| 6 | "AI 能力不足"/"无法自动" 类借口 |
| 7 | 报状态后停 (除非工具客观失败: 磁盘只读/权限拒绝/git lock) |
