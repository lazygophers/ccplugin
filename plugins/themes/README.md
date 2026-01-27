# Style Plugins - UI 设计风格插件库

`plugins/style/` 目录包含 12 个现代 UI 设计风格插件，覆盖 2025 年主流设计趋势，为不同项目提供完整的设计系统、配置规范和实现指南。

## 🎨 设计风格概览

### 现代创意风格

| 风格 | 描述 | 特点 | 适用场景 |
|------|------|------|---------|
| **[Glassmorphism](style-glassmorphism/)** | 玻璃态设计 | 模糊、透明、分层、虚实感 | 现代应用、SaaS、游戏 UI |
| **[Neumorphism](style-neumorphism/)** | 新拟态设计 | 柔和阴影、浮起效果、3D 视觉 | 极简风格、柔和界面 |
| **[Gradient](style-gradient/)** | 渐变艺术 | 流动渐变、色彩过渡、艺术表现 | 创意应用、品牌站点 |
| **[Neon](style-neon/)** | 霓虹赛博 | 发光效果、高饱和、科幻感 | 游戏、电商、品牌体验 |

### 经典怀旧风格

| 风格 | 描述 | 特点 | 适用场景 |
|------|------|------|---------|
| **[Retro](style-retro/)** | 复古怀旧 | 80-90s 审美、温暖色调、复古排版 | 复古品牌、创意站点、娱乐应用 |
| **[Brutalism](style-brutalism/)** | 野兽派设计 | 原始边界、大胆排版、功能优先 | 艺术网站、极简应用 |

### 简洁极简风格

| 风格 | 描述 | 特点 | 适用场景 |
|------|------|------|---------|
| **[Minimal](style-minimal/)** | 极简主义 | 留白、简洁排版、功能至上 | 高级品牌、极简产品 |
| **[Dark](style-dark/)** | 暗黑模式 | 深色背景、高对比、WCAG AAA | 所有应用的夜间模式 |
| **[Pastel](style-pastel/)** | 柔和粉彩 | 淡雅色彩、温柔质感、舒适感 | 女性向应用、生活类应用 |

### 高对比鲜明风格

| 风格 | 描述 | 特点 | 适用场景 |
|------|------|------|---------|
| **[Vibrant](style-vibrant/)** | 充满活力 | 高对比、高饱和、动态感 | 电商、媒体、娱乐 |
| **[HighContrast](style-highcontrast/)** | 高对比无障碍 | WCAG AAA、清晰界限、包容性 | 政府应用、无障碍平台 |

### 高端优雅风格

| 风格 | 描述 | 特点 | 适用场景 |
|------|------|------|---------|
| **[Luxe](style-luxe/)** | 奢华高端 | 金色元素、大理石纹理、精致排版 | 奢侈品、高端服务、VIP 应用 |

## 🚀 选择风格指南

### 按项目类型选择

**📱 电商/消费应用**
- 🎨 推荐：[Vibrant](style-vibrant/) - 吸引眼球、鼓励购买
- 🎨 备选：[Neon](style-neon/) - 创意突出、印象深刻

**💼 企业/B2B 应用**
- 🎨 推荐：[Minimal](style-minimal/) - 专业、清晰、易用
- 🎨 备选：[Dark](style-dark/) - 现代、专业

**🎮 游戏/娱乐**
- 🎨 推荐：[Neon](style-neon/) - 科幻感、沉浸感
- 🎨 备选：[Glassmorphism](style-glassmorphism/) - 现代、视觉深度

**🎨 创意/设计类**
- 🎨 推荐：[Brutalism](style-brutalism/) - 艺术感、独特风格
- 🎨 备选：[Gradient](style-gradient/) - 艺术表现

**👗 生活/女性向应用**
- 🎨 推荐：[Pastel](style-pastel/) - 温柔、舒适
- 🎨 备选：[Luxe](style-luxe/) - 精致、优雅

**🌙 需要深色模式**
- 🎨 推荐：[Dark](style-dark/) - WCAG AAA 标准

**♿ 无障碍优先**
- 🎨 推荐：[HighContrast](style-highcontrast/) - WCAG AAA 标准

**💎 高端品牌**
- 🎨 推荐：[Luxe](style-luxe/) - 奢华、精致
- 🎨 备选：[Minimal](style-minimal/) - 高级感

## 📖 Skills 文档结构

每个风格插件都遵循 **多文件 skills 结构**：

- `SKILL.md` - 核心特性和快速开始（300-400 行）
- `reference.md` - 完整配置规范
- `examples.md` - 实现示例和最佳实践

**浏览指南**：查阅相应风格目录下的这些文件

## 💻 实现支持

所有风格插件都包含：

- Pure CSS 实现
- Tailwind CSS 配置
- React 组件示例
- Vue 组件示例
- Next.js 集成示例

## ✅ 规范遵循

所有 style 插件都遵循 **Anthropic 官方技能创作最佳实践**

详见：[.claude/skills/plugin-skills-authoring.md](../../.claude/skills/plugin-skills-authoring.md)

## 🎯 常见场景

- **现代 SaaS 应用**：Glassmorphism + Dark Mode
- **极简设计**：Minimal
- **无障碍应用**：HighContrast
- **复古风格**：Retro 或 Brutalism
- **奢华品牌**：Luxe
- **充满活力的电商**：Vibrant 或 Neon

## 📚 使用步骤

1. 根据项目类型选择合适的风格
2. 阅读风格的 SKILL.md 了解核心特性
3. 查看 reference.md 获取完整规范
4. 参考 examples.md 的代码示例
5. 集成到你的项目中

## 📝 相关文档

- **Code 插件**：[README.md](../README.md)
- **Skills 编写规范**：[.claude/skills/plugin-skills-authoring.md](../../.claude/skills/plugin-skills-authoring.md)
- **项目架构**：[CLAUDE.md](../../CLAUDE.md)

---

**选择合适的设计风格，为你的项目创造独特的视觉体验！** 🎨
