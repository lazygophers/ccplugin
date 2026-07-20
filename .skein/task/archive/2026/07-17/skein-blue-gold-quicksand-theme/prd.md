# webapp 背景纯蓝金流沙微光主题 — PRD

## 目标
webapp 背景重做为纯蓝金双色流沙微光, 去掉非蓝金杂色 (surface-bg 浅灰等), 全链路审计清色。**status 状态色 (pending/active/check/done/failed 五色相) 保留** — 只清非状态元素的非蓝金色。

## 边界
**内**:
- input.css 令牌根: 浅主题 surface-bg (#EEF1FB 等淡灰蓝) 改纯蓝金; body 背景重做流沙微光
- dist/app.css 重建 (tailwind 编译产物, 跟 input.css)
- page.js 内嵌 style 硬编码色审计 (board.js #fff 等中性色评估)
**外**:
- **status 色相不动** (--h-pending/active/check/done/failed 五色保, 用户明确保留)
- 暗主题 surface-bg (深蓝黑) 保留 (已偏蓝)
- #fff / rgba(0,0,0) 中性色保留 (非色相)
- 玻璃流沙层 (card 流光描边/进度条蓝金) 已是蓝金, 不动
- 不改布局结构 (只改色)

## 审计结果 (非蓝金杂色)
- **surface-bg 浅主题**: `#EEF1FB / #E9EFFB / #DBEAFB` (淡灰蓝, 偏灰非纯蓝金) → **改纯蓝金**
- **surface-bg 暗主题**: `#0B1220 / #0E1729 / #0A0F1C` (深蓝黑) → 保 (已偏蓝)
- **board.js 内嵌 #fff**: badge 文字/border/q-chip/cmd-new hover → 中性白, 保
- **#1a1206**: 暗主题 btn-primary 金字 → 金系, 保
- **rgba(0,0,0,.45)**: glass-shadow → 中性阴影, 保

## 改动

### t1-bg-quicksand-rewrite (input.css body 背景 + surface-bg)
- **浅主题 surface-bg** 改纯蓝金系: 从淡灰蓝 (#EEF1FB 等) 改为蓝金渐变底色 (如 #F0EEF8 → #F5F0E6 蓝金过渡, 或 oklch 派生)
- **body 背景** (line 98-107 浅 / 109-123 暗) 重做纯蓝金流沙微光:
  - 浅: 蓝金双色径向渐变 + 微光 (现状已 accent2 蓝 + skein-gold 金, 但叠了 surface 灰层 → 去灰层, 纯蓝金流沙)
  - 暗: 现状金沙星点已蓝金 → 保, 微调去杂色
- 可加 CSS animation 流沙缓慢流动 (background-position 动画, 微光闪烁)
- 暗主题 surface-bg (深蓝黑) 保

### t2-dist-rebuild + page-audit
- dist/app.css 重建 (input.css 改后跑 tailwind 重建, 复用项目 dev 重建脚本)
- page.js 内嵌 style 审计: 确认无非蓝金硬编码色 (board.js #fff 中性保, 其他清)
- 全链路 grep 确认无非蓝金漏网

## 验收标准
- [ ] 浅主题 surface-bg 为纯蓝金色 (无灰调)
- [ ] body 背景纯蓝金流沙微光 (无灰层杂色)
- [ ] status 五色相保留 (--st-pending/active/check/done/failed 不变)
- [ ] dist/app.css 重建后含新背景
- [ ] page.js 无非蓝金硬编码色 (#fff 中性除外)
- [ ] 全链路 grep无非蓝金漏网 (除 status + 中性)
- [ ] 浅/暗双主题都纯蓝金
- [ ] 无 console error, 布局不破

## 索引
- 任务/子任务/调度: task.json (`skein.py subtask list skein-blue-gold-quicksand-theme`)
