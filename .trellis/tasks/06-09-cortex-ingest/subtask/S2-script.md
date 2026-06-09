---
id: S2
slug: script
deliverable: D3,D4,D5
parent-task: 06-09-cortex-ingest
status: planned
execution-layer: sub-agent
depends-on: []
blocks: [S4, S5]
estimated-tokens: 12000
---

# S2 · 写 ingest.sh + _ingest/ python 模块

## 产出

- `scripts/ingest.sh` (bash 入口 ≤ 80 行)
- `scripts/_ingest/__init__.py` (共享: GitRemote dataclass, URL_RE, helper)
- `scripts/_ingest/identify.py` (输入识别: URL / ssh git / local)
- `scripts/_ingest/router.py` (目标路径计算)
- `scripts/_ingest/planner.py` (dry-run plan JSON 生成)
- `scripts/_ingest/runner.py` (argparse + main)

## 验证

```bash
bash plugins/tools/cortex/scripts/ingest.sh --help

# 各类输入路由 (使用 fixture inputs)
for src in \
  'https://github.com/lazygophers/ccplugin' \
  'https://gitlab.com/gitlab-org/gitlab' \
  'https://docs.python.org/3/library/argparse.html' \
  'git@github.com:tokio-rs/tokio.git'; do
  out=$(bash plugins/tools/cortex/scripts/ingest.sh --dry-run --source "$src" --target /tmp/cortex-test 2>/dev/null)
  echo "$out" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
print('  $src → ', d['plan'][0]['target_path'])
"
done
```

期望:
- github URL → `项目/github.com/lazygophers/ccplugin`
- gitlab URL → `项目/gitlab.com/gitlab-org/gitlab`
- docs.python.org → `项目/docs.python.org/_/3`
- ssh git@github.com → `项目/github.com/tokio-rs/tokio`

## Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-ingest

## 目标
写 scripts/ingest.sh (bash 入口 ≤ 80 行) + scripts/_ingest/ (5 python 模块) 实现输入识别 + 路径路由 + dry-run JSON plan 生成. 本 task 不做实际抓取, 仅 plan.

## 已知
- 4 类输入: github URL / gitlab URL / website URL / local dir
- ssh git URL (git@github.com:owner/repo.git) 也识别
- local + .git + remote → 当 github/gitlab 处理
- local 无 git → 项目/local/<basename>/
- 目标路径: 项目/<host>/<owner>/<repo>/ 或 项目/<domain>/_/<slug>/ 或 项目/local/<name>/
- pyyaml 可用, 也允许 fallback stdlib

## 入口 (ingest.sh)
```
ingest.sh [--dry-run|--apply] [--target <vault-root>] --source <url-or-path> [--help]
  默认 --dry-run + target=$HOME/.cortex
  --source 必填
  --apply 行为: 本 task 范围只生成 plan (与 dry-run 同), 多打一行 "需 main 抓取" 提示
```

## planner JSON 输出
```json
{
  "mode": "dry-run",
  "source": "<input>",
  "kind": "github|gitlab|website|local",
  "plan": [
    {
      "source": "<input>",
      "kind": "<kind>",
      "target_path": "项目/<host>/<owner>/<repo>",
      "target_filename": "README.md",
      "fetch_method": "gh|git-clone|webfetch|local-read",
      "frontmatter_preview": {"type": "project", "source": "<URL>", "summary": "TODO"}
    }
  ]
}
```

## 模块边界
- identify.py: kind 判断 (含 git_remote 读 .git/config [remote "origin"] url)
- router.py: target_path 计算
- planner.py: JSON 拼装
- runner.py: argparse + 输出
- __init__.py: 共享类型

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/scripts/ingest.sh + plugins/tools/cortex/scripts/_ingest/** (新建)
禁改: 其他

## 输出限
- ingest.sh ≤ 80 行
- 每 _ingest/*.py ≤ 200 行

## 验收
subtask "验证" 节命令全过.

## 失败处理
- 工具错 → 重试 1 次
- ssh git URL 不识别 → 用 regex git@<host>:<owner>/<repo>(.git)?
- 不确定 → "需要: <问题>" 回 main

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚
```bash
rm -rf plugins/tools/cortex/scripts/ingest.sh plugins/tools/cortex/scripts/_ingest/
```
