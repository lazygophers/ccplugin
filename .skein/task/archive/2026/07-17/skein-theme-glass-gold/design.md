# skein 微光流沙玻璃主题 — 详细设计

## 令牌系统现状

board + webapp 共享同一套 oklch 语义令牌 (`--h/--c-*/--l-*/--h-*` seed + 明度锚点 → 派生 `--bg/--card/--fg/--accent/--st-*`)。主题切换 = `<html data-theme=xxx>` 变量交换, 无需 dark class。status 色相 (`--h-pending/active/check/done/failed`) 语义固定跨主题不变。

- board: 多主题文件 (`themes/skein.css` 等) + switcher.js (读写 data-theme + localStorage)
- webapp: 单一无主题外观, 令牌折叠进 `:root` (input.css), 需加暗色变体

## 双模式设计

### 浅色 (skein, 增强现有)
- 底纹: 静态晨曦 (薰衣草白顶 → 暖金光晕 → 浅蓝穹底) — 保留
- 增强: 加流光呼吸 (radial-gradient 缓慢位移) + 卡 glass sheen 扫过
- 玻璃卡: 60% 白玻璃 + backdrop-blur(14px) + 蓝顶光描边 — 保留, 加 hover 流光描边

### 暗色 (skein-dark, 新建)
- 底纹: 夜空 (#0B1220 深蓝底) + 金沙微光 (静态星点, 非粒子动画 — 性能)
- 玻璃卡: 40% 暗玻璃 + backdrop-blur(14px) + 金辉光描边
- accent 蓝提亮 (暗底对比), 暖金辉光增强
- 明度锚点反转: `--l-bg:.15 --l-card:.20 --l-fg:.92 --l-head:.96 --l-brd:.30`

## 动效分层 (结构层 + 细节层)

### 结构层
| 元素 | 动效 | 实现 |
|------|------|------|
| 卡 hover | 流光描边 (蓝→金→蓝沿边框滑动) | `::after` conic-gradient + rotate |
| active 卡 | 蓝描边脉动 (box-shadow 呼吸) | `@keyframes pulse` 2s |
| 进度条 | 蓝金流光 (已有 skein-flow) | 保留 |

### 细节层
| 元素 | 动效 | 实现 |
|------|------|------|
| 数字统计 | 递增 (0→值, 600ms) | petite-vue `v-effect` + requestAnimationFrame |
| 列表项 | 入场 (translateY+opacity) | CSS transition + IntersectionObserver |

## 性能守卫

- `@media (prefers-reduced-motion: reduce)` — 全部动画降级为瞬切
- 视口外暂停: board 已有 `.voff` 门控, webapp 用 IntersectionObserver 补
- 流光描边用 `will-change: transform` + transform 而非 background-position (GPU)

## huashu 原型

S1 产出独立高保真 HTML 原型 (board 卡片 + webapp 页面 双模式可切), 用户评审。定稿后 S2/S3 迁回 skein 令牌系统 (原型用硬编码色 → 迁回换 oklch 变量)。

## 调度 (task.json 真值)

```
S1 huashu-prototype (无 deps) → S2 board-themes (deps:S1) ∥ S3 webapp-dark-motion (deps:S1) → S4 motion-pref-guard (deps:S2,S3)
```
