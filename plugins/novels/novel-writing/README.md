# Novel Writing Plugin

> 网络小说创作插件 - 提供完整的小说创作辅助功能

## 简介

Novel Writing 是一个专为网络小说创作设计的 Claude Code 插件，提供从故事构思到文风调整的全方位创作支持。无论你是新手作者还是资深写手，都能通过本插件提升创作效率和作品质量。

## 核心功能

### 📖 故事构思 (Story Brainstorm)
- 题材选择和主题挖掘
- 世界观和背景设定
- 核心冲突设计
- 故事前提优化

### 👥 角色设定 (Character Design)
- 角色档案建立
- 性格特征设计
- 成长弧线规划
- 人物关系网络

### 📊 情节发展 (Plot Development)
- 主线和支线设计
- 冲突升级机制
- 高潮和转折布局
- 节奏控制技巧

### 💬 对话生成 (Dialogue Generation)
- 符合角色性格的对话
- 对话推进情节技巧
- 潜台词设计
- 群戏对话管理

### ✍️ 文风调整 (Style Tuning)
- 多种文风类型支持
- 叙事视角选择
- 语言风格调节
- 氛围营造技巧

### 📝 大纲管理 (Outline Management)
- 三级大纲体系
- 线索管理
- 伏笔追踪
- 节奏规划

## 快速开始

### 安装插件

```bash
# 从市场安装
claude plugin install novel-writing@ccplugin-market

# 从本地安装
claude plugin install ./plugins/novels/novel-writing
```

### 使用命令

```bash
# 故事构思
/novel-writing brainstorm

# 角色设定
/novel-writing character

# 情节设计
/novel-writing plot

# 对话生成
/novel-writing dialogue

# 大纲管理
/novel-writing outline
```

### 使用 Agents

```bash
# 故事顾问
@story-agent 帮我构思一个科幻题材的故事

# 角色设计师
@character-agent 设计一个复杂的反派角色

# 情节架构师
@plot-agent 如何设计一个引人入胜的开局

# 对话大师
@dialogue-agent 生成一段紧张的对峙对话

# 文风顾问
@style-agent 如何营造悬疑紧张的氛围
```

## 技能体系

| 技能 | 说明 | 适用场景 |
|------|------|---------|
| story-brainstorm | 故事构思 | 新作品策划、题材选择 |
| character-design | 角色设定 | 人物塑造、关系设计 |
| plot-development | 情节发展 | 剧情推进、冲突设计 |
| dialogue-generation | 对话生成 | 对话创作、语言优化 |
| style-tuning | 文风调整 | 风格统一、氛围营造 |
| outline-management | 大纲管理 | 结构规划、进度跟踪 |

## 适用类型

本插件支持所有网络小说类型，包括但不限于：

- 玄幻修仙
- 都市言情
- 科幻未来
- 历史架空
- 游戏竞技
- 悬疑推理
- 武侠仙侠

## 创作流程建议

1. **构思阶段**：使用 story-brainstorm 确定题材和主题
2. **设定阶段**：使用 character-design 设计主要角色
3. **规划阶段**：使用 outline-management 制定大纲
4. **创作阶段**：结合 plot-development 和 dialogue-generation 进行写作
5. **优化阶段**：使用 style-tuning 统一文风和调整节奏

## 最佳实践

### 故事构思
- 从核心冲突出发，确保故事有张力
- 世界观要自洽，设定要有逻辑性
- 主题要有深度，避免流于表面

### 角色塑造
- 主角要有明确的目标和成长空间
- 反派要有合理的动机，不能脸谱化
- 配角要有独特性格，避免工具人

### 情节设计
- 开局要抓人，前三章决定读者去留
- 高潮要震撼，情绪要推到极致
- 结局要圆满，伏笔要有回收

### 对话创作
- 每个角色要有独特的说话方式
- 对话要推进情节，避免无效对话
- 适当使用潜台词，增加层次感

### 文风把控
- 保持风格统一，避免前后割裂
- 根据场景调整节奏，张弛有度
- 语言要精炼，避免啰嗦重复

## 示例场景

### 构思新作品

```
用户：我想写一个都市题材的小说，但没有灵感
Assistant：使用 /novel-writing brainstorm 命令

输出：
- 题材方向：都市重生、商战争霸、娱乐圈等
- 核心冲突：重生者利用未来知识改变命运 vs 命运的反噬
- 独特卖点：金融危机背景、跨国商战、情感线交织
```

### 设计角色

```
用户：帮我设计一个复杂的反派角色
Assistant：调用 @character-agent

输出：
- 基础信息：商界大佬，表面儒雅实则冷酷
- 核心动机：因童年创伤形成扭曲价值观
- 成长弧线：从成功商人到偏执狂的转变
- 与主角关系：亦师亦敌，有情感纠葛
```

## 贡献指南

欢迎贡献新的技能和功能！

1. Fork 本仓库
2. 创建特性分支
3. 提交 Pull Request

## 许可证

AGPL-3.0-or-later

## 相关链接

- [项目主页](https://github.com/lazygophers/ccplugin)
- [插件文档](https://github.com/lazygophers/ccplugin/tree/master/plugins/novels/novel-writing)
- [问题反馈](https://github.com/lazygophers/ccplugin/issues)
