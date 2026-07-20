# skein 微光流沙玻璃主题 (蓝金 + 暗色 + 动效) — PRD (主入口)

## 目标
- [ ] 双模式主题: 浅 (晨曦光晕, 增强现有) + 暗 (夜空金沙, 全新), switcher 一键切换, localStorage 记忆
- [ ] 微光流沙玻璃: 玻璃卡 (backdrop-blur + 半透) + 蓝描边金辉光, 贯穿 board + webapp
- [ ] 动效丰富 (结构层 + 细节层): 卡描边流光 / 状态脉动 / 数字递增 / 入场动画
- [ ] 原型先行: huashu-design 出双模式高保真 HTML 原型, 用户评审定稿后迁回 skein 主题文件

## 边界
范围内:
- `assets/board/themes/skein.css` — 增强动效 (流光呼吸/状态脉动)
- `assets/board/themes/skein-dark.css` — 新建暗色主题
- `assets/board/switcher.js` — 注册暗主题 + localStorage 持久化
- `assets/webapp/src/input.css` — 暗色模式 + 流沙动效层 + 入场/数字动画
- `assets/webapp/dist/app.css` — 重建产物
- 原型文件 (临时, 评审后可删)

范围外 (非目标):
- 环境层粒子系统 (性能负担, 用户未选)
- 生产级 Web App 重构 (huashu 只做原型)
- 新增主题色相 (沿用蓝金, status 色相语义固定)

## 验收标准
- [ ] 浅/暗双模式视觉一致 (蓝金 + 玻璃 + 流沙动效), switcher 切换平滑
- [ ] 结构层动效: 卡 hover 流光描边 / active 状态脉动 / glass sheen
- [ ] 细节层动效: 数字递增 / 列表项入场过渡
- [ ] `prefers-reduced-motion` 尊重, 动效降级
- [ ] 视口外动效暂停 (board 已有 voff 门控, webapp 需补)
- [ ] huashu 原型经用户评审确认
- [ ] webapp dist/app.css 重建, 无构建报错

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-theme-glass-gold`)
