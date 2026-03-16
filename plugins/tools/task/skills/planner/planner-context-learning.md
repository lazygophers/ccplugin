# Planner 上下文学习指南

## 概述

基于 [Agentic Context Engineering](https://arxiv.org/html/2602.20478v1) 和 [Claude Code 记忆系统](https://code.claude.com/docs/zh-CN/memory)，planner 采用三层上下文学习策略，系统性地积累项目知识。

## 三层上下文学习（ACE 模式）

### Tier 1 - 热记忆（Constitution，总是加载）

**优先级最高，必须收集**：

- **项目基本信息**：语言、框架、构建工具
- **技术栈版本**：runtime 版本、主要依赖版本
- **架构模式**：单体/微服务、MVC/领域驱动、三层架构等
- **项目上下文文件**：
  - `CLAUDE.md` 或 `.claude/CLAUDE.md`（项目持久指令）
  - `README.md`（项目概览）
  - `.claude/memory/MEMORY.md`（前 200 行自动加载）

**收集方式**：
- 扫描目录结构（`Glob` 或 `serena:list_dir`）
- 读取关键配置（`package.json`、`go.mod`、`pyproject.toml`）
- 查看项目文档（`README.md`、`CLAUDE.md`）

### Tier 2 - 专业知识（Specialist，嵌入领域知识）

**根据任务类型收集**：

- **代码风格约定**：命名规范、文件组织、注释风格
- **测试策略**：单元测试框架、覆盖率要求、mock 策略
- **架构决策**：设计模式、依赖注入、错误处理方式
- **团队约定**：Git 工作流、PR 规范、版本管理

**收集方式**：
- 读取代码风格配置（`.editorconfig`、`.prettierrc`、`eslint.config.js`）
- 查看现有代码实现模式（选取 2-3 个代表性文件）
- 检查测试文件的编写风格
- 读取开发文档（`CONTRIBUTING.md`、`DEVELOPMENT.md`）
- 读取 `.claude/rules/` 目录规则文件

### Tier 3 - 冷记忆（Knowledge Base，按需检索）

**任务相关时检索**（来自 `.claude/memory/` 目录）：

- **历史规划决策**：读取 `planning-patterns.md`
- **成功/失败模式**：查看有效的 agent/skills 组合
- **架构决策记录**：读取 `architecture-decisions.md`
- **技术债记录**：已知问题、待优化点
- **相似功能实现**：通过代码搜索查找

**使用记忆系统的优势**：
- MEMORY.md 前 200 行自动加载，包含核心信息索引
- 详细内容按需读取，节省上下文空间
- 记忆跨会话积累，避免重复学习
- 记忆文件可人工审阅和编辑

## 项目上下文文件管理

### 标准文件结构

```
项目根目录/
├── CLAUDE.md 或 .claude/CLAUDE.md    # 项目持久指令
├── .claude/
│   ├── settings.json                  # 项目设置
│   ├── rules/                         # 规则文件（可选）
│   │   ├── code-style.md              # 代码风格规则
│   │   ├── testing.md                 # 测试约定
│   │   └── architecture.md            # 架构规则
│   └── memory/                        # 自动记忆目录
│       ├── MEMORY.md                  # 记忆索引
│       ├── planning-patterns.md       # 规划模式
│       └── architecture-decisions.md  # 架构决策
└── README.md                          # 项目概览
```

### 读取顺序

1. **CLAUDE.md**（必读，自动加载）：项目级持久指令
2. **`.claude/rules/`**（按需）：特定主题规则，可能包含路径特定规则
3. **`.claude/memory/`**（按需）：历史积累的项目知识
4. **README.md**（推荐）：项目概览和快速开始

### 验证内容一致性

- 技术栈版本是否匹配实际依赖
- 架构描述是否与代码结构一致
- 约定是否仍在遵循（通过代码样本验证）
- CLAUDE.md 中的构建命令是否有效

### 建议更新上下文文件

| 发现内容 | 建议操作 | 目标文件 |
|---------|---------|---------|
| 新的架构决策或设计模式 | 记录到架构规则或记忆 | `.claude/rules/architecture.md` 或 `.claude/memory/architecture-decisions.md` |
| 技术栈升级或依赖变更 | 更新技术栈信息 | `CLAUDE.md` 或 `.claude/memory/tech-stack.md` |
| 新的代码风格约定 | 添加到规则文件 | `.claude/rules/code-style.md` |
| 成功的规划模式 | 记录到规划模式 | `.claude/memory/planning-patterns.md` |
| 构建或测试命令变更 | 更新项目指令 | `CLAUDE.md` |

### 避免冲突

- 检查 CLAUDE.md、`.claude/rules/` 和 `.claude/memory/` 中的冲突指令
- 优先级：规则文件（更具体）> CLAUDE.md（项目级）> 记忆文件（历史积累）
- 发现冲突时通过 `SendMessage` 提醒用户

## Spec-Driven Planning（规范驱动计划）

基于 [Spec-Driven Development](https://monday.com/blog/rnd/software-development-plan/) 理念，在任务分解前生成结构化规范。

### 规范四个维度

1. **功能规范**（What）：
   - 核心功能描述
   - 输入输出定义
   - 边界条件和约束

2. **技术规范**（How）：
   - 采用的设计模式（基于项目现有模式）
   - 需要的依赖库（优先使用现有依赖）
   - 与现有代码的集成方式

3. **质量规范**（Quality）：
   - 测试策略（遵循项目测试约定）
   - 性能要求（如有）
   - 安全考虑（基于项目安全规范）

4. **合规规范**（Compliance）：
   - 遵循的代码风格（从 Tier 2 学习）
   - 遵循的架构约定（从项目理解报告）
   - 必须使用的工具/框架（基于项目技术栈）

### 规范检查清单

- [ ] 规范是否符合项目现有风格？
- [ ] 规范是否考虑了现有架构约束？
- [ ] 规范是否复用了现有组件？
- [ ] 规范是否与 CLAUDE.md 中的指令一致？
- [ ] 规范是否遵循 `.claude/rules/` 中的规则？

## 上下文积累与复用

### 记忆系统工作流

1. **会话开始时**：
   - MEMORY.md 前 200 行自动加载
   - 获取项目核心信息和索引

2. **信息收集阶段**：
   - 根据任务类型读取相关主题文件
   - 规划任务时读取 `planning-patterns.md`
   - 架构变更时读取 `architecture-decisions.md`

3. **计划设计阶段**：
   - 基于记忆中的模式设计任务分解
   - 复用成功的 agent/skills 组合
   - 遵循记录的架构约定

4. **计划完成后**：
   - 发现新的架构决策或约定时，建议更新记忆
   - 通过 `SendMessage` 提示用户

### 配置记忆存储位置

在 `.claude/settings.json` 中配置：

```json
{
  "autoMemoryDirectory": "./.claude/memory"
}
```

### 记忆内容组织

```markdown
# MEMORY.md（索引文件）

## 项目概览
- 语言：Go 1.21
- 框架：Gin + GORM
- 架构：三层架构（handler → service → repository）

## 关键约定
- 命名：驼峰命名，接口以 I 开头
- 错误处理：统一错误码 + 结构化日志（zerolog）
- 测试：表驱动测试 + gomock，覆盖率 ≥ 80%

## 详细文档索引
- 架构决策：见 `architecture-decisions.md`
- 规划模式：见 `planning-patterns.md`
- 技术栈：见 `tech-stack.md`
- 代码约定：见 `conventions.md`

## 最近更新
- 2026-03-16: 添加 Repository 模式约定
- 2026-03-15: 更新测试覆盖率要求到 80%
```

## 阶段转换控制

基于 [Agentic workflows](https://medium.com/quantumblack/agentic-workflows-for-software-development-dc8e64f4a79d) 最佳实践。

### 前置条件检查

从"信息收集"到"计划设计"必须满足：

- [ ] Tier 1 上下文学习完成
- [ ] 项目理解报告输出
- [ ] 上下文文件验证完成
- [ ] 四类关键信息收集完成（目标、依赖、现状、边界）
- [ ] 无未解决的疑问

### 转换失败处理

1. **识别缺失信息**：列出具体缺少的前置条件
2. **提供补充建议**：通过 `SendMessage` 说明并给出建议
3. **等待信息补充**：暂停规划流程

## 参考资料

- [Claude 如何记住您的项目](https://code.claude.com/docs/zh-CN/memory) - 官方记忆系统文档
- [Codified Context: Infrastructure for AI Agents](https://arxiv.org/html/2602.20478v1) - ACE 三层上下文系统
- [Agentic workflows for software development](https://medium.com/quantumblack/agentic-workflows-for-software-development-dc8e64f4a79d) - 项目上下文文件验证
- [Software Development Plan: 2026 Guide](https://monday.com/blog/rnd/software-development-plan/) - Spec-Driven Development
