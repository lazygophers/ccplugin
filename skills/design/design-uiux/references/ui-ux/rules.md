# UX 规则全清单 · 10 类可操作检查项

> 来源：ui-ux-pro-max-skill 的 `quick-reference.md`，10 大类共 ~170 条可操作 UX 规则。
> 每条含：规则名 + 标准 + 依据（Apple HIG / Material Design / WCAG）。
> 用法：UI review/audit 时按类扫；落地某类时查具体规则。优先级 1→10 决定先查哪类。

## 优先级总表

| 优先级 | 类别 | 影响 | 关键检查 | 反模式 |
|--------|------|------|---------|--------|
| 1 | 无障碍 | CRITICAL | 对比度 4.5:1、alt 文本、键盘导航、aria-label | 去焦点环、图标按钮无标签 |
| 2 | 触控与交互 | CRITICAL | 最小 44×44px、间距 8px+、加载反馈 | 只靠 hover、0ms 瞬变 |
| 3 | 性能 | HIGH | WebP/AVIF、懒加载、预留空间(CLS<0.1) | 布局抖动、CLS 累积 |
| 4 | 风格选择 | HIGH | 匹配产品类型、一致性、SVG 图标(非 emoji) | 扁平与拟物混用、emoji 当图标 |
| 5 | 布局与响应式 | HIGH | 移动优先断点、viewport meta、无横向滚动 | 横向滚动、固定 px 宽、禁缩放 |
| 6 | 排版与色彩 | MEDIUM | 基准 16px、行高 1.5、语义色 token | 正文 <12px、灰叠灰、裸 hex |
| 7 | 动画 | MEDIUM | 时长 150-300ms、动效传意、空间连续 | 纯装饰动画、动画 width/height、无 reduced-motion |
| 8 | 表单与反馈 | MEDIUM | 可见 label、错误就近、helper text、渐进披露 | placeholder 当 label、错误只在顶部、信息过载 |
| 9 | 导航模式 | HIGH | 可预测返回、底栏≤5、深链 | 导航过载、返回行为破损、无深链 |
| 10 | 图表与数据 | LOW | 图例、tooltip、可访问配色 | 只靠颜色传意 |

---

## 1. 无障碍（CRITICAL）

- `color-contrast` - 正文对比度 ≥4.5:1（大字 ≥3:1）(Material Design)
- `focus-states` - 交互元素可见焦点环(2-4px)(Apple HIG, MD)
- `alt-text` - 有意义图片加描述性 alt
- `aria-labels` - 纯图标按钮加 aria-label；原生用 accessibilityLabel(Apple HIG)
- `keyboard-nav` - Tab 顺序匹配视觉顺序；全键盘支持(Apple HIG)
- `form-labels` - 用 label 配 for 属性
- `skip-links` - 键盘用户可跳转到主内容
- `heading-hierarchy` - h1→h6 连续，不跳级
- `color-not-only` - 不只靠颜色传信息(加图标/文字)
- `dynamic-type` - 支持系统文字缩放；文字增长时不截断(Apple Dynamic Type, MD)
- `reduced-motion` - 尊重 prefers-reduced-motion；请求时减/禁动画(Apple, MD)
- `voiceover-sr` - 有意义的 accessibilityLabel/Hint；VoiceOver/读屏逻辑阅读顺序(Apple HIG, MD)
- `escape-routes` - 模态与多步流程提供取消/返回(Apple HIG)
- `keyboard-shortcuts` - 保留系统与 a11y 快捷键；拖拽提供键盘替代(Apple HIG)

## 2. 触控与交互（CRITICAL）

- `touch-target-size` - 最小 44×44pt(Apple) / 48×48dp(Material)；必要时扩展命中区超视觉边界
- `touch-spacing` - 触控目标间最小 8px/8dp 间距(Apple HIG, MD)
- `hover-vs-tap` - 主交互用点击/轻触；不只靠 hover
- `loading-buttons` - 异步操作时禁用按钮；显 spinner 或进度
- `error-feedback` - 错误信息就近问题字段
- `cursor-pointer` - 可点击元素加 cursor-pointer(Web)
- `gesture-conflicts` - 主内容避免水平滑动；优先垂直滚动
- `tap-delay` - 用 touch-action: manipulation 减少 300ms 延迟(Web)
- `standard-gestures` - 一致使用平台标准手势；不重定义(如滑动返回、捏合缩放)(Apple HIG)
- `system-gestures` - 不拦截系统手势(控制中心、返回滑动等)(Apple HIG)
- `press-feedback` - 按压有视觉反馈(涟漪/高亮;MD state layers)
- `haptic-feedback` - 确认与重要操作用触觉反馈；避免滥用(Apple HIG)
- `gesture-alternative` - 不只靠手势交互；关键操作必提供可见控件
- `safe-area-awareness` - 主触控目标远离刘海、灵动岛、手势条与屏幕边缘
- `no-precision-required` - 避免要求像素级精准点击小图标或细边缘
- `swipe-clarity` - 滑动操作必显明确暗示(箭头、标签、教程)
- `drag-threshold` - 拖拽前用移动阈值避免误拖

## 3. 性能（HIGH）

- `image-optimization` - 用 WebP/AVIF、响应式图(srcset/sizes)、非关键资源懒加载
- `image-dimension` - 声明 width/height 或用 aspect-ratio 防布局位移(CLS)
- `font-loading` - 用 font-display: swap/optional 避免不可见文字(FOIT)；预留空间减位移(MD)
- `font-preload` - 仅预加载关键字体；不在每个变体上滥用 preload
- `critical-css` - 优先首屏 CSS(内联关键 CSS 或早加载样式表)
- `lazy-loading` - 非 hero 组件懒加载(动态 import / 路由级分割)
- `bundle-splitting` - 按路由/特性分割代码(React Suspense / Next.js dynamic)减初始加载与 TTI
- `third-party-scripts` - 第三方脚本 async/defer 加载；审计移除不必要(MD)
- `reduce-reflows` - 避免频繁布局读写；批量 DOM 读后写
- `content-jumping` - 异步内容预留空间避免布局跳(CLS)
- `lazy-load-below-fold` - 首屏以下图与重媒体用 loading="lazy"
- `virtualize-lists` - 50+ 项列表虚拟化提升内存与滚动性能
- `main-thread-budget` - 每帧工作 <16ms 维持 60fps；重任务移出主线程(HIG, MD)
- `progressive-loading` - >1s 操作用骨架屏/微光替代长阻塞 spinner(Apple HIG)
- `input-latency` - 点击/滚动输入延迟 <100ms(Material 响应标准)
- `tap-feedback-speed` - 点击后 100ms 内给视觉反馈(Apple HIG)
- `debounce-throttle` - 高频事件(滚动、resize、输入)用 debounce/throttle
- `offline-support` - 提供离线状态消息与基础降级(PWA / 移动)
- `network-fallback` - 慢网络提供降级模式(低清图、减动画)

## 4. 风格选择（HIGH）

- `style-match` - 风格匹配产品类型(查 [industry-rules.md](industry-rules.md) 获推荐)
- `consistency` - 所有页面用同一风格
- `no-emoji-icons` - 用 SVG 图标(Heroicons、Lucide)，非 emoji
- `color-palette-from-product` - 从产品/行业选色板(配色走姊妹 skill `design-color`)
- `effects-match-style` - 阴影/模糊/圆角与所选风格对齐(玻璃/扁平/粘土等)
- `platform-adaptive` - 尊重平台惯例(iOS HIG vs Material)：导航、控件、排版、动效
- `state-clarity` - hover/pressed/disabled 状态视觉可辨且不破风格(MD state layers)
- `elevation-consistent` - 卡片/抽屉/模态用一致的高程/阴影阶；禁随机阴影值
- `dark-mode-pairing` - 亮/暗变体一起设计，保持品牌、对比、风格一致
- `icon-style-consistent` - 全产品用一套图标集/视觉语言(线宽、圆角)
- `system-controls` - 优先原生/系统控件；仅品牌需要时定制(Apple HIG)
- `blur-purpose` - 模糊用于表示背景 dismissal(模态、抽屉)，非装饰(Apple HIG)
- `primary-action` - 每屏只有一个主 CTA；次操作视觉从属(Apple HIG)

## 5. 布局与响应式（HIGH）

- `viewport-meta` - width=device-width initial-scale=1(永不禁缩放)
- `mobile-first` - 移动优先设计，再扩展到平板与桌面
- `breakpoint-consistency` - 用系统断点(如 375 / 768 / 1024 / 1440)
- `readable-font-size` - 移动正文最小 16px(避免 iOS 自动缩放)
- `line-length-control` - 移动每行 35-60 字符；桌面 60-75 字符
- `horizontal-scroll` - 移动无横向滚动；内容适配视口宽
- `spacing-scale` - 用 4pt/8dp 递增间距系统(Material Design)
- `touch-density` - 组件间距对触控舒适：不挤、不致误触
- `container-width` - 桌面一致 max-width(max-w-6xl / 7xl)
- `z-index-management` - 定义分层 z-index 阶(如 0 / 10 / 20 / 40 / 100 / 1000)
- `fixed-element-offset` - 固定导航/底栏必须为底层内容预留安全 padding
- `scroll-behavior` - 避免干扰主滚动的嵌套滚动区
- `viewport-units` - 移动优先 min-h-dvh 而非 100vh
- `orientation-support` - 横屏保持布局可读可操作
- `content-priority` - 移动先显核心内容；折叠或隐藏次要内容
- `visual-hierarchy` - 用大小、间距、对比建立层级——非仅靠颜色

## 6. 排版与色彩（MEDIUM）

- `line-height` - 正文用 1.5-1.75
- `line-length` - 限制每行 65-75 字符
- `font-pairing` - 标题/正文字体个性匹配(详见姊妹 skill `design-color` 的 typography.md)
- `font-scale` - 一致字号阶(如 12 14 16 18 24 32)
- `contrast-readability` - 浅底用深色文字(如 slate-900 on white)
- `text-styles-system` - 用平台字号系统：iOS 11 Dynamic Type / Material 5 type roles(HIG, MD)
- `weight-hierarchy` - 用 font-weight 强化层级：粗标题(600-700)、常规正文(400)、中标签(500)(MD)
- `color-semantic` - 定义语义色 token(primary, secondary, error, surface, on-surface)非裸 hex(Material 色彩系统)
- `color-dark-mode` - 暗模式用降饱和/更亮色调变体，非反色；单独测对比(HIG, MD)
- `color-accessible-pairs` - 前景/背景对必达 4.5:1(AA)或 7:1(AAA)；用工具验证(WCAG, MD)
- `color-not-decorative-only` - 功能色(错误红、成功绿)必含图标/文字；避免纯色传意(HIG, MD)
- `truncation-strategy` - 优先换行而非截断；截断时用省略号并经 tooltip/展开提供全文(Apple HIG)
- `letter-spacing` - 尊重平台默认字间距；正文避免紧排(HIG, MD)
- `number-tabular` - 数据列、价格、计时器用 tabular/等宽数字防布局位移
- `whitespace-balance` - 有意用留白分组相关项、分隔版块；避免视觉杂乱(Apple HIG)

## 7. 动画（MEDIUM）

- `duration-timing` - 微交互用 150-300ms；复杂过渡 ≤400ms；避免 >500ms(MD)
- `transform-performance` - 只用 transform/opacity；避免动画 width/height/top/left
- `loading-states` - 加载超 300ms 显骨架或进度指示
- `excessive-motion` - 每视图最多动画 1-2 个关键元素
- `easing` - 进入用 ease-out、退出用 ease-in；UI 过渡避免 linear
- `motion-meaning` - 每个动画必表达因果，非纯装饰(Apple HIG)
- `state-transition` - 状态变化(hover/active/展开/折叠/模态)应平滑动画，非生硬切换
- `continuity` - 页/屏过渡保持空间连续(共享元素、方向性滑动)(Apple HIG)
- `parallax-subtle` - 视差少用；必尊重 reduced-motion 且不致眩晕(Apple HIG)
- `spring-physics` - 优先弹簧/物理曲线而非 linear 或 cubic-bezier 求自然感(Apple HIG 流体动画)
- `exit-faster-than-enter` - 退出动画短于进入(约进入时长 60-70%)求响应感(MD motion)
- `stagger-sequence` - 列表/网格项入场交错 30-50ms/项；避免齐刷刷或过慢(MD)
- `shared-element-transition` - 屏间用共享元素/hero 过渡求视觉连续(MD, HIG)
- `interruptible` - 动画必可中断；用户点击/手势立即取消进行中动画(Apple HIG)
- `no-blocking-animation` - 动画期间永不阻塞用户输入；UI 保持可交互(Apple HIG)
- `fade-crossfade` - 同容器内内容替换用交叉淡入(MD)
- `scale-feedback` - 可点击卡片/按钮按压时微缩放(0.95-1.05)；释放恢复(HIG, MD)
- `gesture-feedback` - 拖拽、滑动、捏合必提供跟踪手指的实时视觉响应(MD Motion)
- `hierarchy-motion` - 用 translate/scale 方向表达层级：从下进入=更深、向上退出=返回(MD)
- `motion-consistency` - 全局统一时长/缓动 token；所有动画共享同一节奏与感觉
- `opacity-threshold` - 淡出元素不应在 opacity 0.2 以下徘徊；要么全淡要么保持可见
- `modal-motion` - 模态/抽屉应从触发源动画(缩放+淡入或滑入)求空间语境(HIG, MD)
- `navigation-direction` - 前进导航向左/上动画；后退向右/下——保持方向逻辑一致(HIG)
- `layout-shift-avoid` - 动画必不致布局重排或 CLS；位置变化用 transform

## 8. 表单与反馈（MEDIUM）

- `input-labels` - 每个输入有可见 label(非仅 placeholder)
- `error-placement` - 错误显在相关字段下方
- `submit-feedback` - 提交时显加载再成功/错误态
- `required-indicators` - 标记必填字段(如星号)
- `empty-states` - 无内容时给有用消息与操作
- `toast-dismiss` - toast 3-5s 自动消失
- `confirmation-dialogs` - 破坏性操作前确认
- `input-helper-text` - 复杂输入下方提供持久 helper text，非仅 placeholder(Material Design)
- `disabled-states` - 禁用元素用降透明度(0.38-0.5)+光标变化+语义属性(MD)
- `progressive-disclosure` - 渐进披露复杂选项；不一上来压垮用户(Apple HIG)
- `inline-validation` - 失焦时验证(非按键)；用户输完才显错(MD)
- `input-type-keyboard` - 用语义 input 类型(email, tel, number)触发正确移动键盘(HIG, MD)
- `password-toggle` - 密码字段提供显示/隐藏切换(MD)
- `autofill-support` - 用 autocomplete / textContentType 属性让系统自动填充(HIG, MD)
- `undo-support` - 破坏性或批量操作允许撤销(如"撤销删除"toast)(Apple HIG)
- `success-feedback` - 完成操作用简短视觉反馈确认(勾、toast、色闪)(MD)
- `error-recovery` - 错误消息必含明确恢复路径(重试、编辑、帮助链接)(HIG, MD)
- `multi-step-progress` - 多步流程显步骤指示或进度条；允许返回(MD)
- `form-autosave` - 长表单应自动保存草稿防意外关闭丢数据(Apple HIG)
- `sheet-dismiss-confirm` - 有未保存更改时关闭抽屉/模态前确认(Apple HIG)
- `error-clarity` - 错误消息必说明原因+如何修复(非仅"输入无效")(HIG, MD)
- `field-grouping` - 逻辑分组相关字段(fieldset/legend 或视觉分组)(MD)
- `read-only-distinction` - 只读状态应与禁用视觉与语义不同(MD)
- `focus-management` - 提交出错后自动聚焦第一个无效字段(WCAG, MD)
- `error-summary` - 多错误时顶部显摘要带各字段锚链接(WCAG)
- `touch-friendly-input` - 移动输入高度 ≥44px 满足触控目标(Apple HIG)
- `destructive-emphasis` - 破坏性操作用语义 danger 色(红)并与主操作视觉分离(HIG, MD)
- `toast-accessibility` - toast 必不抢焦点；读屏用 aria-live="polite"(WCAG)
- `aria-live-errors` - 表单错误用 aria-live 区或 role="alert" 通知读屏(WCAG)
- `contrast-feedback` - 错误与成功状态色必达 4.5:1 对比(WCAG, MD)
- `timeout-feedback` - 请求超时必显明确反馈带重试选项(MD)

## 9. 导航模式（HIGH）

- `bottom-nav-limit` - 底栏导航最多 5 项；图标配标签(Material Design)
- `drawer-usage` - 抽屉/侧栏用于次级导航，非主操作(Material Design)
- `back-behavior` - 返回导航必可预测且一致；保留滚动/状态(Apple HIG, MD)
- `deep-linking` - 所有关键屏必经深链/URL 可达，便于分享与通知(Apple HIG, MD)
- `tab-bar-ios` - iOS：顶层导航用底栏 Tab Bar(Apple HIG)
- `top-app-bar-android` - Android：主结构用 Top App Bar 配导航图标(Material Design)
- `nav-label-icon` - 导航项必同时有图标与文字标签；纯图标导航损害可发现性(MD)
- `nav-state-active` - 当前位置必视觉高亮(颜色、粗细、指示)于导航(HIG, MD)
- `nav-hierarchy` - 主导航(标签/底栏)与次导航(抽屉/设置)必清晰分离(MD)
- `modal-escape` - 模态与抽屉必提供明确关闭/取消暗示；移动可下滑关闭(Apple HIG)
- `search-accessible` - 搜索必易达(顶栏或标签)；提供最近/建议查询(MD)
- `breadcrumb-web` - Web：3+ 层深用面包屑辅助定位(MD)
- `state-preservation` - 返回导航必恢复前次滚动位置、筛选状态、输入(HIG, MD)
- `gesture-nav-support` - 支持系统手势导航(iOS 滑回、Android 预测返回)不冲突(HIG, MD)
- `tab-badge` - 导航项徽章少用表未读/待处理；用户访问后清除(HIG, MD)
- `overflow-menu` - 操作超空间时用溢出/更多菜单，而非硬塞(MD)
- `bottom-nav-top-level` - 底栏仅用于顶层屏；永不嵌套子导航(MD)
- `adaptive-navigation` - 大屏(≥1024px)优先侧栏；小屏用底/顶导航(Material Adaptive)
- `back-stack-integrity` - 永不静默重置导航栈或意外跳首页(HIG, MD)
- `navigation-consistency` - 导航位置跨所有页面保持一致；不按页类型变
- `avoid-mixed-patterns` - 同一层级不混 Tab + 侧栏 + 底栏
- `modal-vs-navigation` - 模态必不用于主导航流；它们打断用户路径(HIG)
- `focus-on-route-change` - 页面切换后焦点移到主内容区供读屏用户(WCAG)
- `persistent-nav` - 核心导航必从深层页可达；不在子流程中完全隐藏(HIG, MD)
- `destructive-nav-separation` - 危险操作(删账户、登出)必与常规导航项视觉与空间分离(HIG, MD)
- `empty-nav-state` - 导航目标不可用时解释原因，而非静默隐藏(MD)

## 10. 图表与数据（LOW）

- `chart-type` - 图表类型匹配数据类型(趋势→折线、对比→柱状、占比→饼/环)
- `color-guidance` - 用可访问配色；避免红/绿仅对色盲用户(WCAG, MD)
- `data-table` - 提供表格替代供无障碍；仅图表对读屏不友好(WCAG)
- `pattern-texture` - 用图案、纹理或形状补充颜色，使数据不靠颜色可辨(WCAG, MD)
- `legend-visible` - 始终显图例；位置近图表，非滚动折叠下方的脱离(MD)
- `tooltip-on-interact` - hover(Web)或 tap(移动)显 tooltip/数据标签示精确值(HIG, MD)
- `axis-labels` - 标注轴含单位与可读刻度；移动避免截断或旋转标签
- `responsive-chart` - 图表小屏必重排或简化(如横条替代竖条、减刻度)
- `empty-data-state` - 无数据时显有意义空状态("暂无数据"+指引)，非空白图(MD)
- `loading-chart` - 图表数据加载时用骨架/微光占位；不显空轴框
- `animation-optional` - 图表入场动画必尊重 prefers-reduced-motion；数据应立即可读(HIG)
- `large-dataset` - 1000+ 数据点时聚合或采样；提供下钻看详情而非全渲染(MD)
- `number-formatting` - 轴与标签用区域感知数字/日期/货币格式(HIG, MD)
- `touch-target-chart` - 交互图表元素(点、段)必 ≥44pt 命中区或触摸扩展(Apple HIG)
- `no-pie-overuse` - >5 类避免饼/环；改柱状求清晰
- `contrast-data` - 数据线/柱与背景 ≥3:1；数据文字标签 ≥4.5:1(WCAG)
- `legend-interactive` - 图例应可点击切换系列可见性(MD)
- `direct-labeling` - 小数据集直接在图上标值减少眼动
- `tooltip-keyboard` - tooltip 内容必键盘可达，不只靠 hover(WCAG)
- `sortable-table` - 数据表必支持排序，aria-sort 指示当前排序状态(WCAG)
- `axis-readability` - 轴刻度必不挤；保持可读间距，小屏自动跳过
- `data-density` - 限制每图信息密度避免认知过载；需要时拆多图
- `trend-emphasis` - 强调数据趋势而非装饰；避免重渐变/阴影遮蔽数据
- `gridline-subtle` - 网格线应低对比(如 gray-200)不与数据竞争
- `focusable-elements` - 交互图表元素(点、柱、片)必键盘可导航(WCAG)
- `screen-reader-summary` - 提供文本摘要或 aria-label 描述图表关键洞察供读屏(WCAG)
- `error-state-chart` - 数据加载失败必显错误消息带重试，非破损/空图
- `export-option` - 数据密集产品提供图表数据 CSV/图导出
- `drill-down-consistency` - 下钻交互必保持清晰返回路径与层级面包屑
- `time-scale-clarity` - 时序图必清晰标注时间粒度(日/周/月)且可切换

---

## 与本目录其他文件的关系

| 文件 | 职责 | 与本文件 |
|------|------|---------|
| [principles.md](principles.md) | 设计原则(层级/对比/对齐/接近/一致/反馈/容错) | 原则层→本文件是规则层(原则的可操作落地) |
| [information-architecture.md](information-architecture.md) | 导航/内容优先级/心智模型 | 本文件 §9 导航模式是其可操作补充 |
| [interaction-design.md](interaction-design.md) | 交互模式/状态完整性/反馈/防错 | 本文件 §2 §7 §8 是其可操作补充 |
| [usability-a11y.md](usability-a11y.md) | Nielsen 10 / WCAG / 键盘 / 对比 | 本文件 §1 无障碍是其检查清单化 |
| [scenarios.md](scenarios.md) | 14 主流场景深度 UX | 场景导向→本文件是规则导向，互补 |
| [industry-rules.md](industry-rules.md) | 100 行业设计决策 | 行业→风格/配色；本文件是跨行业的通用 UX 规则 |
| [charts.md](charts.md) | 25 图表类型选型 | 本文件 §10 图表与数据是其 UX 规则层 |
