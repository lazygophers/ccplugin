# fallback — 未命中兜底

vault 两层都未命中 (见 `search.md`) → 按序兜底. 闭环必走回填 (`writeback.md`).

## 兜底顺序

```
未命中 vault
 │
 1. WebSearch 互联网
 │   拿得准 → 用答案 (标 source URL) → 回填
 │   拿不准 ↓
 2. 问用户 (AskUserQuestion / 直接提问)
 │   用户答 → 用答案 → 回填
```

### 第 2 步: WebSearch 互联网

- 调 WebSearch 查 query
- **拿得准**: 来源权威 (官方文档 / 主流社区) + 多来源一致 → 采用答案, 必标 `source: <URL>`
- **拿不准** → 不瞎猜, 降到第 3 步问用户

### 第 3 步: 问用户

- 用 AskUserQuestion (选项明确时) 或直接提问 (开放式)
- 用户答即权威, 采用
- 禁绕过用户用 WebSearch 模糊结果硬凑

## "拿不准" 判定 (任一命中即拿不准 → 问用户)

| 信号 | 例 |
| --- | --- |
| 多来源冲突 | 不同文档/帖子给出相反结论 |
| 无权威源 | 仅论坛只言片语 / 无官方背书 |
| 时效性强 | 版本/API 频繁变, 搜索结果可能过期 |
| 项目私有约定 | 本仓库/团队特有规则, 互联网不可能知道 → **直接问用户, 跳过 WebSearch** |

项目私有约定类 query 应直接进第 3 步, 不浪费 WebSearch.

## 兜底答案标记

- WebSearch 来源: 答案必带 `source: <URL>`, 回填时进 frontmatter (见 `writeback.md`)
- 用户答案: 标来源 = 用户口述, 回填时可注明 (无 URL)
