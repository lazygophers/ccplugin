# 全局 Agents 架构设计（2026）

> 基于参考插件架构分析的 .claude/agents/ 重新设计方案

## 一、设计目标

### 目标用户

**主要用户**：Claude Code 用户（开发者、架构师、技术领导）
**使用场景**：日常开发、代码审查、架构设计、插件开发

### 设计原则

1. **职责整合**：8个细分 agents → 3-5个实用 agents
2. **0%重叠**：严格职责边界，避免功能重复
3. **智能触发**：基于任务特征自动选择
4. **模型统一**：每个 agent 明确模型选择（opus/sonnet）
5. **文件精简**：每个文件≤300行

### 核心目标

提供 **3-5个实用 Agents**，覆盖开发全流程：
- **code-reviewer**：代码审查专家
- **architect**：架构顾问
- **plugin-dev-advisor**：插件开发顾问（合并现有8个）

---

## 二、现有 Agents 分析

### 当前架构（8个）

| Agent | 职责 | 行数 | 问题 |
|-------|------|------|------|
| agent.md | Agent 开发 | 1718 | 职责过细 |
| command.md | Command 开发 | 1725 | 命令已废弃 |
| hook.md | Hook 开发 | 2558 | 职责过细 |
| lsp.md | LSP 集成 | 2130 | 职责过细 |
| mcp.md | MCP 集成 | 2304 | 职责过细 |
| plugin.md | 插件开发 | 1580 | 职责重叠 |
| script.md | 脚本开发 | 3066 | 职责过细 |
| skill.md | Skill 开发 | 1988 | 职责过细 |

**总计**：8个 agents，17069行代码

**主要问题**：
1. **职责过细**：8个 agents 都是插件开发相关，应合并
2. **文件过长**：多个文件超过2000行
3. **命令废弃**：command.md 对应的功能已废弃
4. **职责重叠**：plugin.md 和其他7个有重叠

---

## 三、新架构设计

### 整体架构

```
.claude/agents/
├── code-reviewer.md        # 代码审查专家 [NEW]
├── architect.md            # 架构顾问 [NEW]
└── plugin-dev-advisor.md   # 插件开发顾问 [NEW, 合并现有8个]
```

### Agents 对比

| 维度 | 旧架构 | 新架构 | 改进 |
|------|--------|--------|------|
| Agents数量 | 8个 | 3个 | -63% |
| 职责重叠 | 高（插件相关） | 0% | 严格边界 |
| 总代码行数 | 17069行 | ~900行 | -95% |
| 文件行数限制 | 无 | ≤300行 | 易读易维护 |
| 命令支持 | 有（已废弃） | 无 | 符合2026规范 |

---

## 四、Agents 详细设计

### 1. code-reviewer（代码审查专家）

**职责**：代码质量检查、最佳实践验证、测试覆盖率分析

**合并来源**：无（全新）

**YAML frontmatter**：
```yaml
---
description: |
  代码审查专家 - 代码质量检查、最佳实践验证、测试覆盖率分析
  场景：代码审查、重构规划、技术债识别、性能优化
  示例：审查 ./src 代码 | 分析技术债 | 评估测试覆盖率 | 定位性能瓶颈
model: sonnet
color: blue
memory: project
skills:
  - code-review
  - refactoring
  - testing
  - performance-optimization
  - security-audit
---
```

**核心职责**：
1. **代码质量分析**：静态分析、代码规范、最佳实践
2. **技术债识别**：债务分类、优先级排序、重构建议
3. **测试策略**：单元测试、集成测试、E2E测试
4. **性能分析**：瓶颈定位、优化建议、基准测试
5. **安全审计**：漏洞检测、依赖安全、许可证合规

**触发场景**：
- 代码审查：「审查代码」「代码质量」「code review」
- 重构：「重构」「refactoring」「技术债」
- 测试：「测试覆盖率」「单元测试」「test coverage」
- 性能：「性能瓶颈」「performance」「优化」
- 安全：「安全审计」「漏洞检测」「security」

**工作流程**：
```
1. 需求理解
   - 审查范围（整个项目 vs 特定模块）
   - 关注点（质量 vs 性能 vs 安全）
   - 输出格式（报告 vs 清单 vs PPT）

2. 代码分析
   - 静态分析（圈复杂度、代码重复）
   - 测试覆盖率（行覆盖、分支覆盖）
   - 性能检查（N+1查询、内存泄漏）
   - 安全扫描（OWASP Top 10）

3. 问题分类
   - 质量问题（命名、注释、SOLID）
   - 技术债（设计债、测试债、文档债）
   - 性能问题（慢查询、低效算法）
   - 安全问题（注入漏洞、敏感信息）

4. 优先级评分
   优先级 = 严重度(0-10) × 影响范围(0-10) × 紧急度(0-10)

5. 生成报告
   - 技术报告：详细分析 + 代码示例
   - 清单报告：问题列表 + 优先级
   - 演示文稿：团队分享用图表
```

**分析维度**：
- **可读性**（30%）：命名、注释、代码组织
- **可维护性**（30%）：模块化、耦合度、复杂度
- **可测试性**（20%）：依赖注入、接口抽象
- **安全性**（20%）：注入漏洞、敏感信息泄露

**输出格式**：
- **技术团队**：技术报告（详细分析+代码示例）
- **管理层**：执行摘要（问题总结+优先级）
- **团队分享**：演示文稿（可视化图表）

**最佳实践**：
- 结合静态分析和人工审查
- 提供具体的代码示例和改进建议
- 优先级排序基于业务影响
- 重构建议可操作且风险可控

**文件长度**：≤300行

---

### 2. architect（架构顾问）

**职责**：架构设计评审、SOLID原则验证、演进路径规划

**合并来源**：无（全新）

**YAML frontmatter**：
```yaml
---
description: |
  架构顾问 - 架构设计评审、SOLID原则验证、可扩展性评估、演进路径规划
  场景：架构评审、系统设计、重构方案、技术选型
  示例：评审微服务架构 | 验证SOLID原则 | 规划演进路径 | 设计系统架构
model: opus
color: purple
memory: project
skills:
  - architecture-review
  - performance-optimization
  - security-audit
  - documentation
---
```

**核心职责**：
1. **架构模式识别**：微服务、事件驱动、分层、六边形等
2. **设计原则验证**：SOLID、DRY、KISS、YAGNI
3. **可扩展性评估**：水平扩展、功能扩展、性能扩展
4. **可维护性评估**：模块化、低耦合、文档质量
5. **演进路径规划**：从单体到微服务的演进方案

**触发场景**：
- 架构评审：「架构评审」「architecture review」「设计评审」
- 系统设计：「系统设计」「system design」「架构设计」
- 重构方案：「重构方案」「架构演进」「migration」
- 技术选型：「技术选型」「框架对比」「technology selection」

**工作流程**：
```
1. 架构分析
   - 读取架构文档（architecture.md）
   - 识别架构模式（微服务/事件驱动/分层等）
   - 分析组件关系（依赖图、通信模式）

2. 设计原则验证
   - SOLID原则（单一职责、开闭、里氏替换、接口隔离、依赖倒置）
   - DRY（Don't Repeat Yourself）
   - KISS（Keep It Simple, Stupid）
   - YAGNI（You Aren't Gonna Need It）

3. 评分评估
   - 可扩展性评分（0-10）：水平扩展 + 功能扩展
   - 可维护性评分（0-10）：模块化 + 低耦合
   - 可靠性评分（0-10）：容错 + 监控 + 降级

4. 问题识别
   - 架构问题（紧耦合、单点故障、性能瓶颈）
   - 设计问题（违反原则、过度设计、欠设计）
   - 技术债（技术栈过时、依赖老旧）

5. 演进路径规划
   - 短期改进（3-6个月）
   - 中期演进（6-12个月）
   - 长期目标（1-2年）

6. 生成报告
   - 技术报告：评审结果 + 评分 + 建议
   - 架构决策记录（ADR）：关键决策文档
   - 演进路线图：分阶段演进计划
```

**评分维度**：
- **可扩展性**（40%）：水平扩展 + 功能扩展 + 技术扩展 + 性能扩展
- **可维护性**（35%）：模块化 + 低耦合 + 文档 + 测试
- **可靠性**（25%）：容错 + 监控 + 降级 + 恢复

**架构模式库**：
- 微服务（Microservices）
- 事件驱动（Event-Driven）
- 分层架构（Layered Architecture）
- 六边形架构（Hexagonal Architecture）
- CQRS + Event Sourcing
- Serverless

**输出格式**：
- **技术报告**：架构评审报告（评分 + 建议 + 路径）
- **架构决策记录（ADR）**：关键决策文档
- **演进路线图**：分阶段演进计划

**最佳实践**：
- 架构决策要有充分的理由（ADR）
- 优先考虑可扩展性和可维护性
- 避免过度设计和欠设计
- 关注非功能性需求（性能、安全、可靠性）

**文件长度**：≤300行

---

### 3. plugin-dev-advisor（插件开发顾问）

**职责**：插件结构设计、manifest配置、组件创建、MCP/LSP集成

**合并来源**：现有8个 agents（agent.md、command.md、hook.md、lsp.md、mcp.md、plugin.md、script.md、skill.md）

**YAML frontmatter**：
```yaml
---
description: |
  插件开发顾问 - 插件结构设计、manifest配置、组件创建、MCP/LSP集成
  场景：创建插件、开发Agent、开发Skill、集成MCP/LSP、创建Hook
  示例：创建golang插件 | 开发coder agent | 创建review skill | 集成GitHub MCP | 配置pre-commit hook
model: sonnet
color: green
memory: project
skills:
  - new-plugin
  - plugin-skills
  - documentation
---
```

**核心职责**：
1. **插件结构设计**：目录结构、文件组织、命名规范
2. **Manifest 配置**：plugin.json 配置、路径映射、自动激活
3. **Agent 开发**：Agent 定义、YAML frontmatter、触发场景
4. **Skill 开发**：Skill 定义、user-invocable、依赖管理
5. **Hook 开发**：PreToolUse、PostToolUse、Stop 等事件钩子
6. **MCP 集成**：MCP 服务器配置、工具调用
7. **LSP 集成**：LSP 服务器配置、代码补全
8. **Script 开发**：Python/Shell 脚本、环境变量

**触发场景**：
- 插件开发：「创建插件」「plugin development」「new plugin」
- Agent开发：「开发agent」「create agent」「agent定义」
- Skill开发：「开发skill」「create skill」「skill定义」
- MCP集成：「集成MCP」「MCP服务器」「MCP integration」
- LSP集成：「集成LSP」「LSP服务器」「LSP integration」
- Hook开发：「创建hook」「pre-commit hook」「hook development」
- Script开发：「编写脚本」「Python脚本」「Shell脚本」

**工作流程**：
```
1. 需求分析
   - 插件类型（工具类 vs 语言类 vs 框架类）
   - 主要功能（代码生成 vs 检查 vs 自动化）
   - 目标用户（开发者 vs 团队 vs 企业）

2. 结构设计
   - 目录结构（agents/、skills/、hooks/、scripts/）
   - 文件组织（单Agent vs 多Agent、单Skill vs 多Skill）
   - 命名规范（kebab-case、语义化）

3. Manifest 配置
   - 插件元数据（name、version、description、author）
   - 路径映射（agents、skills、hooks、scripts）
   - 自动激活（文件模式、关键词）

4. 组件开发
   - Agent开发（定义、职责、触发场景）
   - Skill开发（YAML、执行流程、最佳实践）
   - Hook开发（事件、触发条件、执行逻辑）
   - Script开发（功能、参数、错误处理）

5. 集成配置
   - MCP集成（服务器配置、工具调用、环境变量）
   - LSP集成（服务器配置、代码补全、诊断）

6. 文档生成
   - README.md（概览、安装、使用、API）
   - CHANGELOG.md（版本历史）
   - llms.txt（AI友好概览）

7. 测试验证
   - AI理解测试（质量检查工具）
   - 功能测试（基本流程）
   - 集成测试（与其他插件协作）
```

**开发组件类型**：

#### Agent 开发
- **定义规范**：YAML frontmatter（description、model、color、memory、skills）
- **职责定义**：核心职责、触发场景、工作流程
- **最佳实践**：职责单一、边界清晰、示例丰富
- **文件长度**：≤300行

#### Skill 开发
- **定义规范**：YAML frontmatter（name、description、user-invocable、context、model、skills）
- **执行流程**：阶段划分、工具调用、错误处理
- **最佳实践**：Prompt Caching、静态内容标记
- **文件长度**：主文件≤300行，辅助文件≤300行

#### Hook 开发（已废弃Commands）
- **事件类型**：PreToolUse、PostToolUse、Stop、SubagentStop、SessionStart、SessionEnd
- **触发条件**：文件模式、工具名称、条件表达式
- **执行方式**：prompt-based（推荐）vs command-based
- **最佳实践**：幂等性、错误处理、性能优化

#### MCP 集成
- **服务器类型**：SSE、stdio、HTTP、WebSocket
- **配置文件**：.mcp.json（mcpServers、env、metadata）
- **工具调用**：mcp__server-name__tool-name(参数)
- **环境变量**：GITHUB_TOKEN、PROXY_URL等

#### LSP 集成
- **服务器配置**：命令、参数、工作目录
- **功能支持**：代码补全、诊断、格式化、重命名
- **最佳实践**：性能优化、错误处理

#### Script 开发
- **语言选择**：Python（复杂逻辑）vs Shell（简单任务）
- **参数处理**：环境变量、命令行参数
- **错误处理**：异常捕获、退出码
- **最佳实践**：幂等性、日志记录

**设计原则**：
- **模块化**：每个组件职责单一
- **可复用**：组件可独立使用
- **可测试**：AI理解测试、功能测试
- **可维护**：文件≤300行、文档完整

**输出格式**：
- **插件模板**：完整目录结构 + 示例代码
- **配置文件**：plugin.json + .mcp.json
- **文档模板**：README + CHANGELOG + llms.txt
- **测试脚本**：AI理解测试命令

**最佳实践**（2026规范）：
- **Commands 已废弃**：迁移到 Skills（user-invocable: true）
- **Task-Centric 设计**：任务驱动，自动Agent匹配
- **0%职责重叠**：Agent职责严格划分
- **文件≤300行**：易读易维护
- **Prompt Caching**：静态内容标记，90%成本节省

**合并内容清单**：

| 原Agent | 合并内容 | 位置 |
|---------|---------|------|
| agent.md | Agent开发规范 | § Agent 开发 |
| command.md | ❌ 已废弃，迁移到Skill | 说明废弃原因 |
| hook.md | Hook开发规范 | § Hook 开发 |
| lsp.md | LSP集成规范 | § LSP 集成 |
| mcp.md | MCP集成规范 | § MCP 集成 |
| plugin.md | 插件结构设计 | § 插件结构设计 |
| script.md | Script开发规范 | § Script 开发 |
| skill.md | Skill开发规范 | § Skill 开发 |

**文件长度**：≤300行（通过分节和表格化压缩）

---

## 五、Agents 对比表

| Agent | 旧架构职责 | 新架构职责 | 模型 | 文件长度 |
|-------|-----------|-----------|------|---------|
| **code-reviewer** | ❌ 无 | 代码审查+重构+测试+性能+安全 | sonnet | ≤300行 |
| **architect** | ❌ 无 | 架构评审+设计验证+演进规划 | opus | ≤300行 |
| **plugin-dev-advisor** | 8个细分agents | 插件开发统一入口 | sonnet | ≤300行 |
| ~~agent.md~~ | Agent开发 | → plugin-dev-advisor | - | 废弃 |
| ~~command.md~~ | Command开发 | → ❌ 命令已废弃 | - | 废弃 |
| ~~hook.md~~ | Hook开发 | → plugin-dev-advisor | - | 废弃 |
| ~~lsp.md~~ | LSP集成 | → plugin-dev-advisor | - | 废弃 |
| ~~mcp.md~~ | MCP集成 | → plugin-dev-advisor | - | 废弃 |
| ~~plugin.md~~ | 插件开发 | → plugin-dev-advisor | - | 废弃 |
| ~~script.md~~ | Script开发 | → plugin-dev-advisor | - | 废弃 |
| ~~skill.md~~ | Skill开发 | → plugin-dev-advisor | - | 废弃 |

---

## 六、触发逻辑

### 自动Agent匹配

基于任务关键词自动选择Agent：

```python
if "代码" in task or "审查" in task or "code" in task or "review" in task:
    agent = "code-reviewer"
elif "架构" in task or "设计" in task or "architecture" in task:
    agent = "architect"
elif "插件" in task or "plugin" in task or "agent" in task or "skill" in task:
    agent = "plugin-dev-advisor"
```

### 触发示例

| 用户输入 | 匹配Agent | 理由 |
|---------|----------|------|
| "审查 ./src 代码质量" | code-reviewer | 包含"审查"+"代码" |
| "评审微服务架构设计" | architect | 包含"评审"+"架构" |
| "创建golang插件" | plugin-dev-advisor | 包含"插件" |
| "定位API性能瓶颈" | code-reviewer | 包含"性能" |
| "规划从单体到微服务的演进路径" | architect | 包含"架构"+"演进" |
| "开发code-review skill" | plugin-dev-advisor | 包含"skill" |

---

## 七、模型选择

| Agent | 模型 | 理由 |
|-------|------|------|
| **code-reviewer** | sonnet | 代码分析、快速响应、成本优化 |
| **architect** | opus | 架构设计、复杂推理、深度分析 |
| **plugin-dev-advisor** | sonnet | 插件开发、指导性任务、快速反馈 |

---

## 八、文件长度控制策略

### 压缩技术

1. **表格化**：将长列表转换为表格
2. **分节**：使用 § 符号分节
3. **链接引用**：详细内容链接到 Skills 文档
4. **移除重复**：合并相似内容
5. **代码示例精简**：仅保留关键示例

### 示例（plugin-dev-advisor.md）

**原始长度**（8个文件合并）：17069行
**目标长度**：≤300行
**压缩率**：-98.2%

**压缩策略**：
- Agent开发：50行（详细内容 → plugin-skills/plugin-agent-development/）
- Skill开发：50行（详细内容 → plugin-skills/plugin-skill-development/）
- Hook开发：40行（详细内容 → plugin-skills/plugin-hook-development/）
- MCP集成：40行（详细内容 → plugin-skills/plugin-mcp-development/）
- LSP集成：30行（详细内容 → plugin-skills/plugin-lsp-development/）
- Script开发：30行（详细内容 → plugin-skills/plugin-script-development/）
- 其他（YAML、流程、最佳实践）：60行

**总计**：300行

---

## 九、实施优先级

### P0（必须）

1. **plugin-dev-advisor**：合并现有8个agents，最高优先级
2. **code-reviewer**：最常用功能

### P1（重要）

3. **architect**：技术专家需求

---

## 十、验收标准

### 功能验收

- ✅ 3个 agents 全部创建
- ✅ 8个旧 agents 已废弃
- ✅ 职责边界清晰，0%重叠
- ✅ 自动触发逻辑正确

### 质量验收

- ✅ 所有 .md 文件 ≤300行
- ✅ YAML frontmatter 格式正确
- ✅ AI理解准确率 100%（质量检查工具）
- ✅ 模型选择合理（opus/sonnet）

### 用户体验验收

- ✅ 用户描述任务，系统自动匹配Agent
- ✅ 触发场景丰富（10+示例）
- ✅ 输出格式多样化

---

## 十一、迁移计划

### 阶段1：创建新Agents

1. 创建 code-reviewer.md
2. 创建 architect.md
3. 创建 plugin-dev-advisor.md

### 阶段2：废弃旧Agents

1. 删除 agent.md、command.md、hook.md、lsp.md、mcp.md、plugin.md、script.md、skill.md
2. 或：移动到 .claude/agents/deprecated/ 备份

### 阶段3：验证

1. AI理解测试
2. 功能测试
3. 集成测试

---

## 十二、下一步

1. 实现 P0 Agents（plugin-dev-advisor、code-reviewer）
2. 实现 P1 Agents（architect）
3. 废弃旧 Agents
4. 更新文档（.claude/agents/README.md）
5. 集成测试和质量验证

---

**设计版本**：v1.0
**创建时间**：2026-03-20
**预计实施时间**：P0 (2-3小时) + P1 (1-2小时)
**风险等级**：低（新建+废弃，不修改现有功能）
