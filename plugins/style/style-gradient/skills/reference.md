# 配置参考

以下是完整的实现指南和最佳实践：

# Gradient - 渐变艺术设计风格规范

渐变风格设计采用流动的色彩过渡、多维度变化和艺术表现，创建视觉丰富和动态感的 UI。

## 核心特征

**渐变类型**：
```css
/* 线性渐变 */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* 径向渐变 */
background: radial-gradient(circle, #667eea, #764ba2);

/* 锥形渐变 */
background: conic-gradient(from 0deg, #667eea, #764ba2);
```

**色彩系统**：
```css
/* 渐变调色板 */
--gradient-sunrise: linear-gradient(90deg, #ff6b35, #f7931e);
--gradient-ocean: linear-gradient(135deg, #667eea, #764ba2);
--gradient-forest: linear-gradient(45deg, #134e5e, #71b280);
--gradient-sunset: linear-gradient(180deg, #ff6b9d, #c44569);
```

## 实现要点

**多重渐变**：
```css
.gradient-complex {
  background: 
    linear-gradient(45deg, #667eea 0%, #764ba2 50%, #f093fb 100%),
    linear-gradient(-45deg, #4facfe 0%, #00f2fe 100%);
  background-blend-mode: screen;
}
```

**文本渐变**：
```css
.gradient-text {
  background: linear-gradient(90deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

## 应用场景

- 🎨 创意投资组合
- 🚀 科技产品营销
- 🎵 音乐应用
- 💫 艺术项目

## 渐变方案库

**方案 A：紫蓝梦幻**
```
从 #667eea → #764ba2 → #f093fb
```

**方案 B：橙粉温暖**
```
从 #ff6b35 → #f7931e → #ffb6c1
```

**方案 C：青绿自然**
```
从 #134e5e → #71b280 → #4facfe
```

## DO & DON'T

✅ **DO**:
- 使用 3-5 个停止点
- 平滑的色彩过渡
- 考虑明度变化
- 测试可访问性

❌ **DON'T**:
- 过多颜色停止点
- 高对比中断
- 仅依赖渐变表现
- 忽视性能

## 动画渐变

```css
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.animated-gradient {
  background-size: 200% 200%;
  animation: gradientShift 3s ease infinite;
}
```

## 性能优化

```css
/* 使用 will-change */
.gradient {
  will-change: background;
}

/* 避免过度渲染 */
contain: layout style paint;
```

## 对比度考虑

使用渐变时确保：
- 文本可读性 ≥4.5:1
- 边界清晰可见
- 色盲用户可区分

## 渐变生成工具

- [Gradient Designer](https://www.gradients.com/)
- [ColorSpace](https://mycolor.space/)
- [Easing Gradients](https://easing-gradients.github.io/)

## 参考资源

- Awesome Gradients Collections
- Design Inspiration Sites
- CSS-Tricks Gradient Guides


## 浏览器支持

所有现代浏览器均支持相关 CSS 属性。
对于旧版浏览器，请考虑使用 polyfill 或降级方案。
