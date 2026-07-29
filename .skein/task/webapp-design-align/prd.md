# webapp 设计对齐 (board+task 改用 design.css 原语 + 字号上调) — PRD (主入口)

## 目标
- [ ] webapp 字号整体上调 — 当前 <1440px 视口无 html 基线 (design.css 仅 :1847 ≥1440px / :1873 ≥1700px 两条媒体查询内的 html 规则), 正文实际 text-sm=14px / text-xs=12px 偏小
- [ ] design.css 已有原语但页面手搓工具类 — board.js ~62 处 / task.js ~67 处裸堆砌 (≥3 class 且不含任何语义原语), 且两页板块标题分歧 (board 用 .eyebrow 11px, task 用 .section-title 1.25rem)
- [ ] 清掉从未生效的死 class
## 边界
- 范围内文件: assets/webapp/src/design.css, src/new/pages/board.js, src/new/pages/task.js
- 字号方案 (用户裁定 A「基线 + px 收口」): ① design.css 顶部新增无媒体查询 html { font-size: 17px } ② :1847 ≥1440px 16px→18px ③ :1873 ≥1700px 17px→19px ④ design.css 内 ~80 处 font-size: Npx 转 rem (基数 17, 保留 3 位小数)
- 间距同步 (用户裁定): design.css 内组件级 padding / margin / gap 的 px 值也按 /17 转 rem (~150+ 处)。border-width / box-shadow / border-radius / outline 的 px 不转 (与字号无关, 转了反而失真)
- DAG 族整体锁 px (用户裁定「节点内字号锁死」+ main 自决连带项): .dag-node* / .dag-pop-* / .dag-legend* / .dag-svg / .dep-dag-* / .sub-dag-* 这几族的 font-size 与 padding / margin / gap 全部保持 px 原值不转 — 依据 board.js:280-282 DENSITY 表 (large 260x76 / compact 190x52 / mini 120x32) 是 JS 算的固定 px 框, 内容跟着基线涨而框不涨会挤爆; design.css:653 注释已记录 mini 档 32px 高只剩 28px 放字
- 原语替换 (用户全选 4 项): ① board.js 8 处 .eyebrow → .section-title (823/848/872/918/926/944/953/963) ② board.js:711 + task.js:311 手搓行 → .subtask-row (design.css:1105) ③ 清死类 ④ board.js:656 → .tab-btn (design.css:385); task.js:445 面包屑 → .antd-breadcrumb (design.css:1495, 分隔符走 .sep)
- 死类清单 (tailwind.css 与 design.css 均无定义): bg-surface/30 (board.js:874, task.js:287), bg-surface/50 (task.js:242), border-brd/30 (task.js:242/287), antd-btn-primary (task.js:355/526), w-1.5 h-1.5 (task.js:208), gap-1.5 (board.js:642); 另 task.js:460/462 h(span·opacity-40) 用的是全角 · 非点号, class 从未生效
- 波及页面 (用户裁定「顺手扫一遍」): html 基线是全局的, dashboard/tasks/queue/spec/archive.js 与 index.html 字号会一起变大 — 本次不改它们的代码, 但 s4 出一份固定尺寸容器 / 溢出风险清单供后续裁定
- 范围外: tokens.css 不加字号 token (无收口点); tailwind.config.js 不动 (不改 fontSize 刻度); depdag.js 已基本对齐不改样式
- 约束: JS 侧字号类名零改动 (board+task 共 76 处 text-* 保持原样, 靠 html 基线放大)
## 验收标准
- [ ] design.css 内 grep "font-size:.*px" 只剩: html 基线 3 条 + DAG 族 (dag-*/dep-dag-*/sub-dag-*) 的原值; 其余全为 rem
- [ ] px→rem 换算逐条正确 (N/17, 保留 3 位小数), 抽查 .eyebrow(11px→0.647) / .md-body(13px→0.765) / .antd-btn(13px→0.765) / .tl-name(14px→0.824) / .badge(11px→0.647) / .antd-tag(12px→0.706) 六处
- [ ] DAG 族零改动: git diff 中 .dag-node* / .dag-pop-* / .dag-legend* / .dag-svg / .dep-dag-* / .sub-dag-* 各规则的 font-size 与 padding 行不出现在 diff 里
- [ ] padding/margin/gap 转 rem 覆盖组件级规则; border-width / box-shadow / border-radius / outline 的 px 保持不变 (diff 中不应出现这四类属性)
- [ ] 死类全部消除: grep bg-surface/ + border-brd/30 + antd-btn-primary + w-1\.5 + h-1\.5 + gap-1\.5 在 board.js/task.js 中零命中
- [ ] 全角 · 修正: task.js:460/462 改为 h(span.opacity-40) 正常点号
- [ ] 原语替换后 grep 计数: board.js 中 .eyebrow 归零、.section-title ≥8; .subtask-row 在 board.js+task.js 合计 ≥2; .tab-btn 在 board.js ≥1; .antd-breadcrumb 在 task.js ≥1
- [ ] node --check board.js / task.js 全过
- [ ] s4 产出风险清单 (只读, 不改码): 5 个页面 + index.html 的固定 px 宽高 / truncate / 绝对定位布局位置, 标注哪些会被 +6.25% 字号撑破
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list webapp-design-align`)
