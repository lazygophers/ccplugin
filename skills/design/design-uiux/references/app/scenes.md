# App 媒介 · 场景自适应

同一 App 要适配多场景。场景轴决定何时切换、切什么。布局见 [layout.md](layout.md)，组件见 [components.md](components.md)；色彩 / 风格在姊妹 skill `design-color`。

## 场景轴速查

| 场景轴 | 切换什么 | 触发 |
|--------|---------|------|
| 亮 / 暗模式 | 中性阶、背景、强调色 | 系统偏好 / 手动 |
| 平台 | 组件形态、导航、手势 | iOS / Android / 桌面 |
| 横竖屏 | 布局重排（列表→分栏） | 设备旋转 |
| 手机 / 平板 | 分栏（Split View）、密度 | size class |
| 动态字体 | 字号跟随系统辅助设置 | Dynamic Type / Font Scale |
| 离线 / 弱网 | 功能降级、缓存、提示 | 网络状态 |
| 首次启动 | 引导 / 权限请求 / 空状态 | onboarding |
| 后台 / 前台 | 刷新策略、推送 | 生命周期 |

## 亮 / 暗模式

- 系统跟随 + 手动覆盖
- 暗模式重调中性阶、降饱和、提对比（色彩模板在姊妹 skill `design-color`）
- 图片 / 图标备亮暗两套或自适应

## 平台适配

- 用条件编译 / 平台分支渲染差异化组件（iOS Sheet vs Android Dialog）
- 手势遵循平台（iOS 边缘返回、Android 返回键）
- 权限请求文案与时机随平台规范

## 横竖屏与尺寸分级

- 手机竖屏：单栏滚动
- 手机横屏：列表→分栏（Master-Detail），或保持竖屏锁定（游戏 / 视频）
- 平板：Split View（侧栏 + 主区）、多任务分屏
- 桌面：自由缩放窗口，布局流式响应

iOS size class（Compact / Regular）决定布局；Android 用 `sw600dp` 等资源限定符。

## 动态字体与无障碍

- 跟随系统字号设置（iOS Dynamic Type / Android Font Scale）
- 布局在最大字号下不塌（文本可换行、不截断关键信息）
- VoiceOver / TalkBack：所有交互有 `accessibilityLabel`
- 降低动效（iOS Reduce Motion / Android Remove Animations）尊重

## 离线 / 弱网

- 本地缓存最近数据，离线可看
- 写操作排队，恢复后同步
- 明确提示离线状态，禁假装成功
- 图片 / 媒体降级加载（缩略图、占位）

## 首次启动与空状态

- 引导：≤3 步，可跳过
- 权限：用时请求，说明为什么需要，别启动全要
- 空状态：插画 + 说明 + CTA，不只是「暂无数据」

## 自检

- [ ] 亮 / 暗模式均可读
- [ ] 横竖屏布局不塌
- [ ] 最大字号下不截断
- [ ] 离线有降级与提示
- [ ] 空状态 / 错误态 / 加载态有设计
