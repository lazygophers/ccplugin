# 内容 JSON schema

内容 JSON 只写内容，不写样式。CLI 校验顶层键与每个块的 `type`、必填字段；未知顶层键、未知块类型、缺必填字段都会报错（退出码 2）。

## 顶层字段

| 键 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `topic` | string | 是 | 主题短名，决定输出文件 `<topic>-v<N>.html` 与 `outDir` 的 `{topic}`。只允许字母（含中文）、数字、`. _ -`，首字符为字母或数字，≤80 字符，不含 `..` |
| `type` | `research` \| `plan` \| `compare` \| `review` \| `explain` \| `report` \| `spec` | 是 | 产物类型，参与风格决定（`byType`），显示在页头 |
| `style` | `paper` \| `sketch` \| `terminal` | 否 | 仅在用户点名风格时写；优先于配置 |
| `title` | string | 是 | 标题 |
| `subtitle` | string | 否 | 副标题 |
| `meta` | object | 否 | `author`（作者块文字，缺省取配置 `author.name`）、`date`（YYYY-MM-DD，缺省当天）、`status`（如 `草稿` / `定稿`） |
| `summary` | object | 是 | `point`：一句话结论；`text`：摘要段落；`points`：至多 3 条要点 |
| `kpis` | Kpi[] | 否 | 指标卡（2–4 个），仅科研风显示；缺省或 `[]` 不显示 |
| `blocks` | Block[] | 是 | 正文块，至少 1 个 |
| `conclusion` | string | 否 | 文末一句话结论 |
| `changes` | string[] | 否 | 与上一版的变更；仅在 v≥2 时显示于正文前 |
| `references` | {text, source}[] | 是 | 出处，只列本轮实际读过的来源（读过的网页、文件、命令输出），`source` 写 URL、文件路径或命令；凭记忆的知识不列为出处，确需提及时在 `text` 末尾标「未核对」；可为空数组 |

CLI 写入、内容不得提供的字段：`meta.generated`、`meta.version`、`meta.kind`、`meta.byline`、`meta.logo`、`watermark`、`showme`。

Kpi：`{ label: string, value: string, unit?: string, note: string, spark?: number[] }`，`spark` 为迷你柱数据。

## 块

通用约定：`caption` 为图 / 表 / 清单标题，自动编号（图 n、表 n、清单 n）；`point` 为可选的本块要点，科研风放边栏旁注，手绘风放荧光笔标题，程序员风不显示。

| type | 必填 | 可选 | 字段说明 |
|---|---|---|---|
| `heading` | `text` | `num`、`level`、`wide` | 开一个新面板。`num` 覆盖自动节号（如 `"3.1"`）；`level: 1` 为分部标题（横跨整行、不带正文）；`wide: true` 强制横跨两列 |
| `paragraph` | `text` | | 正文段落，行长约 80 字 |
| `list` | `items` | `ordered` | `items: {title?, text}[]` |
| `flow` | `caption`、`nodes` | `point` | 纯顺序步骤。`nodes: {id, label, detail}[]`，单行从左到右，一行放不下（缩放后说明字号低于 12px）时自动折成蛇形多排；节点按文字加宽、超宽折行；所在面板自动横跨两列 |
| `graph` | `caption`、`nodes`、`edges` | `point`、`direction` | 有向图，用于有分叉或合并的结构（git 分叉、调用树、架构依赖）。`nodes: {id, label, detail?}[]`；`edges: {from, to, label?}[]`，`from` / `to` 引用节点 `id`，不得成环；`direction`：`LR`（缺省，左→右）或 `TB`（上→下），`LR` 横排放不下（缩放后说明字号低于 12px）时自动改为 `TB`。自动分层：层号为最长前驱链长度，节点优先沿用前驱所在的行（车道），分叉出的节点另起一行；所在面板自动横跨两列 |
| `table` | `caption`、`columns`、`rows` | `point`、`mono` | `columns: string[]`，`rows: string[][]`；`mono` 指定等宽显示的列下标 |
| `kv` | `caption`、`columns`、`rows` | `point`、`mono` | 与 `table` 同形，用于配置项 / 术语表；缺省第 0 列等宽 |
| `chart` | `caption`、`unit`、`series`、`data` | `point`、`note`、`total` | 分组柱状图。`series: {key, label}[]`；`data` 每行 `stage` 为分类名，其余键与 `series[].key` 对应、值为数字；`note` 为数据说明；`total` 给出时科研风附合计公式 T<sub>total</sub> = Σ 最后一个系列 |
| `code` | `caption`、`lang`、`filename`、`code` | `point` | 高亮语言：`typescript`、`bash`、`json`、`text`，其余自动识别 |
| `codes` | `caption`、`panes` | `point` | 多栏并排代码，`panes: {title, lang, code}[]`；所在面板横跨两列 |
| `steps` | `items` | `point` | 编号步骤，`items: {title, detail}[]`；也用于「需要你做的事」与时间线（`title` 写日期） |
| `stack` | `caption`、`layers` | `point`、`note` | 叠放图，`layers[0]` 为最上层（优先级最高），`layers: {label, detail}[]`；`note` 标在箭头旁 |
| `wireframe` | `caption`、`regions` | `point` | 整页线框 ①–⑧，`regions` 依次对应页头、结论区、指标卡、正文网格、需要你做的事、出处、页脚、水印 |
| `image` | `caption`、`src` | `point`、`alt` | `src` 为本地文件路径（相对内容 JSON 所在目录；png/jpg/gif/webp/svg）或 `data:` URI，CLI 内联；远程 URL 拒绝 |

## 布局规则

- 按 `heading` 切面板；窗口 ≥1440px 两列，以下单列。
- 含 `flow`、`graph`、`codes`、`wireframe` 的面板横跨两列；落单的普通面板也横跨整行。

## 示例

```json
{
  "topic": "cache-choice",
  "type": "compare",
  "title": "会话缓存选型",
  "subtitle": "Redis 与进程内 LRU 的取舍",
  "meta": { "status": "草稿" },
  "summary": {
    "point": "选 Redis",
    "text": "多实例部署要求共享会话，进程内 LRU 无法满足；Redis 的 P99 延迟在预算内。",
    "points": ["多实例共享是硬约束", "P99 1.8 ms，预算 5 ms", "运维成本可接受"]
  },
  "kpis": [
    { "label": "P99 延迟", "value": "1.8", "unit": "ms", "note": "压测 10k QPS" },
    { "label": "候选方案", "value": "2", "note": "Redis / LRU" }
  ],
  "blocks": [
    { "type": "heading", "text": "对比" },
    { "type": "table", "caption": "两种方案", "point": "共享会话是分水岭",
      "columns": ["维度", "Redis", "进程内 LRU"],
      "rows": [["多实例共享", "支持", "不支持"], ["P99", "1.8 ms", "0.1 ms"]] },
    { "type": "heading", "text": "延迟" },
    { "type": "chart", "caption": "各操作延迟", "unit": "ms", "note": "压测环境 4C8G",
      "series": [{ "key": "p50", "label": "P50" }, { "key": "p99", "label": "P99" }],
      "data": [{ "stage": "get", "p50": 0.4, "p99": 1.8 }, { "stage": "set", "p50": 0.5, "p99": 2.1 }] },
    { "type": "heading", "text": "需要你做的事" },
    { "type": "steps", "items": [{ "title": "确认预算", "detail": "批准 Redis 实例费用。" }] }
  ],
  "conclusion": "采用 Redis 作为会话缓存。",
  "references": [{ "text": "压测记录", "source": ".scratch/cache-choice/bench.log" }]
}
```
