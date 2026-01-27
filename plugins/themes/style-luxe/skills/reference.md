# 配置参考

以下是完整的实现指南和最佳实践：

# Luxe - 奢华高端设计风格规范

奢华风格设计采用黄金元素、大理石纹理和精致排版，传达高端、优雅和premium 品牌形象。

## 核心特征

**色彩系统**：
```css
/* 奢华调色板 */
--gold: #d4af37;         /* 黄金 */
--dark-navy: #1a1a2e;    /* 深海军蓝 */
--cream: #f5f1de;        /* 奶油色 */
--marble-gray: #a8a8a8;  /* 大理石灰 */
--black: #0a0a0a;        /* 漆黑 */
--rose-gold: #b76e79;    /* 玫瑰金 */
```

**排版**：
```css
--font-display: Didot, Georgia, serif;  /* 优雅衬线 */
--font-body: Lora, serif;               /* 平衡衬线 */
--font-weight: 300 | 400 | 600;        /* 轻-中等-粗体 */
--letter-spacing: 0.15em;               /* 宽松间距 */
```

## 实现要点

**黄金强调**：
```css
.luxury-accent {
  color: #d4af37;
  text-shadow: 0 0 1px rgba(212, 175, 55, 0.3);
  border-bottom: 2px solid #d4af37;
}
```

**大理石效果**：
```css
.marble-bg {
  background: linear-gradient(
    135deg,
    #f5f1de 0%,
    #e8e4d5 25%,
    #d4d0c8 50%,
    #c0bbb3 100%
  );
}
```

## 应用场景

- 💎 高端珠宝品牌
- 🍾 奢侈酒类
- ✨ 美容护肤
- 🏨 高级酒店

## 配色方案

**方案 A：黄金经典**
- 主色：深海军蓝
- 强调：黄金
- 背景：奶油色

**方案 B：玫瑰金现代**
- 主色：黑色
- 强调：玫瑰金
- 背景：奶油色

## 排版层级

| 元素 | 大小 | 权重 | 间距 |
|------|------|------|------|
| H1 | 48px | 300 | 0.2em |
| H2 | 36px | 400 | 0.15em |
| Body | 16px | 400 | 0.1em |

## DO & DON'T

✅ **DO**:
- 优雅的排版选择
- 充足的留白
- 有目的的黄金使用
- 高质量的视觉资产

❌ **DON'T**:
- 过度黄金化
- 廉价的配色
- 拥挤的布局
- 不匹配的字体

## 间距系统

```css
--spacing-unit: 8px;
--padding: 32px 48px;  /* 宽松内边距 */
--margin: 24px 0;      /* 开放空间 */
```

## 参考资源

- Luxury Brand Websites
- High-end Design Inspiration
- Dribbble Premium Designs


## 浏览器支持

所有现代浏览器均支持相关 CSS 属性。
对于旧版浏览器，请考虑使用 polyfill 或降级方案。
