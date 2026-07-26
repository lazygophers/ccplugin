# examples 设计参考提取 (过程证据)

源: plugins/tools/skein/docs/examples/index.html (172K, 2218 行)。

## 配色 token (tailwind config 内联 examples:14-46)
- ocean 5 阶: foam #e8f4fa / shallow #74b9e8 / mid #429cd1 / deep #237bb8 / abyss #0f4d75 (:16-22)
- whiteSand 3 色: pearl #fffefb / shell #fdf6e8 / cream #f8f0dc (:24-28)
- goldSand 4 色: light #f0d9a0 / mid #e6c88b / deep #d4b066 / sunset #c89548 (:30-35)
- night 3 阶: base #0f2033 / mid #162c42 / deep #091420 (:37-41)
- 语义: success #48bb78 / warning #ed8936 / danger #e53e3e (:43-45)
- font: Inter / system-ui (:47-49)

## antd 组件范式 (6 tab, examples:460-466 tab-btn)
6 区: colors / components / charts / motion / timeline / dag。

组件清单 (按 antd 6 大类, h4 行号):
- General: Button :798, Icon :821, Grid 24 列 :869, Layout :895
- Layout/Navigation: Menu 水平 :949, Menu 垂直含子菜单 :960, Breadcrumb :1004, Pagination :991, Steps :1017
- DataEntry: Input :1057, Select :1077, DatePicker :1087, Checkbox :1098, Radio :1105, Switch :1115
- DataDisplay: Table :1143, Tag :1229, Badge :1240, Avatar :1258, Tooltip :1273, Card :1289, Skeleton :1410
- Feedback: Modal 原生 dialog :1347, Alert :1324, Message :1366, Spin :1377, Progress :1384

colors 区组件 demo: Button :729, Input :740, 状态标签 Badge :754。

## 布局视觉原语
- .glass 玻璃卡 (圆角+边框+半透) examples:439-451 多处。
- .bg-fluid-light / .bg-fluid-dark (linear-gradient 白沙→奶油→浪花 / night 渐变) :57-66。
- .bg-wave 浪花→近海渐变 :68-70。
- .hover-float translateY+shadow 上浮 :136-141。
- tab 切换: .tab-btn + .tab-btn.active :167-184, data-tab-target + JS 切 active。
- .text-gradient-ocean 渐变文字 :129。
- .tl-dot Timeline 时间轴点 (cur 态 tlPulse) :207-214; 纵向 + 横向 (:1905) Timeline。
- DAG 节点态: 待执行 (ocean.shallow 边 + whiteSand.pearl 填) :304; 进行中 (ocean.deep 填 + dagPulse) :325-331。
- .antd-spin 旋转 :246; .antd-shimmer 骨架闪动 :249-255。
- drop-shadow(0 4px 8px rgba(0,0,0,.15)) 海滩阴影 :339。

## 动效语言 (keyframes examples:144-214)
- waveShift 6s 海浪水平偏移 :144-148 (.animate-wave)。
- staggerIn 0.6s cubic-bezier(0.22,1,0.36,1) 级联入场 :150-157 (.animate-stagger-in)。
- pulseDot 1.6s 通用脉冲 :159-165 (.pulse-dot)。
- tlPulse 时间轴当前点 :207-214 (prefers-reduced-motion 直接 animation:none)。
- dagPulse 1.6s DAG 进行中节点 opacity :325-331。
- antdSpin 旋转 :245; antdShimmer 骨架 :255。

## 重写可复用清单
- token (16 色+字体): 替代或并存现 oklch 体系。
- 组件 (≥20): Button/Icon/Grid/Layout/Menu/Breadcrumb/Pagination/Steps/Input/Select/DatePicker/Checkbox/Radio/Switch/Table/Tag/Badge/Avatar/Tooltip/Card/Skeleton/Modal/Alert/Message/Spin/Progress。
- 原语 (≥8): glass/bg-fluid/bg-wave/hover-float/text-gradient/tab-btn/tl-dot/dag-node。
- 动效 (≥7): waveShift/staggerIn/pulseDot/tlPulse/dagPulse/antdSpin/antdShimmer。
