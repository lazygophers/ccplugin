# Design — cortex-ingest sources 拆分

## sources/<type>.md 模板

```markdown
> source — type=<X>; 识别 + 抓取方法 + frontmatter 提示

## 识别

- 匹配条件: <URL pattern / 路径属性>
- 优先序中位置: <见 routing.md>
- 反例 (不属本 source): <列举>

## 目标路径

`项目/<host>/<owner>/<repo>/` (按 cortex-schema 模块)

## 抓取方法

| 方法 | 适用 | 实现 |
| --- | --- | --- |
| 1 | 主路 | <e.g. gh CLI> |
| 2 | fallback | <e.g. WebFetch + parse README> |

## 典型示例

source: `<URL or path>`
plan:
```json
{...}
```

## frontmatter 提示 (落盘 README.md)

```yaml
---
type: project
source: <URL>
summary: <...>
...
---
```

完整模板: `../../cortex-schema/templates/project/<host>.md`

## 与 extract 边界

(同 sources.md 原边界节, 各 source 复述一行)
```

## 各 source 内容草案

### github.md
- 识别: URL host = github.com / www.github.com; ssh git@github.com:owner/repo.git
- 抓取: gh CLI (`gh repo view <o>/<r> --json description,readme,stargazerCount,...`); fallback WebFetch raw README
- 模板引用: cortex-schema/templates/project/github.md

### gitlab.md
- 识别: URL host = gitlab.com; ssh git@gitlab.com:...
- 抓取: glab CLI 优先 (若安装); fallback WebFetch
- 模板: cortex-schema/templates/project/gitlab.md

### website.md
- 识别: 任意 https?:// URL (host 非 github/gitlab)
- 抓取: WebFetch 拉 HTML → 简要 summary; 不递归 crawl
- 模板: cortex-schema/templates/project/website.md
- 注意: host=任意 domain, slug=URL path 第 1 段

### local.md
- 识别: 文件系统 dir 存在
- 子分支:
  - 含 `.git/config` + remote 是 github/gitlab → 递归当 github/gitlab 处理 (转给 github.md/gitlab.md 流程)
  - 无 git 或无 remote → 项目/local/<basename>/
- 抓取: 本地读 README.md / package.json / Cargo.toml / 等
- 模板: cortex-schema/templates/project/website.md (本地资源类似 website 一份)

## SKILL.md 路由表 (新)

```
## 何时读哪个

| 任务 | 文件 |
| --- | --- |
| 查 GitHub 抓取详情 | sources/github.md |
| 查 GitLab 抓取详情 | sources/gitlab.md |
| 查 Website 抓取详情 | sources/website.md |
| 查 local dir 抓取详情 (含 git remote 检测) | sources/local.md |
| 查输入识别算法 / 优先序 | references/routing.md |
| 查 CLI vs sub-agent 抓取流程 / dry-run/apply | references/workflow.md |
```

## 资源边界

| Subtask | 写 | 互斥 |
| --- | --- | --- |
| S1 | `sources/**` (新建 4) + 删 `references/sources.md` | 无 |
| S2 | `SKILL.md` + `references/{routing,workflow}.md` 引用 | 与 S1 串行 |
| S3 | 只读 | 收口 |

## 验证契约

S3 必跑:
1. `test -d sources/ && test ! -f references/sources.md`
2. 4 source 文件存在, 各 ≤ 100 行
3. SKILL.md ≤ 60 行 + frontmatter 合规
4. `! grep -rln 'references/sources.md\|sources.md' references/` (在 references 内 0 命中)
5. ingest 6 输入路由测试同前 (脚本不变)
6. 4 skill smoke 同前
