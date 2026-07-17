# agent-reach 路由

skein-research 外部检索探测到 agent-reach **AVAILABLE** 时按本文件路由; **FALLBACK** (无 agent-reach) 见文末降级段。agent-reach 是互联网能力路由器 (15 平台、多后端), 存在时必须用它, 不自己发明方案。它自带 `SKILL.md` + `references/{search,social,career,dev,web,video}.md` 完整命令, 按其文档路由。

## 路由对照 (调研意图 → agent-reach 分类)

| 调研意图 | agent-reach 分类 |
| --- | --- |
| 网页/代码搜索 (选型、报错、文档) | search |
| GitHub 仓库/实现/issue/PR | dev |
| 社区讨论 (小红书/Twitter/B站/Reddit/V2EX) | social |
| 网页/文章/RSS 精读 | web |
| YouTube/B站/播客字幕转录 | video |

路由细节以 agent-reach 各 references 为准 (命令版本漂移只维护一处)。

## AVAILABLE — 纳入 agent-reach 作数据源

1. **多后端/登录态平台先体检**: `agent-reach doctor --json`, 按各平台 `active_backend` 选命令组。
2. **声明在用什么**: 回传里注明「经 agent-reach 的 X 平台 / Y 后端取得」(承接 researcher「带来源」铁律, 来源写平台+命令)。
3. **失败按 agent-reach references 重试链**, 不瞎猜命令。
4. **全网调研组合多平台并行**: Exa 网页搜索 + GitHub 看实现 + Twitter/Reddit 看讨论 + 小红书/B站看中文场景, 并行收集再汇总。

## FALLBACK — 无 agent-reach

降级用 agent 自带 `WebSearch` / `WebFetch`。能力受限 (无登录态平台、无字幕转录), 回传时**注明「agent-reach 不可用, 已降级 WebSearch/WebFetch, X 类数据未覆盖」**, 别假装全网都查过。
