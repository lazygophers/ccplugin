---
name: new-plugin
description: 创建新插件 - 插件结构设计、manifest配置、组件创建、MCP集成、文档生成
user-invocable: true
context: fork
model: sonnet
skills:
  - plugin-skills
  - documentation
---

# 创建新插件（New Plugin）

**迁移说明**：本 Skill 迁移自 `.claude/commands/new.md`（Commands已废弃，符合2026规范）

## 概览

本 Skill 提供完整的插件开发流程，从需求分析到测试验证，帮助用户快速创建高质量的 Claude Code 插件。

**核心能力**：
1. 需求分析和规划
2. 插件结构设计
3. Manifest 配置
4. 组件创建（Agents、Skills、Hooks、Scripts）
5. MCP/LSP 集成
6. 文档生成
7. 测试验证

## 执行流程

### 阶段1：需求分析

**目标**：理解用户需求，明确插件功能和设计方向

**步骤**：
1. 使用 `AskUserQuestion` 询问以下信息（如果用户输入不明确）：
   - 插件类型（工具类/语言类/框架类）
   - 主要功能（代码生成/检查/自动化）
   - 目标用户（开发者/团队/企业）
   - 技术栈（Python/Go/JavaScript等）
   - 特殊需求（MCP集成/LSP集成/Hooks）

2. 在询问前，先通过以下方式收集现状信息：
   - 阅读现有代码（Read）
   - 阅读现有文档（Read）
   - 搜索最佳实践（WebSearch或deep-research）
   - 分析常用方案（serena:search_for_pattern）

3. 确保需求足够详细和明确：
   - What：要实现什么功能？
   - Why：为什么需要这个插件？
   - Who：目标用户是谁？
   - When：优先级如何？
   - Where：影响哪些模块？
   - How：技术方案偏好？

### 阶段2：生成开发计划

**目标**：将需求拆分为可执行的子任务，建立依赖关系

**步骤**：
1. 进入 Plan 模式（EnterPlanMode）
2. 生成完整的需求说明和开发说明
3. 尽可能细致地拆分需求：
   - 每个子任务职责单一
   - 明确输入/输出
   - 定义验收标准
   - 建立依赖关系（DAG）

4. 为每个子任务分配 agents 和 skills：
   - 开发插件结构 → Agents(plugin-dev-advisor) + Skills(plugin-skills)
   - 开发 Agents → Agents(plugin-dev-advisor) + Skills(plugin-agent-development)
   - 开发 Skills → Agents(plugin-dev-advisor) + Skills(plugin-skill-development)
   - 开发 Hooks → Agents(plugin-dev-advisor) + Skills(plugin-hook-development)
   - 开发 Scripts → Agents(plugin-dev-advisor) + Skills(plugin-script-development)
   - 集成 MCP → Agents(plugin-dev-advisor) + Skills(plugin-mcp-development)
   - 集成 LSP → Agents(plugin-dev-advisor) + Skills(plugin-lsp-development)
   - 生成文档 → Skills(documentation)

5. 退出 Plan 模式（ExitPlanMode），等待用户确认

### 阶段3：执行开发任务

**目标**：按计划执行所有开发任务

**步骤**：
1. 按依赖顺序执行任务
2. **并行限制**：最多2个任务同时执行
3. 优先使用 agents 而非直接执行：
   - Agents(plugin-dev-advisor) 负责所有插件开发相关任务
   - Agents(code-reviewer) 负责代码审查
   - Agents(architect) 负责架构评审（如需要）

4. 实时输出进度：
   ```
   [新插件开发·插件结构设计·进行中]
   [新插件开发·创建Agents·进行中]
   [新插件开发·创建Skills·已完成]
   ```

### 阶段4：完善测试

**目标**：确保测试通过率100%，覆盖率≥95%

**步骤**：
1. 为每个组件添加测试：
   - Agent 测试：AI理解测试（质量检查工具）
   - Skill 测试：功能测试、执行流程测试
   - Hook 测试：触发条件测试
   - Script 测试：单元测试、集成测试

2. 使用质量检查工具验证 AI 理解：
   ```bash
   claude --settings ~/.claude/settings.glm-4.5-flash.json \
     -p "$(cat agents/agent-name.md)" \
     --output-format stream-json | \
     jq -r 'select(.type == "result" and .subtype == "success") | .result'
   ```

3. 确保测试覆盖率：
   - 单元测试覆盖率≥90%
   - 集成测试覆盖主要流程
   - E2E 测试覆盖关键场景

### 阶段5：代码规范检查

**目标**：确保所有变更符合规范

**步骤**：
1. 检查文件长度：
   - *.md 文件：≤300行（推荐100-200行）
   - *.py 文件：≤800行（推荐200-500行）
   - *.go 文件：≤800行（推荐200-500行）

2. 检查代码风格：
   - 与原有代码风格一致
   - 命名规范（kebab-case for files, camelCase for variables）
   - 注释完整（关键逻辑必须注释）

3. 检查 YAML frontmatter：
   - 所有 Agents 和 Skills 必须有 frontmatter
   - 必填字段完整（description、model、skills等）

4. 检查文件组织：
   - 无多余空行和空格
   - 目录结构符合规范
   - 文件命名符合规范

### 阶段6：文档生成

**目标**：生成完整的插件文档

**步骤**：
1. 更新/创建 llms.txt：
   - 项目概览
   - 目录结构
   - 核心组件
   - 使用示例

2. 生成/更新 README.md：
   - 插件介绍
   - 安装方法
   - 使用示例
   - API 文档

3. 创建 CHANGELOG.md：
   - 版本历史
   - 变更记录

4. 如果是新增插件，注册到 `.claude-plugin/marketplace.json`

### 阶段7：最终验证

**目标**：全面验证插件质量

**步骤**：
1. AI 理解测试（所有 Agents 和 Skills）
2. 功能测试（基本流程）
3. 集成测试（与其他插件协作）
4. 文档完整性检查

## 最佳实践

### 需求收集

- 先理解现状，再提问
- 提供具体选项帮助用户选择
- 说明为什么需要这个信息
- 不限提问次数，确保需求明确

### 任务拆分

- 使用 MECE 原则（互相独立、完全穷尽）
- 每个子任务可独立验收
- 明确依赖关系（使用 DAG）
- 优先级排序（P0/P1/P2）

### 并行执行

- 最多2个任务并行
- 不能修改同一文件
- 不能操作同一模块
- 有依赖的任务串行执行

### 代码质量

- 结合静态分析和人工审查
- 使用 deep-research 确保内容正确、及时、更新
- 使用 chrome 操作浏览器搜索最新数据
- 所有变更必须有测试覆盖

### 文档完整性

- README 必须包含：安装、使用、示例
- llms.txt 必须及时更新
- CHANGELOG 记录版本变更
- 代码注释清晰完整

## 2026 规范要求

### ✅ 必须遵守

1. **Commands 已废弃**：使用 Skills（user-invocable: true）
2. **文件长度限制**：所有 .md 文件≤300行
3. **0%职责重叠**：Agent 职责严格划分
4. **Prompt Caching**：静态内容使用 `<!-- STATIC_CONTENT -->` 标记
5. **MCP Server Cards**：.mcp.json 包含 metadata 字段
6. **PROXY_URL**：无默认值（不使用 `${PROXY_URL:-default}`）

### ❌ 必须避免

1. ~~创建 commands/ 目录~~
2. ~~文件超过300行~~
3. ~~缺少 YAML frontmatter~~
4. ~~缺少测试~~
5. ~~缺少文档~~

## 输出格式

### 插件目录结构

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # ✅ Manifest配置
├── agents/                  # ✅ Agents目录
│   └── agent-name.md        # ≤300行
├── skills/                  # ✅ Skills目录
│   └── skill-name/
│       ├── SKILL.md         # ≤300行
│       └── examples.md      # ≤300行
├── hooks/                   # ⚙️ Hooks目录（可选）
├── scripts/                 # ⚙️ Scripts目录（可选）
├── .mcp.json               # ⚙️ MCP配置（可选）
├── README.md               # ✅ 项目文档
├── CHANGELOG.md            # ✅ 版本历史
└── llms.txt                # ✅ AI友好概览
```

### Manifest 示例（plugin.json）

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "插件描述",
  "author": {
    "name": "作者名称",
    "email": "email@example.com",
    "url": "https://github.com/username"
  },
  "homepage": "https://github.com/username/plugin-name",
  "repository": "https://github.com/username/plugin-name",
  "license": "AGPL-3.0-or-later",
  "keywords": ["keyword1", "keyword2"],
  "agents": [
    "./agents/agent-name.md"
  ],
  "skills": "./skills/",
  "hooks": {
    "SessionStart": [{
      "hooks": [{"type": "command", "command": "echo 'Plugin loaded'"}]
    }]
  }
}
```

## 使用示例

### 示例1：创建简单工具插件

```bash
用户输入："创建一个名为 version 的插件，用于版本号管理"

→ 阶段1：需求分析
  AI 提问："版本号格式？（SemVer/Calendar/Custom）"
  用户回答："SemVer（major.minor.patch）"

  AI 提问："主要功能？（bump version/get version/validate version）"
  用户回答："全部功能"

→ 阶段2：生成计划
  [Plan Mode]
  子任务1：创建插件结构 → plugin-dev-advisor
  子任务2：创建 version-manager agent → plugin-dev-advisor
  子任务3：创建 bump-version skill → plugin-dev-advisor
  子任务4：创建 get-version skill → plugin-dev-advisor
  子任务5：编写测试 → code-reviewer
  子任务6：生成文档 → documentation

→ 阶段3：执行开发（串行/并行）
  [新插件开发·创建插件结构·已完成]
  [新插件开发·创建agent·已完成]
  [新插件开发·创建skills·进行中]

→ 阶段4-7：测试、检查、文档、验证
  [新插件开发·完成·质量100%]
```

### 示例2：创建语言类插件

```bash
用户输入："创建 golang 插件，支持代码生成和测试"

→ 阶段1：需求分析
  AI 提问："需要 LSP 集成吗？（用于代码补全）"
  用户回答："是"

  AI 提问："需要哪些 agents？"
  用户回答："golang-coder（代码生成）、golang-tester（测试）"

→ 阶段2-7：...（同上）
```

## 相关 Skills

- **plugin-skills** - 插件开发规范（详细指南）
- **documentation** - 文档生成
- **code-review** - 代码审查
- **architecture-review** - 架构评审（大型插件）

## 工具集成

- **Plan Mode**：EnterPlanMode / ExitPlanMode
- **User Interaction**：AskUserQuestion
- **Agents**：Agents(plugin-dev-advisor)、Agents(code-reviewer)
- **Code Search**：serena:search_for_pattern
- **Web Search**：WebSearch、deep-research

---

**迁移完成**：Commands 已废弃，功能完整迁移到 Skill，符合2026最新规范。
