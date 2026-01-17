# UI 设计风格插件集合

本目录包含 12 个专业的 UI 设计风格插件，为 Claude Code 提供完整的现代设计系统参考。

## 🎨 风格插件清单

### 1. **Glassmorphism** - 玻璃态
- **特色**：模糊、透明、分层光线效果
- **用途**：现代应用、金融科技、游戏 UI
- **参考**：macOS Big Sur、Windows 11
- **插件**：`style-glassmorphism`

### 2. **Neumorphism** - 新拟态
- **特色**：柔和阴影、浮起效果、3D 视觉
- **用途**：移动应用、设置面板、仪表板
- **对比**：平衡拟物化和极简主义
- **插件**：`style-neumorphism`

### 3. **Minimal** - 极简主义
- **特色**：留白充足、清晰排版、功能至上
- **用途**：新闻网站、内容平台、企业官网
- **原则**：优先级排序、消除装饰
- **插件**：`style-minimal`

### 4. **Dark Mode** - 暗黑模式
- **特色**：深色背景、高对比、WCAG AAA 标准
- **用途**：通用暗黑主题、编辑器、夜间模式
- **优点**：护眼、省电（OLED）、现代感
- **插件**：`style-dark`

### 5. **Neon** - 霓虹赛博
- **特色**：发光效果、高饱和色彩、科幻感
- **用途**：游戏 UI、科技初创、创意项目
- **灵感**：Cyberpunk 2077、Synthwave 美学
- **插件**：`style-neon`

### 6. **Retro** - 复古怀旧
- **特色**：80-90s 审美、温暖色调、斜体排版
- **用途**：创意项目、时尚品牌、音乐应用
- **特点**：鲜艳对比、曲线设计、打字机字体
- **插件**：`style-retro`

### 7. **Brutalism** - 野兽派
- **特色**：原始边界、大胆排版、功能优先
- **用途**：艺术项目、建筑投资组合、编辑设计
- **哲学**：原始性、清晰层级、大胆声明
- **插件**：`style-brutalism`

### 8. **Pastel** - 柔和粉彩
- **特色**：淡雅色彩、圆角、柔和阴影
- **用途**：儿童应用、生活方式、教育平台
- **感觉**：温柔、舒适、梦幻
- **插件**：`style-pastel`

### 9. **Vibrant** - 充满活力
- **特色**：高饱和色彩、大胆对比、动态布局
- **用途**：创意机构、音乐产品、时尚品牌
- **能量**：充满活力、视觉冲击、大胆表达
- **插件**：`style-vibrant`

### 10. **Luxe** - 奢华高端
- **特色**：黄金元素、大理石纹理、精致排版
- **用途**：高端珠宝、奢侈品、酒店服务
- **品质**：优雅、premium、精致
- **插件**：`style-luxe`

### 11. **High Contrast** - 高对比无障碍
- **特色**：WCAG AAA、清晰界限、包容性设计
- **用途**：政府网站、医疗平台、通用可访问
- **标准**：严格对比度（≥7:1）、键盘导航
- **插件**：`style-highcontrast`

### 12. **Gradient** - 渐变艺术
- **特色**：流动渐变、色彩过渡、艺术表现
- **用途**：创意投资组合、营销落地页
- **特性**：多维度变化、视觉丰富、动态感
- **插件**：`style-gradient`

## 📁 文件结构

每个风格插件都包含：

```
style-{name}/
├── .claude-plugin/
│   └── plugin.json          # 插件元数据
└── skills/
    └── SKILL.md             # 设计规范文档（~300 行）
                             # 包含：核心特征、色彩系统、实现要点、
                             # 应用场景、DO & DON'T、参考资源
```

## 🚀 使用方式

### 作为 Claude Code 插件加载
```bash
# 从 marketplace.json 自动加载
# 插件会出现在 Claude Code 的插件列表中
```

### 查阅设计规范
```
打开任意插件的 skills/SKILL.md 文件
获取该风格的完整设计规范、色彩系统、实现代码示例
```

### 应用到项目
1. 阅读对应风格的 SKILL.md
2. 了解核心特征和色彩系统
3. 使用提供的 CSS 变量和代码片段
4. 一致地应用到整个项目

## 🎯 选择风格指南

| 项目类型 | 推荐风格 |
|---------|--------|
| 现代 SaaS | Glassmorphism, Dark Mode |
| 创意机构 | Vibrant, Retro, Gradient |
| 企业官网 | Minimal, Luxe |
| 儿童应用 | Pastel, Retro |
| 游戏 | Neon, Glassmorphism |
| 无障碍优先 | High Contrast, Dark Mode |
| 艺术项目 | Brutalism, Gradient, Vibrant |
| 移动优先 | Neumorphism, Pastel, Minimal |

## 📊 2025 年设计趋势

这 12 个风格反映了 2025 年最新的设计趋势：

✅ **保持强势**：
- Glassmorphism（现代应用标配）
- Dark Mode（用户需求驱动）
- Minimal（经典常青）
- High Contrast（无障碍重视）

🔥 **新兴趋势**：
- Neumorphism 改进版本
- Neon + Glassmorphism 混搭
- Brutalism 复兴
- Retro 怀旧回潮

📈 **增长方向**：
- Gradient 艺术应用
- Pastel 人文关怀
- Vibrant 大胆表达
- Luxe 高端市场

## 🛠️ 技术支持

所有插件提供：
- ✅ CSS 3 实现
- ✅ Tailwind CSS 配置
- ✅ CSS 变量系统
- ✅ 响应式设计方案
- ✅ 可访问性指南
- ✅ 性能优化建议

## 📚 学习资源

### 在线工具
- [Glassmorphism.io](https://glassmorphism.com/)
- [Neumorphism.io](https://neumorphism.io/)
- [WebAIM 对比度检查器](https://webaim.org/resources/contrastchecker/)
- [Color Hunt - 配色灵感](https://colorhunt.co/)

### 参考资料
- [2025 年 UI 设计趋势研究](https://www.thewebfactory.us/blogs/30-best-web-design-trends-styles-for-2025/)
- [Material Design 3](https://m3.material.io/)
- [WCAG 2.1 可访问性指南](https://www.w3.org/WAI/WCAG21/quickref/)

## 🤝 贡献

如果您有新的设计风格想法或改进建议，欢迎提交 PR！

## 📝 许可证

所有风格插件均采用 MIT 许可证。

---

**最后更新**：2025 年 1 月 17 日  
**总计插件数**：12 个  
**总行数**：~3,600 行设计规范文档
