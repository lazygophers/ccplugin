# workflow — 抓取流程 + dry-run/apply

## 抓取方法表

| InputKind | 首选方法 | Fallback | 工具载体 |
| --- | --- | --- | --- |
| github | `gh repo view <owner>/<repo> --json name,description,readme,defaultBranchRef,licenseInfo` | `WebFetch https://raw.githubusercontent.com/<o>/<r>/HEAD/README.md` | CLI (gh) / sub-agent (WebFetch) |
| gitlab | `glab repo view <owner>/<repo>` | `WebFetch https://gitlab.com/<o>/<r>/-/raw/HEAD/README.md` | CLI (glab) / sub-agent |
| website | `WebFetch <url>` | (无) | sub-agent (有 WebFetch 工具的 agent) |
| local | 直接读 `<dir>/README.md` + 可选 `package.json` / `pyproject.toml` / `Cargo.toml` | (无) | CLI (read) |

混合策略: ingest.sh 本身不直调 `WebFetch` (脚本无该能力), 而是输出 plan, 标 `fetch_method`. main 会话或 sub-agent 按 plan 调度.

## dry-run JSON plan 字段

```json
{
  "source": "https://github.com/lazygophers/ccplugin",
  "kind": "github",
  "host": "github.com",
  "owner": "lazygophers",
  "repo": "ccplugin",
  "target_path": "项目/github.com/lazygophers/ccplugin",
  "target_filename": "README.md",
  "fetch_method": "gh",
  "fetch_fallback": "WebFetch",
  "frontmatter_preview": {
    "type": "project",
    "host": "github.com",
    "owner": "lazygophers",
    "repo": "ccplugin",
    "source": "https://github.com/lazygophers/ccplugin"
  },
  "needs_main": false,
  "notes": []
}
```

`needs_main=true` 当 fetch_method 仅 sub-agent 可执行 (`WebFetch` website 情况).

## apply 行为

**本 task 范围**: `--apply` **仍只生成 plan + 标注 "需 main 抓取"**, 不直接落盘. 真实抓取由 main 会话或后续 task 接 sub-agent 完成. 理由:

- 脚本无 `WebFetch` 能力 (sub-agent 才有)
- `gh` / `git clone` 可在脚本内做, 但完整 ingest 链路 (抓 → 摘要 → frontmatter 渲染) 牵涉 LLM 总结, 应由 main 调度.

**后续 task 范围**: 实现 `--apply` 真实落盘 (frontmatter 用 cortex-schema `templates/project/<variant>.md` 渲染, 内容用 `gh`/`WebFetch` 取 README + LLM 摘要).

## state/ingest-cursor.json

```json
{
  "entries": [
    {
      "source": "https://github.com/lazygophers/ccplugin",
      "target_path": "项目/github.com/lazygophers/ccplugin",
      "sha": "<commit-sha or content-sha>",
      "ingested_at": "2025-06-09T12:00:00Z"
    }
  ]
}
```

apply 落盘时追加; dry-run 不写. 用于增量 (二次 ingest 同源时跳过或 diff).

## 调度示例 (main 会话)

```bash
# 1. 生成 plan
bash scripts/ingest.sh --dry-run --source https://github.com/lazygophers/ccplugin > /tmp/plan.json

# 2. 检查 plan
jq '.target_path, .fetch_method' /tmp/plan.json

# 3. main 或 sub-agent 按 plan 执行抓取 (本 task 范围外)
#    - gh repo view ... > raw.md
#    - LLM 摘要 + frontmatter 渲染 (cortex-schema templates)
#    - 写入 <vault>/项目/github.com/lazygophers/ccplugin/README.md
#    - 追加 state/ingest-cursor.json
```

## 与其他 skill 协作

- 入库后想检索/分类: 用 `cortex-extract` (不会动 `项目/`, 只动 `memory/L4-inbox/`).
- 入库前/后 frontmatter 校验: 用 `cortex-lint`.
- frontmatter / 路径权威定义: `cortex-schema`.
