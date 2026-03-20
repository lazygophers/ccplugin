# 全局 Skills 架构设计（2026）

> 基于参考插件架构分析的 .claude/skills/ 重新设计方案

## 一、设计目标

### 目标用户

**主要用户**：Claude Code 用户（开发者、技术专家、团队领导）
**次要用户**：插件开发者（已有 plugin-skills/）

### 设计原则

1. **任务驱动**：Task-Centric，用户描述任务，系统自动匹配
2. **分层设计**：用户入口（user-invocable）+ 内部能力
3. **全流程覆盖**：开发→测试→部署→维护
4. **2026规范**：符合最新技术标准
5. **精简高效**：每个文件≤300行

### 核心目标

提供 **8-12个实用 Skills**，覆盖日常开发的核心场景：
- 代码质量（code-review、refactoring、testing）
- 架构设计（architecture-review、design-patterns）
- 开发工具（git-workflow、ci-cd）
- 文档生成（documentation）
- 插件开发（保留 plugin-skills/）

---

## 二、Skills 架构方案

### 整体架构

```
.claude/skills/
├── code-review/           # 代码审查 [NEW]
│   ├── SKILL.md
│   ├── best-practices.md
│   └── examples.md
├── refactoring/           # 重构指导 [NEW]
│   ├── SKILL.md
│   └── patterns.md
├── architecture-review/   # 架构评审 [NEW]
│   ├── SKILL.md
│   └── principles.md
├── testing/               # 测试策略 [NEW]
│   ├── SKILL.md
│   └── frameworks.md
├── documentation/         # 文档生成 [NEW]
│   ├── SKILL.md
│   └── templates/
├── git-workflow/          # Git 工作流 [NEW]
│   ├── SKILL.md
│   └── workflows.md
├── performance-optimization/  # 性能优化 [NEW]
│   ├── SKILL.md
│   └── techniques.md
├── security-audit/        # 安全审计 [NEW]
│   ├── SKILL.md
│   └── checklists.md
├── new-plugin/            # 创建新插件 [MIGRATED from commands]
│   ├── SKILL.md
│   └── templates/
└── plugin-skills/         # 插件开发 [EXISTING]
    ├── SKILL.md
    └── ...（保留现有结构）
```

### Skills 分类

#### 第一类：用户入口 Skills（user-invocable: true）

| Skill | 职责 | 使用场景 |
|-------|------|---------|
| **code-review** | 代码审查 | 代码质量检查、最佳实践验证、测试覆盖率 |
| **refactoring** | 重构指导 | 代码重构、设计模式应用、技术债处理 |
| **architecture-review** | 架构评审 | 架构设计评审、SOLID原则验证、演进路径规划 |
| **git-workflow** | Git 工作流 | 分支策略、提交规范、PR模板、版本管理 |
| **new-plugin** | 创建新插件 | 插件开发、结构设计、组件创建 |

#### 第二类：核心能力 Skills（内部调用）

| Skill | 职责 | 被调用者 |
|-------|------|---------|
| **testing** | 测试策略 | code-review、refactoring |
| **documentation** | 文档生成 | architecture-review、new-plugin |
| **performance-optimization** | 性能优化 | code-review、architecture-review |
| **security-audit** | 安全审计 | code-review、architecture-review |

#### 第三类：保留 Skills（现有）

| Skill | 职责 | 状态 |
|-------|------|------|
| **plugin-skills** | 插件开发 | 保留并优化 |

---

## 三、Skills 详细设计

### 1. code-review（代码审查）

**职责**：代码质量检查、最佳实践验证、测试覆盖率分析

**YAML frontmatter**：
```yaml
---
name: code-review
description: 代码审查 - 质量检查、最佳实践验证、测试覆盖率分析，生成改进建议
user-invocable: true
context: fork
model: sonnet
skills:
  - testing
  - performance-optimization
  - security-audit
---
```

**核心能力**：
1. **静态分析**：圈复杂度、代码重复、认知复杂度
2. **代码规范**：命名规范、注释质量、代码组织
3. **最佳实践**：SOLID原则、DRY、KISS
4. **测试覆盖**：行覆盖率、分支覆盖率、目标≥80%
5. **安全扫描**：注入漏洞、敏感信息泄露

**输出格式**：
- **技术报告**：详细分析 + 代码示例 + 改进建议
- **清单报告**：问题列表 + 优先级排序
- **演示文稿**：团队分享用可视化图表

**使用示例**：
```bash
用户："审查 ./src 目录的代码质量"
→ 触发 code-review skill
→ 调用 testing（测试覆盖率分析）
→ 调用 performance-optimization（性能检查）
→ 调用 security-audit（安全扫描）
→ 生成综合审查报告
```

**文件结构**：
- `SKILL.md`（≤300行）：主文件，执行流程
- `best-practices.md`（≤300行）：最佳实践详细说明
- `examples.md`（≤300行）：10个审查示例

---

### 2. refactoring（重构指导）

**职责**：代码重构、设计模式应用、技术债处理

**YAML frontmatter**：
```yaml
---
name: refactoring
description: 重构指导 - 代码重构、设计模式应用、技术债识别和优先级排序
user-invocable: true
context: fork
model: sonnet
skills:
  - testing
  - documentation
---
```

**核心能力**：
1. **技术债识别**：设计债、测试债、文档债、架构债
2. **优先级排序**：严重度 × 影响范围 × 紧急度
3. **设计模式应用**：单例、工厂、策略、观察者等
4. **重构步骤**：红绿重构法、小步快跑
5. **风险控制**：测试覆盖、回归测试、AB测试

**输出格式**：
- **重构计划**：阶段划分 + 任务分解 + 风险评估
- **代码示例**：重构前后对比
- **测试策略**：回归测试用例

**使用示例**：
```bash
用户："重构 ./src/services 模块，应用依赖注入模式"
→ 触发 refactoring skill
→ 分析当前代码结构
→ 识别技术债（紧耦合、难以测试）
→ 生成重构计划（5个阶段）
→ 提供代码示例和测试策略
```

**文件结构**：
- `SKILL.md`（≤300行）：主文件，重构流程
- `patterns.md`（≤300行）：23种设计模式详解

---

### 3. architecture-review（架构评审）

**职责**：架构设计评审、SOLID原则验证、演进路径规划

**YAML frontmatter**：
```yaml
---
name: architecture-review
description: 架构评审 - 设计评审、SOLID原则验证、可扩展性评估、演进路径规划
user-invocable: true
context: fork
model: opus
skills:
  - performance-optimization
  - security-audit
  - documentation
---
```

**核心能力**：
1. **架构模式识别**：微服务、事件驱动、分层、六边形等
2. **设计原则验证**：SOLID、DRY、KISS、YAGNI
3. **可扩展性评估**：水平扩展、功能扩展、性能扩展
4. **可维护性评估**：模块化、低耦合、文档质量
5. **演进路径规划**：从单体到微服务的演进方案

**输出格式**：
- **技术报告**：架构评审报告（评分 + 建议 + 路径）
- **架构决策记录（ADR）**：关键决策文档
- **演进路线图**：分阶段演进计划

**使用示例**：
```bash
用户："评审 ./docs/architecture.md 的微服务设计"
→ 触发 architecture-review skill
→ 识别架构模式（微服务 + 事件驱动）
→ 验证 SOLID 原则
→ 评估可扩展性（8.5分）、可维护性（7.0分）
→ 生成改进建议和演进路径
```

**文件结构**：
- `SKILL.md`（≤300行）：主文件，评审流程
- `principles.md`（≤300行）：SOLID + DRY + KISS + YAGNI 详解

---

### 4. testing（测试策略）

**职责**：测试策略设计、测试用例生成、测试框架选择

**YAML frontmatter**：
```yaml
---
name: testing
description: 测试策略 - 单元测试、集成测试、E2E测试，测试用例生成
user-invocable: false
context: same
model: sonnet
skills: []
---
```

**核心能力**：
1. **测试策略**：单元测试、集成测试、E2E测试
2. **测试框架选择**：Jest、Pytest、JUnit等
3. **测试用例生成**：AAA模式（Arrange-Act-Assert）
4. **覆盖率分析**：行覆盖率、分支覆盖率、函数覆盖率
5. **Mock 策略**：依赖Mock、API Mock

**输出格式**：
- **测试策略文档**：测试金字塔、覆盖率目标
- **测试用例**：详细测试代码
- **测试报告**：覆盖率报告 + 建议

**文件结构**：
- `SKILL.md`（≤300行）：主文件，测试策略
- `frameworks.md`（≤300行）：主流测试框架对比

---

### 5. git-workflow（Git 工作流）

**职责**：分支策略、提交规范、PR模板、版本管理

**YAML frontmatter**：
```yaml
---
name: git-workflow
description: Git 工作流 - 分支策略（Git Flow/GitHub Flow/Trunk-based）、提交规范、PR模板
user-invocable: true
context: fork
model: sonnet
skills:
  - documentation
---
```

**核心能力**：
1. **分支策略**：Git Flow、GitHub Flow、Trunk-based Development
2. **提交规范**：Conventional Commits（feat/fix/docs/style/refactor/test/chore）
3. **PR模板**：描述、checklist、关联Issue
4. **版本管理**：语义化版本（SemVer）
5. **代码审查规范**：审查checklist、批准流程

**输出格式**：
- **工作流文档**：分支策略 + 提交规范 + PR流程
- **模板文件**：PR模板、Issue模板、提交模板
- **Git Hooks**：pre-commit、commit-msg检查

**使用示例**：
```bash
用户："设计适合20人团队的 Git 工作流"
→ 触发 git-workflow skill
→ 推荐 GitHub Flow（简单高效）
→ 生成提交规范（Conventional Commits）
→ 提供 PR 模板和审查checklist
→ 配置 Git Hooks 自动检查
```

**文件结构**：
- `SKILL.md`（≤300行）：主文件，工作流设计
- `workflows.md`（≤300行）：3种主流工作流详细对比

---

### 6. new-plugin（创建新插件）

**职责**：插件开发、结构设计、组件创建（迁移自 commands/new.md）

**YAML frontmatter**：
```yaml
---
name: new-plugin
description: 创建新插件 - 插件结构设计、manifest配置、组件创建、MCP集成
user-invocable: true
context: fork
model: sonnet
skills:
  - plugin-skills
  - documentation
---
```

**核心能力**：
1. **插件结构设计**：目录结构、文件组织
2. **Manifest 配置**：plugin.json 配置
3. **组件创建**：agents、skills、hooks、commands（已废弃）
4. **MCP 集成**：MCP 服务器配置
5. **文档生成**：README、CHANGELOG

**输出格式**：
- **插件模板**：完整的插件目录结构
- **配置文件**：plugin.json + .mcp.json
- **文档模板**：README + CHANGELOG

**使用示例**：
```bash
用户："创建一个名为 golang 的插件，用于 Go 语言开发"
→ 触发 new-plugin skill
→ 创建插件目录结构
→ 生成 plugin.json
→ 创建示例 agent（golang-coder）
→ 生成 README 和 CHANGELOG
```

**文件结构**：
- `SKILL.md`（≤300行）：主文件，创建流程
- `templates/`：插件模板文件

---

### 7. performance-optimization（性能优化）

**职责**：性能瓶颈定位、优化建议、基准测试

**YAML frontmatter**：
```yaml
---
name: performance-optimization
description: 性能优化 - 瓶颈定位（N+1查询、内存泄漏）、优化建议、基准测试
user-invocable: false
context: same
model: sonnet
skills: []
---
```

**核心能力**：
1. **瓶颈定位**：慢查询、低效算法、内存泄漏
2. **优化建议**：缓存、索引、异步处理
3. **基准测试**：性能指标、压力测试
4. **监控方案**：APM、日志分析

**输出格式**：
- **性能报告**：瓶颈分析 + 优化建议
- **基准测试结果**：优化前后对比
- **监控配置**：Prometheus + Grafana

**文件结构**：
- `SKILL.md`（≤300行）：主文件，优化流程
- `techniques.md`（≤300行）：20种优化技术详解

---

### 8. security-audit（安全审计）

**职责**：安全扫描、漏洞检测、合规检查

**YAML frontmatter**：
```yaml
---
name: security-audit
description: 安全审计 - 漏洞检测（SQL注入、XSS）、依赖安全、许可证合规
user-invocable: false
context: same
model: sonnet
skills: []
---
```

**核心能力**：
1. **漏洞检测**：OWASP Top 10（SQL注入、XSS、CSRF等）
2. **依赖安全**：CVE漏洞扫描、依赖版本检查
3. **许可证合规**：开源许可证检查
4. **敏感信息检测**：密钥、密码泄露检测

**输出格式**：
- **安全报告**：漏洞列表 + 风险评级 + 修复建议
- **合规报告**：许可证合规性
- **修复方案**：具体修复代码示例

**文件结构**：
- `SKILL.md`（≤300行）：主文件，审计流程
- `checklists.md`（≤300行）：OWASP Top 10 检查清单

---

### 9. documentation（文档生成）

**职责**：文档生成、API文档、llms.txt

**YAML frontmatter**：
```yaml
---
name: documentation
description: 文档生成 - README、API文档、架构图、llms.txt
user-invocable: false
context: same
model: sonnet
skills: []
---
```

**核心能力**：
1. **README 生成**：项目概览、安装、使用示例
2. **API 文档**：接口文档、参数说明、示例
3. **架构图生成**：Mermaid 图、架构决策记录（ADR）
4. **llms.txt 生成**：AI友好的项目概览

**输出格式**：
- **README.md**：完整的项目文档
- **API.md**：API参考文档
- **ARCHITECTURE.md**：架构文档 + Mermaid 图
- **llms.txt**：AI系统可读文档

**文件结构**：
- `SKILL.md`（≤300行）：主文件，文档生成流程
- `templates/`：README/API/ARCHITECTURE 模板

---

### 10. plugin-skills（插件开发）

**职责**：保留现有功能，优化结构

**现有结构**：
```
plugin-skills/
├── SKILL.md
├── plugin-development/
├── plugin-agent-development/
├── plugin-skill-development/
├── plugin-command-development/
├── plugin-hook-development/
├── plugin-mcp-development/
├── plugin-lsp-development/
├── plugin-script-development/
└── quality-check/
```

**优化方向**：
1. **主文件精简**：SKILL.md ≤300行
2. **移除命令开发**：plugin-command-development（命令已废弃）
3. **更新最佳实践**：符合2026规范
4. **添加2026技术**：DGoT、Agentic RAG 等示例

---

## 四、Skills 调用关系

### 用户入口 Skills

```
用户直接调用：
- code-review
- refactoring
- architecture-review
- git-workflow
- new-plugin
```

### 内部调用链

```
code-review
├── testing
├── performance-optimization
└── security-audit

refactoring
├── testing
└── documentation

architecture-review
├── performance-optimization
├── security-audit
└── documentation

git-workflow
└── documentation

new-plugin
├── plugin-skills
└── documentation
```

---

## 五、文件行数控制策略

### 主文件（SKILL.md）≤300行

**结构**：
1. YAML frontmatter（10-20行）
2. 概览（50-100行）
3. 核心能力（100-150行）
4. 执行流程（50-100行）
5. 最佳实践（30-50行）

**精简技术**：
- 移除重复内容
- 使用链接引用详细文档
- 表格化信息
- 移除版本历史

### 辅助文件≤300行

**类型**：
- best-practices.md
- examples.md
- patterns.md
- workflows.md
- templates/

**策略**：
- 每个文件聚焦单一主题
- 使用表格和列表
- 提供代码示例
- 避免长篇大论

---

## 六、实施优先级

### P0（必须）

1. **code-review**：最常用的功能
2. **new-plugin**：迁移自 commands/new.md
3. **plugin-skills**：优化现有功能

### P1（重要）

4. **refactoring**：高频使用场景
5. **architecture-review**：技术专家需求
6. **git-workflow**：团队协作必备

### P2（可选）

7. **testing**：内部能力，支撑其他 skills
8. **documentation**：内部能力，支撑其他 skills
9. **performance-optimization**：内部能力
10. **security-audit**：内部能力

---

## 七、验收标准

### 功能验收

- ✅ 10个 skills 全部创建
- ✅ 5个用户入口 skills（user-invocable: true）
- ✅ 5个内部能力 skills
- ✅ commands/new.md 已迁移到 skills/new-plugin/
- ✅ plugin-skills/ 已优化

### 质量验收

- ✅ 所有 .md 文件 ≤300行
- ✅ YAML frontmatter 格式正确
- ✅ 依赖关系清晰
- ✅ 文档完整（README + 主文件 + 辅助文件）

### 用户体验验收

- ✅ 用户描述任务，系统自动匹配
- ✅ 高质量输入静默处理
- ✅ 低质量输入智能提问
- ✅ 输出格式多样化

---

## 八、下一步

1. 实现 P0 Skills（code-review、new-plugin、plugin-skills 优化）
2. 实现 P1 Skills（refactoring、architecture-review、git-workflow）
3. 实现 P2 Skills（内部能力 skills）
4. 更新文档（.claude/skills/README.md）
5. 删除 commands/ 目录
6. 集成测试和质量验证

---

**设计版本**：v1.0
**创建时间**：2026-03-20
**预计实施时间**：P0 (2-3小时) + P1 (2-3小时) + P2 (1-2小时)
**风险等级**：低（仅新增和优化，不破坏现有功能）
