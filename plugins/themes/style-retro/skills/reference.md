# 配置参考

以下是完整的实现指南和最佳实践：

# Retro - 复古怀旧设计风格规范

复古风格设计融合 80-90 年代审美，采用温暖色调、曲线排版和复古字体，唤起怀旧情感。

## 核心特征

**色彩系统**：
```css
/* 温暖调色板 */
--retro-red: #ff6b6b;      /* 复古红 */
--retro-orange: #ffa600;   /* 橙色 */
--retro-yellow: #ffde00;   /* 黄色 */
--retro-purple: #c06c84;   /* 复古紫 */
--retro-cream: #f4e4c1;    /* 奶油色 */
--retro-brown: #6f5d46;    /* 棕色 */
```

**排版**：
```css
/* 复古字体 */
--font-display: "Courier New", monospace;  /* 打字机 */
--font-body: Georgia, serif;               /* 衬线 */
--font-accent: Comic Sans, cursive;        /* 装饰体 */
```

## 实现要点

**80s 风格**：
- 鲜艳的对比色
- 网格图案
- 厚重的轮廓

**90s 风格**：
- 渐变背景
- 浮动阴影
- 斜体元素

```css
.retro-box {
  background: linear-gradient(135deg, #ff6b6b, #ffa600);
  border: 3px solid #6f5d46;
  box-shadow: 
    5px 5px 0px #f4e4c1,
    10px 10px 0px #6f5d46;
  transform: skewX(-5deg);
}
```

## 应用场景

- 🎪 创意项目
- 👗 时尚品牌
- 🎵 音乐应用
- 📸 社交媒体

## 字体推荐

| 类型 | 推荐字体 |
|------|---------|
| 标题 | VT323, Space Mono |
| 正文 | Courier Prime, IBM Plex Mono |
| 装饰 | Fredoka One, Righteous |

## DO & DON'T

✅ **DO**:
- 拥抱大胆的色彩组合
- 使用重厚的边框
- 应用怀旧图形
- 混合字体风格

❌ **DON'T**:
- 过度使用闪烁效果
- 忽视可读性
- 所有元素都复古化
- 忽视现代用户体验

## 色彩配方

```
主配色方案：互补色 (±120°)
示例：红 (#ff6b6b) + 绿 (#6bc82f) + 紫 (#c06c84)
```

## 参考资源

- Figma Retro Design UI Kit
- 80s Inspiration Pinterest
- 90s Web Archive


## 浏览器支持

所有现代浏览器均支持相关 CSS 属性。
对于旧版浏览器，请考虑使用 polyfill 或降级方案。
