# Design — cortex schema 单一真相源整合

## 内容归属重组

| 内容块 | 旧位置 | 新位置 (唯一) | 备注 |
| --- | --- | --- | --- |
| 三模块物理树 (项目/领域/脚本) | layout.md + schema-knowledge | **schema-knowledge** | 移除 layout 副本 |
| 5 级物理树 (L0-core ... L4-inbox) | layout.md + schema-memory | **schema-memory** | 同 |
| 双层同构原则 (~/.cortex/.wiki + <repo>/.wiki) | layout.md | **schema-knowledge** (主) + schema-memory 各引用 | 放 knowledge, memory 一句话引用 |
| 脚本目录用途分离 (顶层 scripts vs .wiki/脚本) | layout.md + schema-knowledge | **schema-knowledge/references/scripts.md** | 全部移走 |
| 开放扩展位 (~/.cortex/ 顶层) | layout.md | **schema-knowledge/references/topology.md (新)** | 顶层全局物理布局集中放这 |
| 顶层必备目录 (config/state/scripts/logs) | layout.md + validate-layout.sh | **schema-knowledge/references/topology.md** | validate-layout.sh 改注释引这 |
| 遗忘曲线速查 + 反直觉警告 | layout.md + schema-memory | **schema-memory** | 移走 layout 副本 |
| level↔dir 映射表 | lint references/rules.md (R6) | **schema-memory/references/levels.md** (或新 mapping 段) | 从 lint 迁来 |
| frontmatter 通用字段表 | layout.md | **schema-knowledge/references/templates.md (新)** | 含全字段速查表 |
| frontmatter 模板 (project/domain/rule/memory) | 散落 | **schema-knowledge/references/templates.md** | 集中 |

## 新增 references 文件

- `schema-knowledge/references/topology.md` — ~/.cortex/ 顶层布局 + 双层同构 + 开放扩展位
- `schema-knowledge/references/templates.md` — frontmatter 通用字段 + 各 type 模板

(其他 references 已存在: projects/domains/scripts)

## 删除文件

- `plugins/tools/cortex/docs/layout.md` — 全部内容迁完后删
- (可选) `plugins/tools/cortex/docs/` 目录如果空也删

## 引用契约

lint / extract / agent / scripts / README / llms.txt 引用 schema-* 时:

| 引用方 | 引用语句模板 |
| --- | --- |
| lint references/rules.md (R4 同构) | "必备目录清单见 `cortex-schema-knowledge/references/topology.md` (顶层) + `cortex-schema-memory/references/levels.md` (memory 5 级)" |
| lint references/rules.md (R6 等级) | "level↔dir 映射权威见 `cortex-schema-memory/references/levels.md`" |
| lint references/rules.md (R3 命名) | "三模块命名规则见 `cortex-schema-knowledge/references/{projects,domains,scripts}.md`" |
| extract references/classifier.md | "路由目标路径定义见 `cortex-schema-knowledge` + `cortex-schema-memory`" |
| agents/cortex.md | "目录契约权威: cortex-schema-knowledge + cortex-schema-memory skill" |
| validate-layout.sh 注释 | "必备目录定义见 cortex-schema-knowledge/references/topology.md" |
| README.md | 同上 |
| llms.txt | 同上 |

**绝不**在引用方重复列实际路径段; 仅给出权威源指针.

## SKILL.md 不动

4 skill SKILL.md (薄入口) 内容已 ≤ 60 行, 本 task 不重写 SKILL.md. 仅:
- 路径速查表保留 (≤ 1 行/模块, 详情指 references)
- 路由表新增 references (topology.md / templates.md / 等)

## 资源边界

| Subtask | 写资源 | 互斥 |
| --- | --- | --- |
| S1 | `skills/cortex-schema-knowledge/**` (含新增 topology.md / templates.md) | 无 |
| S2 | `skills/cortex-schema-memory/**` (含 levels.md 加映射段) | 无 |
| S3 | `skills/cortex-lint/references/**` | 无 |
| S4 | `skills/cortex-extract/references/**` | 无 |
| S5 | `docs/layout.md` (删) + `agents/cortex.md` + `README.md` + `llms.txt` + `scripts/validate-layout.sh` | 与 S1+S2 串行 (S5 依赖知道内容已迁完) |
| S6 | 只读 | 串行收口 |

S1//S2 并行 → S3//S4//S5 并行 → S6.

## 验证契约

S6 必跑:
1. `test ! -f plugins/tools/cortex/docs/layout.md`
2. `! grep -r "docs/layout.md" plugins/tools/cortex/`
3. `! grep -E "memory/L[0-9]-(core|long|mid|short|inbox)" plugins/tools/cortex/skills/cortex-lint/references/rules.md` (lint 不再硬列 memory 路径; 允许在测试命令示例里出现, 排除掉)
4. `! grep -E "项目/<host>|领域/<area>" plugins/tools/cortex/skills/cortex-extract/references/classifier.md` (extract 不再硬列)
5. `bash scripts/validate-layout.sh --target tests/fixtures/layout-ok/` 仍 rc=0
6. `bash scripts/lint.sh --check --target tests/fixtures/lint/` 行为同改前 (脚本逻辑未变)
7. 4 SKILL.md frontmatter 全合规 (description/wtu/arguments)

## Rollback

每 subtask 独立, 失败仅:
```bash
git checkout plugins/tools/cortex/<对应路径>/
```
