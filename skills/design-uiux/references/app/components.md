# App 媒介 · 组件与手势

原生组件优先（免费获得无障碍 + 平台习惯 + 性能）。自定义只在原生不能满足品牌表达时。布局见 [layout.md](layout.md)，场景见 [scenes.md](scenes.md)；色彩 / 风格在姊妹 skill `design-color`。

## 组件选型原则

1. **用户要完成什么任务？** 任务决定组件
2. **状态空间全不全？** default / pressed / focused / disabled / loading / error / empty / selected
3. **平台原生有没有？** 有就用，省无障碍与性能成本

## 组件族

| 组件族 | 关键点 |
|--------|--------|
| 导航栏 | 标题居中（iOS）/ 左（Android）；行动按钮位置随平台 |
| 列表 / Collection | 行高、分隔、滑动操作、下拉刷新、上拉加载 |
| 表单 | 输入聚焦滚入可视区、键盘遮挡处理、实时校验 |
| 底部 Sheet | 确认操作、多选项；可拖拽高度 |
| Toast / Snackbar | 非阻断，带可选行动按钮（Android Snackbar） |
| 权限弹窗 | 用时请求；说明为什么需要 |
| 启动屏 | 极简，快速过渡到内容 |
| 空状态 | 插画 + 说明 + CTA |
| FAB（悬浮行动） | Android 主操作入口；桌面少用 |

## 状态完整性

每个交互组件覆盖：

```
default → pressed → focused → disabled
                       ↘ loading / error / empty / selected
```

漏状态 = 半成品。设计组件时列全状态再实现。

## 手势设计

| 手势 | 用途 | 可见性 |
|------|------|--------|
| 点击 | 主操作 | 明确（按钮样） |
| 长按 | 次级菜单 / 进入编辑 | 需暗示或引导 |
| 滑动 | 切页 / 出操作 / 删除 | 需部分可见或提示 |
| 捏合 | 缩放 | 内容可缩时自然 |
| 拖拽 | 排序 / 移动 | 拖把手柄暗示 |

手势不可见 = 用户发现不了。关键手势首次使用要有引导或可见暗示。

## 组件 token 化

组件值取自项目 token，不硬编码：

```
Button.Primary: bg=primary, text=primary-contrast, radius=radius-md, h=44pt
Button.Secondary: bg=bg-card, border=border, text=text
```

换肤 / 暗模式 / 密度一处生效全局生效；色彩模板在姊妹 skill `design-color`。

## 可访问性基线

- 所有交互可 VoiceOver / TalkBack 到达，有 `accessibilityLabel`
- 触控目标 ≥ 44pt（iOS）/ 48dp（Android）
- 焦点顺序合理
- 动效尊重 Reduce Motion

## 自检

- [ ] 原生组件优先
- [ ] 状态全覆盖
- [ ] 触控目标达标
- [ ] 关键手势有可见暗示
- [ ] 无障碍标签齐全
