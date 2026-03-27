---
description: 执行完整的深度研究工作流程 - Task-Centric任务驱动，DGoT核心优化，单次需求收集
user-invocable: true
context: fork
model: sonnet
memory: project
skills:
  - dgot-engine
  - agentic-retriever
  - source-validator
  - knowledge-synthesizer
  - code-inspector
---

# 深度研究（Deep Research）

## 核心职责

Task-Centric 任务驱动型深度研究系统，自动编排Agent和Skill完成复杂研究任务。

## 2026架构特性

- **DGoT动态优化**：降低43-56%研究成本
- **Agentic RAG**：动态检索策略，精度99%
- **单次需求收集**：智能结构化提问，无重复交互
- **自动Agent匹配**：基于任务特征自动选择最优Agent

## 工作流程

### 阶段1：智能需求收集（单次）

通过 AskUserQuestion 收集结构化信息（5-8个维度）：

**必须收集**：
1. **研究目标**：具体要研究什么？解决什么问题？
2. **研究范围**：全面研究 vs 特定方向？包含哪些方面？
3. **目标受众**：技术专家 vs 管理层 vs 普通读者？
4. **输出格式**：技术报告 vs 演示文稿 vs 博客文章？

**可选收集**（根据任务类型）：
5. **时间范围**：历史回顾 vs 现状分析 vs 未来趋势？
6. **质量标准**：引用等级要求（A-E级）？深度要求？
7. **对比对象**：是否需要对比分析？对比哪些方案？
8. **约束条件**：时间限制？成本预算？技术栈限制？

### 阶段2：自动Agent匹配

基于任务特征自动选择Agent（无需用户选择）：

**匹配规则**：
```python
if "代码" in task or "质量" in task or "性能" in task:
    agent = "code-analyst"
elif "选型" in task or "对比" in task or "vs" in task:
    agent = "research-strategist"
elif "github.com" in task or "依赖" in task or "安全" in task:
    agent = "project-assessor"
elif "架构" in task or "设计" in task or "重构" in task:
    agent = "architecture-advisor"
else:
    # 默认：根据研究目标智能推断
    agent = auto_match_agent(task)
```

**多Agent协作**（复杂任务）：
- 代码质量+架构评审 → code-analyst + architecture-advisor
- 技术选型+项目评估 → research-strategist + project-assessor

### 阶段3：DGoT核心驱动（自动执行）

使用 `dgot-engine` 优化研究路径：

```python
# 初始化
paths = dgot.Generate(k=5)  # 生成5个初始路径
scored = dgot.Score(paths)   # 质量评分

# 动态裁剪
best = dgot.KeepBestN(scored, n=3)  # 保留前3个

# 早停检查
if dgot.EarlyStop(best):  # 质量≥8.5分，3个路径达标
    return dgot.Aggregate(best)

# 深化路径
refined = dgot.Refine(best)
final = dgot.Aggregate(refined)
```

**成本节省**：
- 早停机制：平均减少30%迭代
- 动态裁剪：平均减少20%无效路径
- 总体节省：43-56%成本

### 阶段4：智能检索（Agentic RAG）

使用 `agentic-retriever` 多源并行检索：

**检索策略**（自动选择）：
- **深度优先**：单一主题深入挖掘（技术原理、学术研究）
- **广度优先**：多角度快速覆盖（市场分析、行业趋势）
- **平衡搜索**：深度+广度结合（技术选型、综合评估）

**信息源**（8+渠道）：
- 学术：PubMed、IEEE、ACM、arXiv、Google Scholar
- 技术：GitHub、Stack Overflow、技术博客
- 商业：Gartner、IDC、McKinsey
- 新闻：技术媒体、行业报告

### 阶段5：质量验证（A-E评级）

使用 `source-validator` 过滤低质量信息：

**自动过滤**：
- A级（9.0-10）：优先使用
- B级（7.0-8.9）：重点参考
- C级（5.0-6.9）：辅助支持
- D级（3.0-4.9）：交叉验证
- E级（0-2.9）：自动丢弃

**质量保证**：
- 每个关键发现需要≥2个B级以上来源确认
- 所有统计数据需验证原始来源
- 专家观点需确认专家身份和领域

### 阶段6：知识合成（8种格式）

使用 `knowledge-synthesizer` 生成最终报告：

**格式选择**（基于受众和场景）：
1. **执行摘要** - 高层决策者（1-2页）
2. **技术报告** - 技术专家（5-15页）
3. **学术论文** - 研究人员（8-20页）
4. **演示文稿** - 团队分享（10-20页PPT）
5. **博客文章** - 技术社区（1500-3000字）
6. **对比表格** - 快速决策（1-2页）
7. **清单报告** - 质量审计（2-5页）
8. **llms.txt** - API文档（可变）

## 使用示例

### 示例1：代码质量分析

```bash
输入：分析 ./src 目录的代码质量和技术债

自动流程：
1. 需求收集：研究范围（./src）、输出格式（技术报告）
2. Agent匹配：code-analyst（关键词"代码质量"）
3. DGoT驱动：Generate(5) → Score → KeepBestN(3)
4. 代码检查：code-inspector 静态分析
5. 质量验证：source-validator 验证最佳实践来源
6. 知识合成：技术报告（质量+债务+优先级）
```

### 示例2：技术选型

```bash
输入：对比 React vs Vue vs Svelte 在企业项目中的优劣

自动流程：
1. 需求收集：对比对象（3个框架）、场景（企业项目）
2. Agent匹配：research-strategist（关键词"对比"）
3. DGoT驱动：广度优先搜索，多角度对比
4. 智能检索：官方文档+技术博客+社区讨论
5. 质量验证：A级（官方文档）+ B级（专家博客）
6. 知识合成：对比表格（多维度评分矩阵）
```

### 示例3：GitHub项目评估

```bash
输入：评估 facebook/react 的项目质量和安全风险

自动流程：
1. 需求收集：项目（facebook/react）、关注点（质量+安全）
2. Agent匹配：project-assessor（检测到github.com）
3. DGoT驱动：平衡搜索，质量+安全双维度
4. 项目分析：code-inspector GitHub集成（gh 命令）
5. 安全审计：CVE数据库、依赖树分析
6. 知识合成：技术报告（健康度+安全分+风险评估）
```

### 示例4：架构评审

```bash
输入：评审 ./docs/architecture.md 的架构设计

自动流程：
1. 需求收集：设计文档路径、评审重点（可扩展性）
2. Agent匹配：architecture-advisor（关键词"架构"）
3. DGoT驱动：深度优先，架构原则验证
4. 模式识别：识别架构模式（微服务/事件驱动）
5. 原则验证：SOLID、DRY、KISS验证
6. 知识合成：技术报告（评审+建议+重构路径）
```

## 进度追踪

实时显示研究进度：

```
[深度研究·技术选型·进行中]
├─ 需求收集：✅ 完成（3个维度）
├─ Agent匹配：✅ research-strategist
├─ DGoT路径生成：🔄 进行中（5/5路径已生成）
├─ 质量评分：⏳ 等待
├─ 信息检索：⏳ 等待
└─ 知识合成：⏳ 等待

预计完成时间：2-3分钟
预计成本：$0.15（基于DGoT优化）
```

## 循环终止条件

自动判断何时完成：

1. **信息完整**：所有关键维度已收集
2. **质量达标**：≥80%的发现有B级以上来源支持
3. **目标达成**：研究问题已充分回答
4. **用户确认**：最终报告获得用户认可

## 最佳实践

- 提供具体的研究目标（避免"优化代码"这类模糊描述）
- 明确输出格式和受众（技术报告 vs 演示文稿）
- 说明约束条件（时间/成本/技术栈限制）
- 对比分析时明确对比对象和维度
- 复杂任务可分阶段执行（先概念理解，再深入分析）

## 与旧架构对比

| 维度 | 旧架构 | 新架构（2026） |
|------|--------|---------------|
| 需求收集 | 重复2次 | 单次智能收集 |
| Agent选择 | 用户手动 | 自动匹配 |
| 成本优化 | 无 | DGoT动态裁剪（-50%） |
| 检索精度 | 传统RAG | Agentic RAG（99%） |
| 交互次数 | 10+次 | 5-8次 |
| 平均耗时 | 8-10分钟 | 4-6分钟 |
