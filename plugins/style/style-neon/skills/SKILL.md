# Neon - 霓虹赛博设计风格规范

霓虹风格设计采用发光高饱和色彩，创建充满能量的科幻感 UI，适合科技和创意项目。

## 核心特征

**色彩系统**：
```css
--neon-cyan: #00d9ff;     /* 青蓝 */
--neon-pink: #ff006e;     /* 霓虹粉 */
--neon-purple: #b900d9;   /* 紫色 */
--neon-green: #00ff41;    /* 霓虹绿 */
--neon-yellow: #ffff00;   /* 荧光黄 */
--bg-dark: #0a0a0a;       /* 黑色背景 */
```

**发光效果**：
```css
--glow: 0 0 10px currentColor;
--glow-strong: 0 0 20px currentColor, 0 0 40px currentColor;
```

## 实现要点

**发光文本**：
```css
.neon-text {
  color: #00d9ff;
  text-shadow: 
    0 0 10px #00d9ff,
    0 0 20px #00d9ff,
    0 0 40px #00d9ff;
}
```

**边框发光**：
```css
.neon-border {
  border: 2px solid #ff006e;
  box-shadow: 0 0 10px #ff006e inset,
              0 0 10px #ff006e;
}
```

## 应用场景

- 🎮 游戏 UI
- 🚀 科技初创
- 💿 音乐应用
- 🌐 虚拟世界体验

## 色彩搭配方案

**方案 A：青粉对比**
- 主色：#00d9ff
- 次色：#ff006e
- 背景：#0a0a0a

**方案 B：全彩霓虹**
- 使用 3-4 个互补色
- 保持等饱和度
- 避免色彩混乱

## DO & DON'T

✅ **DO**:
- 深色背景（＃000000-#1a1a1a）
- 有意义的色彩对比
- 节制的动画和闪烁
- 提供无障碍替代方案

❌ **DON'T**:
- 过度闪烁（易发癫痫）
- 所有元素发光
- 浅色背景
- 忽视可读性

## 对比度注意

| 组合 | 对比度 |
|------|--------|
| 青 + 黑 | 8.5:1 ✅ |
| 粉 + 黑 | 5.4:1 ✅ |
| 黄 + 黑 | 13.4:1 ✅ |

## 性能优化

```css
/* 使用 filter 替代 text-shadow */
.neon {
  filter: drop-shadow(0 0 10px #00d9ff);
}
```

## 参考资源

- Cyberpunk 2077 UI Design
- Synthwave 美学参考
- Neon Design Inspiration
