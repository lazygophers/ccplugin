---
id: S1
slug: skill
deliverable: D1,D2
parent-task: 06-09-cortex-ingest
status: planned
execution-layer: sub-agent
depends-on: []
blocks: [S4, S5]
estimated-tokens: 8000
---

# S1 · 建 cortex-ingest skill

## 产出

- `skills/cortex-ingest/SKILL.md` ≤ 60 行
- `skills/cortex-ingest/references/sources.md` (4 类输入定义 + 与 extract 边界)
- `skills/cortex-ingest/references/routing.md` (识别算法 + 目标路径表 + git remote 检测)
- `skills/cortex-ingest/references/workflow.md` (抓取流程 CLI + sub-agent 混合 + dry-run/apply)

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-ingest
test -f $d/SKILL.md && test -f $d/references/sources.md && test -f $d/references/routing.md && test -f $d/references/workflow.md
[[ $(wc -l < $d/SKILL.md) -le 60 ]]
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-ingest'
assert len(fm['description']) <= 512 and len(fm['when_to_use']) <= 128
assert '用户说' not in fm['description'] and '用户说' not in fm['when_to_use']
assert isinstance(fm['arguments'], str)
assert fm.get('user-invocable') is True
print('OK')
"
```

## Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-ingest

## 目标
建 cortex-ingest skill: SKILL.md ≤ 60 行薄入口 + 3 references (sources/routing/workflow), 描述知识库构建流程, 接受 GitHub/GitLab/Website URL + local dir 4 类输入, 路由到 cortex-schema 项目模块.

## 已知
- frontmatter (见 design.md "frontmatter" 节):
  name: cortex-ingest
  description: "知识库构建 ingest — 接受 GitHub/GitLab/Website URL 或 local dir 输入, 自动识别+路由到 项目/<host>/<owner>/<repo>/ (本地 git repo 当 github/gitlab 处理, 非 git → 项目/local/<name>/). 默认 dry-run JSON plan, --apply 调度抓取 (gh/git clone/WebFetch 混合) + 落盘."
  when_to_use: "入库新仓库/抓取项目/import GitHub repo/ingest website/导入本地 dir/build 项目知识库"
  argument-hint: "[--dry-run|--apply] <source>"
  arguments: "[--dry-run|--apply] <来源>"
  user-invocable: true
- 路径权威: cortex-schema (引用 ../cortex-schema/templates/project/<variant>.md)
- 与 extract 边界: extract = L4-inbox 内部分类; ingest = 外部资源进 vault

## SKILL.md 结构
1. frontmatter
2. 1 段总览
3. 4 输入速查表 (github/gitlab/website/local)
4. 目标路径速查表
5. 路由表: | 任务 | 文件 |
   - 查 4 类输入定义 + 与 extract 边界 → sources.md
   - 查识别算法 + 路径映射 + git remote 检测 → routing.md
   - 查抓取流程 (CLI vs sub-agent) + dry-run/apply → workflow.md
6. 入口: bash scripts/ingest.sh
7. 引用 cortex-schema (项目模块 templates) / cortex-lint / cortex-extract

## references 内容
- sources.md: 4 类输入逐条 (github / gitlab / website / local), 含识别条件 + 典型示例 + 与 extract 边界 (ingest 抓外部, extract 整内部)
- routing.md: 识别算法 (URL pattern → ssh git → local + git remote → local fallback) + 目标路径表 + git remote 解析 (https + ssh) + 路径占位规则 (slug / `_`)
- workflow.md: 抓取方法表 (github=gh/WebFetch, gitlab=glab/WebFetch, website=WebFetch, local=read) + dry-run JSON plan 字段 + apply 行为 (本 task 范围只生成 plan, 实际抓取由 main / sub-agent 后续完成) + state/ingest-cursor.json 结构

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-ingest/** (新建)
禁改: 其他 skill / 脚本 / agent

## 输出
- SKILL.md ≤ 60 行
- 各 reference ≤ 220 行

## 验收
subtask "验证" 节命令全过.

## 失败处理
- 工具错 → 重试 1 次
- 字符上限 → 砍冗余, 保触发词 (ingest/提取/抓取/import/build/github/gitlab/website/local)

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚
```bash
rm -rf plugins/tools/cortex/skills/cortex-ingest/
```
