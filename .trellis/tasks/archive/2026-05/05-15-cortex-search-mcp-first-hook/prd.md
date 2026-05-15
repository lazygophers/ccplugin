# cortex search MCP first + hook 每轮注入 + 召回率提升

## Goal

修 4 个用户报问题:
- **P1** AI 没先搜知识库 (hook 提示弱)
- **P2** AI 用 bash search.sh 而非 mcp__obsidian__* (设计冲突)
- **P3** 多 MCP 时选了 qmd 而非 obsidian (无 ranking)
- **P4** 召回率低 (索引粒度差, 关键词不匹配 frontmatter)

核心: 推翻 cortex-search 五级回退顺序, 让 mcp__obsidian__* **first**。

## What I already know

### 当前设计冲突

| 文件 | 现状 |
|---|---|
| `scripts/hooks/user_prompt_submit.sh:140` | 推 `bash ~/.cortex/scripts/search.sh` (bash, 走 cortex 五级回退) |
| `AGENT.md §1 先搜后问` | 推 `cortex-search skill` 或 `obsidian search:context` (CLI), MCP 仅 fallback |
| `skills/cortex-search/SKILL.md` 五级回退 | L1 hot.md / L2 index.md / L3 SC REST / **L4 MCP simple_search** / L5 rg — MCP 排第 4 |
| 现实结果 | hook 推 bash, SKILL 把 MCP 排 L4, AI 自然不优先 MCP |

### Hook 触发条件

`user_prompt_submit.sh` 提示**仅在触发词命中时注入** (L140 触发词列表), 通用问题不注入 → AI 无强约束。

### qmd MCP 存在

`qmd` 是另一个 MCP server (本地 markdown 索引), AGENT.md **完全没提**。AI 多 MCP 时按 description 模糊匹配, qmd 听起来更通用 → 选错。

### 召回率低真因

`mcp__obsidian__obsidian_simple_search` 用 Obsidian 内置 engine, 匹配:
- frontmatter 字段值
- 正文
- tags

但 ingest 生成的项目子页 frontmatter:
- `title`: 文件名 (英文 `_index.md` / `architecture.md`)
- `desc`: 1-3 句描述
- `tags`: 高层分类
- **不含**用户搜索词的具体短语 (如 "tmtc_bg" / "测试环境" / "日志访问")

hot.md / index.md 仅含项目根 stub, 子页不进。

## Decision (ADR-lite)

**Context**: 4 个 AskUserQuestion 锁定。

**Decision**:
- D1 (P2): **MCP first 推翻五级**. hook + AGENT + SKILL 全部重写, mcp__obsidian__* 升 L1, search.sh 仅作 L2 fallback (Obsidian 不可达时)
- D2 (P3): 软提示 "优先 obsidian MCP", 不强制禁其他 (hook 提示文本含 "优先 obsidian, qmd/local rg 仅作 fallback")
- D3 (P1): hook **每个 user prompt 都注入** MCP first 提示, 移除触发词限定
- D4 (P4): 召回率提升 — ingest/save 落档时:
  - frontmatter 加 `aliases` (含中文同义词 / 缩写 / 全称)
  - frontmatter 加 `keywords` (用户可能搜的具体短语, 含项目名 / 文件名 / 函数名)
  - hot.md 加项目子页 ≥ 3 高分页面 (按 score + confidence 排序)

**Consequences**:
- search.sh 不废弃, 仍可用 (CLI 用户操作), 但 AI 不推
- cortex-search SKILL 五级重排 (MCP L1 / hot.md L2 / index.md L3 / SC L4 / rg L5)
- hook 提示每轮注入增 ~200 token (可接受)
- 召回率提升需 ingest 流程改, 旧文件需 migrate 加 aliases/keywords (留 P5 单独 / 与 P4 同 PR)

## Requirements

### R1 (P2 + P3): hook 重写 — MCP first

`scripts/hooks/user_prompt_submit.sh`:

```bash
# 当前 (触发词命中才注入):
if [触发词命中]:
    msg = "⚠️ 用户问题含触发词 ... 第一个工具调用必须先搜:
    1. bash ~/.cortex/scripts/memory.sh recall
    2. bash ~/.cortex/scripts/search.sh ..."

# 改为 (每轮注入, MCP first):
msg = """🔍 cortex 搜索硬契约 (本会话每轮强制):

非通用问答 (代码改 / 找文档 / 排查问题 / 涉及项目知识) 前, 第一个工具调用必须是搜索:

1. **首选**: `mcp__obsidian__obsidian_simple_search query=<关键词>` (优先 obsidian MCP, 非 qmd / 其他)
2. **次选**: `mcp__obsidian__obsidian_complex_search` (JsonLogic 复杂查询, 如按 tag/path 过滤)
3. **fallback**: `bash ~/.cortex/scripts/search.sh --query <q>` (Obsidian MCP 不可达时)
4. 记忆查询: `mcp__obsidian__obsidian_get_recent_changes` (按时间) 或 `bash ~/.cortex/scripts/memory.sh recall` (按 URI)

**禁止**:
- 跳过搜索直接问用户 (有触发词时)
- 用 qmd MCP 替代 obsidian MCP (qmd 索引不全)
- 用 Bash rg / Grep 替代 MCP search (除非 MCP 不可达 + search.sh 也失败)

无命中允许问用户, 但提示中引用 hits/path 证明搜过。
"""

if [触发词命中]:
    msg += "\n💡 当前项目在知识库: 知识库/项目/<host>/<org>/<repo>/"
```

注意: hook 输出格式对齐现有结构 (Python 字符串 / additionalContext), 不破坏现有解析。

### R2 (P2): AGENT.md §1 升级硬契约

`plugins/tools/cortex/AGENT.md` §1 "先搜后问" 重写:

```markdown
1. **先搜后问 (硬契约, hook 每轮强制)** —

   非通用问题前, 第一个工具调用必须是搜索:

   - **L1 = mcp__obsidian__obsidian_simple_search** (强制 first, 优先 obsidian 不用 qmd)
   - **L2 = mcp__obsidian__obsidian_complex_search** (JsonLogic 高级查询)
   - **L3 fallback = bash ~/.cortex/scripts/search.sh** (MCP 不可达时)
   - **L4 fallback = ripgrep** (search.sh 也失败)

   禁止跳过 L1 直接问用户 (有触发词时), 禁止用 qmd MCP 替代 obsidian。
   未授权 MCP 时 (AskUserQuestion 单次授权) 才走 L3。

   确认无既有经验 (L1-L4 全无命中) 才允许向用户提问, 提问时引用 L1 hits 路径证明搜过。
```

§3 vault 写硬契约不动 (上批 PR 已定)。

### R3 (P2): cortex-search SKILL 五级重排

`plugins/tools/cortex/skills/cortex-search/SKILL.md` 五级:

| 旧顺序 | 新顺序 |
|---|---|
| L1 hot.md | **L1 mcp__obsidian__obsidian_simple_search** |
| L2 index.md | **L2 mcp__obsidian__obsidian_complex_search** (按 tag / path 过滤) |
| L3 Smart Connections | **L3 hot.md** (Obsidian MCP 不可达时, AI 直读 hot.md, 实际此 case 罕见) |
| L4 MCP simple_search | **L4 index.md** |
| L5 ripgrep | **L5 ripgrep** (兜底) |

砍掉 Smart Connections (用户 Obsidian 不一定装 SC, 移除依赖)。

`scripts/cli/search.py` 实际 CLI 实现 (bash search.sh 调) 也按新顺序重排, 但 **保留** hot.md / index.md / SC 作为 fallback (CLI 模式 AI 不调时仍有用)。

### R4 (P3): hook 提示加 "优先 obsidian, 禁 qmd"

R1 已含 (msg "**首选**: mcp__obsidian__* (优先 obsidian MCP, 非 qmd / 其他)")。

不在 AGENT.md 显式禁 qmd (软约束), 仅在 hook 提示文本中提。

### R5 (P1): hook 每轮注入

R1 重写 `user_prompt_submit.sh` 主体 — 移除触发词条件分支, **每个 prompt 都注入** 搜索硬契约提示。触发词命中时**额外**加项目知识库路径提示。

### R6 (P4): 召回率提升 — frontmatter aliases/keywords + hot.md 加子页

#### R6.1 schema 升级

`skills/cortex-ingest/references/extract.md §3` 加 2 可选 (但强烈推荐) 字段:

```yaml
aliases: [<中文同义词>, <英文缩写>, <全称>, ...]  # AI 落档时根据 title/desc 生成 ≥ 3 个
keywords: [<具体短语>, <可能搜的词>, ...]         # ≥ 5 个具体词, 含项目名/文件名/函数名/术语
```

#### R6.2 ingest_remote / save 写入

`scripts/cli/lib/remote.py` `compute_*` 函数或新 helper:

```python
def extract_aliases_keywords(title: str, desc: str, body: str, host: str, org: str, repo: str, path: str) -> tuple[list[str], list[str]]:
    """从 title/desc/body/path 自动抽 aliases (≥3) + keywords (≥5)."""
    aliases = []
    # title 中文翻译占位 (AI 后续填)
    # 缩写 / 全称推导
    # ...
    
    keywords = []
    # path 文件名 stem
    # body 中 ``code`` 标识符 (rg)
    # heading text
    # 高频技术词
    # ...
    
    return aliases, keywords
```

ingest_git / ingest_website / save.py 落档时调, 写入 frontmatter。

#### R6.3 hot.md 加项目子页

`scripts/cli/save.py` 或独立 hot.md 维护脚本: 每次写新页时, 若该页 score ≥ 7.0 且 maturity in (stable, review) → 入 hot.md "## 项目高分页面" 节, 上限 3 篇 / 项目 (按 score 排序保留最新)。

### R7: 测试 + docs/memory 同步

- 测试 `test_aliases_keywords.py` + `test_hook_msg.py` (hook 提示文本断言)
- docs/快速上手.md 加 "AI 搜索硬契约" 节
- docs/故障排查.md 加 "MCP 不可达回退" 节
- AGENT.md / memory P9 同步

## Acceptance Criteria

- [ ] hook user_prompt_submit.sh 每轮注入 MCP first 提示 (无触发词限定)
- [ ] AGENT.md §1 升级硬契约 (L1 MCP first / L2 complex / L3 search.sh / L4 rg)
- [ ] cortex-search SKILL 五级重排 (MCP L1/L2, hot.md/index.md 降级)
- [ ] ingest_remote / save 落档写 aliases + keywords
- [ ] hot.md 加项目高分子页 (≤ 3 / 项目)
- [ ] hook 提示软标 "优先 obsidian MCP, 非 qmd"
- [ ] 测试基线 497 → ≥ 510
- [ ] ruff clean
- [ ] AI 质量检查 (cortex-search SKILL + AGENT.md) 验证仍正确识别
- [ ] real vault smoke: hook msg 注入验证 + ingest 后 frontmatter 含 aliases/keywords

## Definition of Done

- pytest 全绿
- ruff clean
- AI 质量检查通过
- hook 干跑测试: `cat /dev/null | python3 plugins/tools/cortex/scripts/hooks/user_prompt_submit.sh` 输出含 MCP first 提示
- 用户验证: 下次会话开始, AI 第一个工具调用是 mcp__obsidian__*
- git commit (拆 4 commits: hook+AGENT / SKILL / aliases-keywords / docs+memory)

## Out of Scope

- 不废弃 search.sh CLI (用户操作仍用, AI 不推)
- 不强制禁 qmd MCP (软提示)
- 不动 vault 写契约 (上批 PR §3 不变)
- 不破坏 497 测试 / 21 lint
- 不动评分字段实现 (上批 PR P8 落地)
- 不实现 Obsidian engine 索引重建 (是 Obsidian 内部, 不归 cortex)

## Implementation Plan (4 PR)

| PR | 范围 |
|---|---|
| PR1 | hook user_prompt_submit.sh + AGENT.md §1 重写 (P1 + P2 + P3 主体) |
| PR2 | cortex-search SKILL 五级重排 + search.py CLI 顺序调 |
| PR3 | aliases/keywords frontmatter + ingest_remote/save 写入 + hot.md 加子页 (P4) |
| PR4 | 测试 + docs + AGENT/memory P9 同步 |
