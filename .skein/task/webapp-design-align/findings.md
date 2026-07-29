# s4 — 范围外页面溢出风险清单 (只读勘察, 零代码改动)

## 前提校正 (重要 — 缩小了风险面)

design.css 里绝大多数 tailwind 尺寸类 (`w-10` / `h-10` / `gap-*` / `w-56`) **本身就是 rem 基准**, 全局 `html { font-size: 17px }` 让它们与文字**同比例放大**, 容器与内容同步变大, 不会单独撑爆。

真正会撑爆的只有三类:
1. **字面 px** — inline style 或 `[Npx]` 任意值, 不随 rem 走
2. **flex 行内固定文案兄弟元素** — 徽标/时间戳挤占 `truncate` 元素的可用空间
3. **视口临界处的横向整行** — topbar 整体变宽后溢出

## 高 (1 条)

**tasks.js:155** — 全仓唯一命中的字面 px 任意值 (已 grep 全量核实, `[Npx]` 模式仅此一处)
```js
h('label.flex.items-center.gap-2.px-3.py-1.5.rounded-lg.border.border-brd/60.bg-card/60.min-w-\\[200px\\]', [
```
- 风险: `min-w-[200px]` 不随根字号缩放。但它是 **min 非 fixed**, 内部 input 是 `flex-1`, label 会被内容撑开 → 实际破版风险低
- 建议: 改 `min-w-[12.5rem]` 彻底同步; 不改也不会破版
- 附带发现: 这行的 `border-brd/60` 与 `bg-card/60` 同属本轮在 board/task.js 清掉的死类家族 (design.css/tailwind.css/tokens.css 均无定义)。tasks.js 在本次范围外, 未动

## 中 (6 条) — 5 条是同一结构性模式

**模式: flex 行内固定文案徽标挤压 truncate 区域**, 在 4 个文件重复出现:

| 文件:行 | 挤压源 | 被挤 |
|---|---|---|
| dashboard.js:72-89 | `antd-tag` 状态徽标 + 时间戳 | `flex-1.min-w-0` 内 truncate 标题 |
| tasks.js:24-49 | `priorityBadge` 长文案 `优先级 (8)` | truncate 标题 |
| queue.js:73-102 | 同上 `priorityBadge` | truncate 标题 |
| archive.js:12-49 | `antd-tag` 状态徽标 | truncate 标题 |

- 风险: 徽标文字随字号放大占更多水平空间 → 同行 truncate 标题**截断点提前** (信息丢失, 非破版)
- **最小共性修法**: 统一给徽标类元素补 `flex-shrink-0` (一处改法覆盖 4 个文件)。未实施

**spec.js:34-37** — `spec.id` 是全路径 (如 `core/arch/xxx.md`), 本身长, `truncate` 截断点提前概率高
- 建议: 加 `title` 属性做 tooltip 兜底

**index.html:38-67** — topbar 单行拥挤 (logo + 6 个 nav tab + `w-56` 搜索框 + 2 个图标按钮, `flex items-center gap-4` 无 wrap 无 overflow-x)
- 风险: 在 `md` 断点刚过 (≈768px, nav 刚显示) 的窄桌面视口, 总宽放大 6.25% 后可能挤压换行或搜索框被压没
- **需实际视口走查 768px–1024px 区间** — 纯结构推断, 未验证

## 低 (4 条)

- dashboard.js:23 / spec.js:56 — `w-10.h-10` KPI/图标框, rem 基准同比例放大, 仅未做三位数任务量的视觉走查
- tasks.js:34 — `line-clamp-1` 描述行, 每行容纳字数减少但整行同比例缩放, 影响有限
- index.html:74-76 — `fab-top` `fixed bottom-6 right-6 w-12 h-12`, 偏移与尺寸均 rem 基准, 位置比例不变

## 汇总

高 1 / 中 6 / 低 4 — **零破版级风险**, 全部是「截断提前」类信息密度问题, 加上 1 处需视口走查确认的 topbar。

后续若要动手, 优先级: ① 徽标补 `flex-shrink-0` (一改覆盖 4 文件) → ② topbar 视口走查 → ③ tasks.js:155 转 rem。
