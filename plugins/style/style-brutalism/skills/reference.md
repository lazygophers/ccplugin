# 配置参考

以下是完整的实现指南和最佳实践：

# Brutalism - 野兽派设计风格规范

野兽派设计强调原始、大胆和功能性，优先级排序功能而非美学，采用粗体排版和几何形态。

## 核心特征

**设计原则**：
- 原始性（raw materials）
- 大胆排版
- 明确的边界
- 功能至上

**颜色系统**：
```css
--black: #000000;
--white: #ffffff;
--gray: #404040;
--accent: #ff0000;  /* 可选强调色 */
```

**排版**：
```css
--font-family: Georgia, "Courier New", monospace;
--font-weight: bold | 700;
--font-size: 32px (heading);
--letter-spacing: 0.1em;  /* 宽松间距 */
```

## 实现要点

**大胆边框**：
```css
.brutal-box {
  border: 4px solid #000;
  background: #ffffff;
  padding: 24px;
  margin: 16px;
}
```

**粗体排版**：
```css
.brutal-heading {
  font-weight: 900;
  font-size: 48px;
  line-height: 1;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
```

## 应用场景

- 🎨 艺术项目
- 📰 编辑设计
- 🏛️ 建筑投资组合
- 💡 概念设计

## 网格系统

```css
/* 严格网格对齐 */
--grid-size: 8px;
--column-gap: 32px;
--row-gap: 24px;
```

## DO & DON'T

✅ **DO**:
- 大胆、清晰的排版
- 强烈的对比
- 明确的网格对齐
- 功能性优先

❌ **DON'T**:
- 过度装饰
- 模糊的边界
- 细线条
- 隐藏信息

## 空间分配

| 元素 | 大小 |
|------|------|
| 外边距 | 16-32px |
| 内边距 | 16-24px |
| 边框厚度 | 2-4px |

## 配色变体

**单色**：仅黑白
**二色**：黑 + 单色强调
**高对比**：黑 + 白 + 充满活力的强调

## 参考资源

- Swiss Design Movement
- Dieter Rams 十大设计原则
- Brutalism Design Archive


## 浏览器支持

所有现代浏览器均支持相关 CSS 属性。
对于旧版浏览器，请考虑使用 polyfill 或降级方案。
