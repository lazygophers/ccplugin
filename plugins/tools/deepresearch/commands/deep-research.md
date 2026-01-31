---
name: deep-research
description: 执行完整的深度研究工作流程 - 根据研究内容选择合适的Agent，通过多轮交互完成深度研究
auto-activate: true
argument-hint: [研究内容]
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
| 代码审查和质量分析 | 文本/路径     | Agents(code-review-agent)          | 关键词："代码审查"、"代码质量"、"代码规范"                                        | AskUserQuestion |
| 性能分析和优化     | 文本/路径     | Agents(performance-analysis-agent) | 关键词："性能分析"、"性能优化"、"性能瓶颈"<br>或：路径 + 性能关键词               | AskUserQuestion |
| 技术债识别         | 文本/路径     | Agents(technical-debt-agent)       | 关键词："技术债"、"重构"、"代码异味"                                              | AskUserQuestion |
| GitHub项目评估     | URL/文本      | Agents(project-evaluation-agent)   | 关键词："GitHub项目"、"项目评估"、"开源项目"<br>或：包含 "github.com"             | AskUserQuestion |
| 技术选型对比       | 文本          | Agents(tech-selection-agent)       | 关键词："技术选型"、"方案对比"、"vs"                                              | AskUserQuestion |
| 依赖安全审计       | 文件路径      | Agents(dependency-audit-agent)     | 关键词："依赖审计"、"安全漏洞"、"依赖安全"<br>或：package.json/pyproject.toml文件 | AskUserQuestion |
| 技术概念解释       | 文本          | Agents(concept-explanation-agent)  | 关键词："什么是"、"如何"、"概念解释"                                              | AskUserQuestion |
| 架构设计评审       | 文档路径/文本 | Agents(architecture-review-agent)  | 关键词："架构评审"、"架构设计"、"架构评估"<br>或：架构文档路径                    | AskUserQuestion |

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
| code-review-agent          | local-code-analysis, synthesizer-skills                   | citation-validator-skills           |
| performance-analysis-agent | local-code-analysis, synthesizer-skills                   | explorer-skills                     |
| technical-debt-agent       | local-code-analysis, synthesizer-skills                   | explorer-skills                     |
| project-evaluation-agent   | github-analysis-skills, synthesizer-skills                       | citation-validator-skills           |
| tech-selection-agent       | content-retriever-skills, synthesizer-skills                     | question-refiner-skills, explorer-skills   |
| dependency-audit-agent     | content-retriever-skills, citation-validator-skills, synthesizer-skills | explorer-skills                     |
| concept-explanation-agent  | content-retriever-skills, synthesizer-skills                     | question-refiner-skills, explorer-skills   |
| architecture-review-agent  | local-code-analysis, synthesizer-skills                   | citation-validator-skills, explorer-skills |

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

## 执行保证

| 保证项        | 要求                                      |
| ------------- | ----------------------------------------- |
| Agent选择确认 | 必须使用AskUserQuestion确认Agent选择      |
| 信息收集      | 必须通过AskUserQuestion收集必要信息       |
| 缺口补充      | 发现信息缺口时必须通过AskUserQuestion补充 |
| 结果确认      | 最终报告前必须获得用户确认                |
