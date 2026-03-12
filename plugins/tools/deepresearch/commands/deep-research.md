---
description: 执行完整的深度研究工作流程 - 根据研究内容选择合适的Agent，通过多轮交互完成深度研究
auto-activate: true
argument-hint: [研究内容]
model: sonnet
memory: project
---

# 深度研究

通过多轮交互和智能Agent协作，完成深度研究任务。

## 研究流程

### 阶段1：Agent选择与方案提供

1. 分析研究内容，识别研究类型
2. 匹配最合适的Agent
3. 通过`AskUserQuestion`提供Agent选择方案
4. 获取用户确认

### 阶段2：信息采集与需求明确

1. 识别需要收集的信息维度
2. 通过`AskUserQuestion`多轮提问：
    - 研究范围和具体方向
    - 时间范围（历史/现状/未来）
    - 地理范围（本地/区域/全球）
    - 目标受众和详细程度
    - 质量标准和时间约束
3. 生成结构化研究计划
4. 确认用户是否满意

### 阶段3：循环执行与结果完善

1. **信息采集**：根据研究计划采集信息
2. **理解整理**：整理分类信息，识别关键发现
3. **质量检查**：检查信息完整性，识别缺口
4. **交互完善**：对有问题的部分通过`AskUserQuestion`提问
5. **循环迭代**：重复步骤1-4，直到获得完整结果

## Agent选择策略

| 研究内容特征       | 输入类型      | 选择Agent                          | 检测逻辑                                                                          | 确认方式        |
| ------------------ | ------------- | ---------------------------------- | --------------------------------------------------------------------------------- | --------------- |
| 代码审查和质量分析 | 文本/路径     | Agents(deepresearch:code-review)          | 关键词："代码审查"、"代码质量"、"代码规范"                                        | AskUserQuestion |
| 性能分析和优化     | 文本/路径     | Agents(deepresearch:performance-analysis) | 关键词："性能分析"、"性能优化"、"性能瓶颈"<br>或：路径 + 性能关键词               | AskUserQuestion |
| 技术债识别         | 文本/路径     | Agents(deepresearch:technical-debt)       | 关键词："技术债"、"重构"、"代码异味"                                              | AskUserQuestion |
| GitHub项目评估     | URL/文本      | Agents(deepresearch:project-evaluation)   | 关键词："GitHub项目"、"项目评估"、"开源项目"<br>或：包含 "github.com"             | AskUserQuestion |
| 技术选型对比       | 文本          | Agents(deepresearch:tech-selection)       | 关键词："技术选型"、"方案对比"、"vs"                                              | AskUserQuestion |
| 依赖安全审计       | 文件路径      | Agents(deepresearch:dependency-audit)     | 关键词："依赖审计"、"安全漏洞"、"依赖安全"<br>或：package.json/pyproject.toml文件 | AskUserQuestion |
| 技术概念解释       | 文本          | Agents(deepresearch:concept-explanation)  | 关键词："什么是"、"如何"、"概念解释"                                              | AskUserQuestion |
| 架构设计评审       | 文档路径/文本 | Agents(deepresearch:architecture-review)  | 关键词："架构评审"、"架构设计"、"架构评估"<br>或：架构文档路径                    | AskUserQuestion |

## Skills激活策略

### 核心流程Skills（所有Agent通用）

| Skill                      | 用途                       | 时机              | 必需性 |
| -------------------------- | -------------------------- | ----------------- | ------ |
| Skills(question-refiner)   | 明确研究问题，细化研究需求 | 阶段2开始时       | 可选   |
| Skills(content-retriever)  | 采集相关信息和数据         | 阶段3信息采集阶段 | 按需   |
| Skills(explorer)           | 探索专业领域和技术前沿     | 需要深入探索时    | 按需   |
| Skills(citation-validator) | 验证信息来源质量           | 质量检查阶段      | 按需   |
| Skills(synthesizer)        | 整合研究结果，生成报告     | 最后阶段          | 必需   |

### 辅助决策Skills（按需激活）

| Skill                     | 用途                   | 触发条件               |
| ------------------------- | ---------------------- | ---------------------- |
| Skills(got-controller)    | 复杂研究项目的路径优化 | 需要优化研究策略时     |
| Skills(research-executor) | 并行执行多维度研究任务 | 需要多个角度并行研究时 |

### Agent特定Skills需求

| Agent                      | 必需Skills                                         | 可选Skills                   |
| -------------------------- | -------------------------------------------------- | ---------------------------- |
| code-review          | local-code-analysis, synthesizer-skills                   | citation-validator-skills           |
| performance-analysis | local-code-analysis, synthesizer-skills                   | explorer-skills                     |
| technical-debt       | local-code-analysis, synthesizer-skills                   | explorer-skills                     |
| project-evaluation   | github-analysis-skills, synthesizer-skills                       | citation-validator-skills           |
| tech-selection       | content-retriever-skills, synthesizer-skills                     | question-refiner-skills, explorer-skills   |
| dependency-audit     | content-retriever-skills, citation-validator-skills, synthesizer-skills | explorer-skills                     |
| concept-explanation  | content-retriever-skills, synthesizer-skills                     | question-refiner-skills, explorer-skills   |
| architecture-review  | local-code-analysis, synthesizer-skills                   | citation-validator-skills, explorer-skills |

## 多轮交互策略

| 交互时机     | 交互目的         | 交互方式                          |
| ------------ | ---------------- | --------------------------------- |
| Agent选择后  | 确认Agent选择    | AskUserQuestion提供2-3个Agent选项 |
| 需求明确阶段 | 收集研究维度信息 | AskUserQuestion逐个询问5-8个维度  |
| 信息采集后   | 确认信息充分性   | AskUserQuestion确认是否需要补充   |
| 发现缺口时   | 补充缺失信息     | AskUserQuestion针对缺口提问       |
| 报告生成前   | 确认报告方向     | AskUserQuestion确认重点和格式     |

### 循环终止条件

| 条件               | 说明                   |
| ------------------ | ---------------------- |
| 已收集所有必要信息 | 核心维度信息已收集完整 |
| 用户确认信息充足   | 用户确认无需更多信息   |
| 生成完整的研究报告 | 报告内容完整且符合要求 |
| 用户主动结束研究   | 用户明确表示结束研究   |

## 执行检查清单

### 阶段 1：Agent 选择与方案提供检查

- [ ] 分析研究内容，识别研究类型（代码审查/性能分析/技术选型等）
- [ ] 根据研究内容特征匹配最合适的 Agent（参考 Agent 选择策略表）
- [ ] 准备 2-3 个 Agent 选择方案
- [ ] 通过 `AskUserQuestion` 提供 Agent 选择方案
- [ ] 获取用户确认选择的 Agent

### 阶段 2：信息采集与需求明确检查

- [ ] 识别需要收集的信息维度（范围、时间、地理、受众、质量）
- [ ] 通过 `AskUserQuestion` 逐个询问信息维度
- [ ] 收集研究范围和具体方向
- [ ] 收集时间范围（历史/现状/未来）
- [ ] 收集地理范围（本地/区域/全球）
- [ ] 收集目标受众和详细程度
- [ ] 收集质量标准和时间约束
- [ ] 生成结构化研究计划
- [ ] 通过 `AskUserQuestion` 确认用户是否满意

### 阶段 3：循环执行与结果完善检查

**信息采集检查**：
- [ ] 根据研究计划采集信息
- [ ] 使用合适的 Skills（content-retriever, explorer 等）
- [ ] 记录信息来源和可信度

**理解整理检查**：
- [ ] 整理分类采集的信息
- [ ] 识别关键发现和模式
- [ ] 标注信息之间的关联

**质量检查**：
- [ ] 检查信息完整性（对照研究计划）
- [ ] 识别信息缺口
- [ ] 验证信息来源质量（使用 citation-validator）

**交互完善检查**：
- [ ] 对有问题的部分通过 `AskUserQuestion` 提问
- [ ] 补充缺失的信息
- [ ] 澄清模糊的内容

**循环迭代检查**：
- [ ] 重复步骤 1-4 直到获得完整结果
- [ ] 检查是否满足循环终止条件

### Skills 激活检查

**核心流程 Skills（所有 Agent 通用）**：
- [ ] `Skills(question-refiner)` - 需要明确研究问题时激活
- [ ] `Skills(content-retriever)` - 信息采集阶段激活
- [ ] `Skills(explorer)` - 需要深入探索时激活
- [ ] `Skills(citation-validator)` - 质量检查阶段激活
- [ ] `Skills(synthesizer)` - **必需**，最后阶段激活

**Agent 特定 Skills 检查**（参考 Agent 特定 Skills 需求表）：
- [ ] 确认当前 Agent 的必需 Skills 已激活
- [ ] 确认当前 Agent 的可选 Skills 按需激活

### 循环终止条件检查

- [ ] 已收集所有必要信息（核心维度信息完整）
- [ ] 用户确认信息充足
- [ ] 生成完整的研究报告
- [ ] 用户主动结束研究

### 最终报告生成检查

- [ ] 使用 `Skills(synthesizer)` 整合研究结果
- [ ] 报告格式符合用户要求
- [ ] 报告内容完整且有深度
- [ ] 引用来源已标注
- [ ] 通过 `AskUserQuestion` 获得用户最终确认

## 工具调用说明

### 必需工具

| 工具 | 用途 | 调用时机 |
|------|------|---------|
| `AskUserQuestion` | 确认 Agent 选择、收集信息、补充缺口、确认结果 | 阶段 1、阶段 2、阶段 3 交互完善、最终确认 |

### Agent 调用

根据研究内容选择（参考 Agent 选择策略表）：
| Agent | 触发条件 | 检测逻辑 |
|------|---------|---------|
| `deepresearch:code-review` | 代码审查和质量分析 | 关键词："代码审查"、"代码质量" |
| `deepresearch:performance-analysis` | 性能分析和优化 | 关键词："性能分析"、"性能优化" |
| `deepresearch:technical-debt` | 技术债识别 | 关键词："技术债"、"重构" |
| `deepresearch:project-evaluation` | GitHub 项目评估 | 包含 "github.com" 或关键词 |
| `deepresearch:tech-selection` | 技术选型对比 | 关键词："技术选型"、"vs" |
| `deepresearch:dependency-audit` | 依赖安全审计 | package.json/pyproject.toml |
| `deepresearch:concept-explanation` | 技术概念解释 | 关键词："什么是"、"如何" |
| `deepresearch:architecture-review` | 架构设计评审 | 关键词："架构评审"、"架构设计" |

### Skills 引用

**核心流程 Skills**：
| Skill | 用途 | 必需性 |
|------|------|--------|
| `Skills(question-refiner)` | 明确研究问题 | 可选 |
| `Skills(content-retriever)` | 采集信息 | 按需 |
| `Skills(explorer)` | 探索前沿 | 按需 |
| `Skills(citation-validator)` | 验证来源 | 按需 |
| `Skills(synthesizer)` | 整合报告 | **必需** |

**辅助决策 Skills**：
| Skill | 用途 | 触发条件 |
|------|------|---------|
| `Skills(got-controller)` | 优化研究路径 | 需要优化研究策略时 |
| `Skills(research-executor)` | 并行执行研究 | 需要多角度并行研究时 |

## 执行保证

| 保证项        | 要求                                      |
| ------------- | ----------------------------------------- |
| Agent选择确认 | 必须使用AskUserQuestion确认Agent选择      |
| 信息收集      | 必须通过AskUserQuestion收集必要信息       |
| 缺口补充      | 发现信息缺口时必须通过AskUserQuestion补充 |
| 结果确认      | 最终报告前必须获得用户确认                |

## 注意事项

### 研究质量保证

- Agent 选择必须基于研究内容特征
- 信息收集必须覆盖所有关键维度
- 信息来源必须验证可信度
- 最终报告必须有深度和洞察

### 常见错误

- ❌ 未确认用户直接选择 Agent
- ❌ 信息收集不完整就生成报告
- ❌ 未验证信息来源可信度
- ❌ 报告内容浅薄缺少深度

### 最佳实践

- ✅ 多轮交互确保需求明确
- ✅ 循环迭代确保信息完整
- ✅ 验证来源确保信息可信
- ✅ 整合深度确保报告质量
