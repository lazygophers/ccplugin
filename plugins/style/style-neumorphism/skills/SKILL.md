# Neumorphism - 新拟态设计风格规范

新拟态（Neumorphic）设计结合了拟物化和极简主义，使用柔和阴影创建 3D 浮起或凹陷效果。

## 核心特征

**视觉特性**：
- 双阴影系统（亮、暗）
- 圆角整数化（8-16px）
- 单色或接近单色（对比 5-10%）
- 浮起或按压视觉

**颜色系统**：
```css
--bg-base: #e0e5ec;
--text-primary: #3a3a3a;
--shadow-light: rgba(255, 255, 255, 0.7);
--shadow-dark: rgba(170, 170, 170, 0.3);
```

**阴影配置**：
```css
/* 浮起效果 */
--shadow-raised: 
  6px 6px 16px #bebebe,
  -6px -6px 16px #ffffff;

/* 按压效果 */
--shadow-pressed:
  inset 6px 6px 16px #bebebe,
  inset -6px -6px 16px #ffffff;
```

## 实现要点

**CSS 双阴影**：
```css
.neumorphic {
  background: #e0e5ec;
  border-radius: 12px;
  box-shadow: 
    6px 6px 16px rgba(0, 0, 0, 0.1),
    -6px -6px 16px rgba(255, 255, 255, 0.7);
}
```

**按钮交互**：
```css
.button:active {
  box-shadow: inset 6px 6px 16px rgba(0, 0, 0, 0.1);
}
```

## 应用场景

- 🎮 移动应用按钮
- ⚙️ 设置面板
- 📊 仪表板卡片
- 💬 聊天应用

## 特性对比

| 特性 | Neumorphism | Skeuomorphism |
|------|------------|---------------|
| 颜色 | 单色范围 | 多色彩 |
| 深度 | 柔和阴影 | 强烈阴影 |
| 易用性 | 可能混淆 | 直观易懂 |
| 可访问性 | 需注意对比 | 较好 |

## DO & DON'T

✅ **DO**:
- 确保足够的对比度（AAA 标准）
- 使用清晰的交互反馈
- 保持一致的阴影距离
- 测试光源方向

❌ **DON'T**:
- 混合多种渐变
- 使用过度饱和色彩
- 忽视键盘导航
- 过度复杂的阴影

## 浏览器兼容性

- Chrome/Edge: ✅ 完全支持
- Safari: ✅ iOS 15+
- Firefox: ✅ 支持但需前缀

## 参考资源

- [Neumorphism.io](https://neumorphism.io/)
- Dribbble Neumorphism 集合
- Design Trends 2025 对比
