---
name: question-refiner-skills
description: 研究问题优化技能 - 详细配置规范和实现指南
---

## 问题优化器详细规范

### 核心功能

问题优化器负责将模糊或宽泛的研究问题转化为结构化的、可执行的研究计划。

### 激活条件

当用户提出以下内容时自动激活：
- 模糊的研究问题（"研究人工智能"）
- 缺乏明确方向的问题
- 过于宽泛的主题（"技术发展"）
- 需要进一步细化的研究需求

### 优化流程详解

#### 1. 初步分析算法

```python
def analyze_question(question_text):
    """
    分析研究问题的复杂度和类型
    """
    # 识别问题类型
    question_type = identify_question_type(question_text)

    # 提取核心概念
    core_concepts = extract_core_concepts(question_text)

    # 评估复杂度
    complexity = assess_complexity(question_text, core_concepts)

    return {
        "type": question_type,
        "concepts": core_concepts,
        "complexity": complexity,
        "scope": estimate_scope(complexity)
    }
```

#### 2. 关键维度提问矩阵

| 维度 | 问题类型 | 深度问题 | 关键考量 |
|------|---------|---------|---------|
| **研究范围** | 学术研究 | 具体研究子领域？理论还是实证？ | 确保研究聚焦且可执行 |
|  | 技术研究 | 具体技术栈？应用场景？ | 平衡技术深度和实用性 |
|  | 市场研究 | 目标市场？细分领域？ | 确保市场分析的针对性 |
| **输出要求** | 学术研究 | 论文类型？字数要求？格式规范？ | 符合学术标准 |
|  | 技术研究 | 技术方案？实现指南？性能指标？ | 输出实用性强 |
|  | 商业研究 | 报告类型？决策支持？投资分析？ | 满足商业需求 |
| **受众分析** | 专家导向 | 专业深度要求？术语使用？ | 保持专业性和可理解性 |
|  | 管理导向 | 决策支持重点？风险关注点？ | 侧重战略和执行 |
|  | 投资导向 | ROI分析？风险评估？市场前景？ | 侧重财务和机会 |
| **时间约束** | 学术研究 | 论文截止时间？研究周期？ | 合理安排研究进度 |
|  | 商业研究 | 报告需求时间？决策时间线？ | 满足商业时间要求 |
|  | 技术研究 | 开发时间线？技术选型周期？ | 考虑技术实现周期 |
| **质量标准** | 信息来源 | 权威性要求？文献类型？ | 确保信息可靠性 |
|  | 数据质量 | 样本要求？数据类型？时效性？ | 保证数据质量 |
|  | 分析深度 | 理论要求？实证要求？对比分析？ | 满足深度需求 |

#### 3. 结构化提示生成模板

```markdown
# {{research_topic}} 研究计划

## 研究背景
{{background_context}}

## 具体研究范围
{{scope_details}}

### 核心研究维度
- {{dimension_1}}
- {{dimension_2}}
- {{dimension_3}}

### 排除范围
- {{exclusions}}

## 研究目标
{{objectives}}

### 主要研究问题
1. {{question_1}}
2. {{question_2}}
3. {{question_3}}

### 次要研究问题
1. {{question_4}}
2. {{question_5}}

## 受众分析
{{audience_analysis}}

### 目标受众
{{target_audience}}

### 需求分析
{{requirements}}

### 知识水平
{{knowledge_level}}

## 输出要求
{{output_requirements}}

### 格式要求
{{format_requirements}}

### 详细程度
{{detail_level}}

### 特殊要求
{{special_requirements}}

## 质量标准
{{quality_standards}}

### 来源要求
{{source_requirements}}

### 验证要求
{{verification_requirements}}

### 时效性要求
{{timeliness_requirements}}

## 研究方法
{{research_methods}}

### 数据收集策略
{{data_collection}}

### 分析框架
{{analysis_framework}}

### 质量控制
{{quality_control}}

## 预期成果
{{expected_outcomes}}

### 主要交付物
{{deliverables}}

### 价值点
{{value_points}}
```

### 问题类型识别系统

#### 1. 学术研究问题
**特征识别**：
- 使用学术术语
- 涉及理论或方法论
- 引用文献需求
- 研究空白识别

**优化策略**：
```markdown
# 学术研究优化模板

## 理论框架
- [ ] 理论基础
- [ ] 概念界定
- [ ] 研究假设

## 方法论
- [ ] 研究设计
- [ ] 数据收集
- [ ] 分析方法

## 文献要求
- [ ] 文献类型
- [ ] 时间跨度
- [ ] 地理范围
- [ ] 语言限制
```

#### 2. 技术研究问题
**特征识别**：
- 技术术语使用
- 实现相关提问
- 性能关注点
- 工具和平台需求

**优化策略**：
```markdown
# 技术研究优化模板

## 技术维度
- [ ] 技术栈
- [ ] 实现方案
- [ ] 性能指标
- [ ] 安全要求

## 应用场景
- [ ] 使用环境
- [ ] 用户需求
- [ ] 约束条件

## 评估标准
- [ ] 功能性
- [ ] 性能
- [ ] 可维护性
- [ ] 可扩展性
```

#### 3. 市场研究问题
**特征识别**：
- 商业术语使用
- 市场和竞争关注
- 用户和客户提及
- 投资和财务相关

**优化策略**：
```markdown
# 市场研究优化模板

## 市场维度
- [ ] 目标市场
- [ ] 市场规模
- [ ] 增长趋势
- [ ] 细分市场

## 竞争分析
- [ ] 主要竞争者
- [ ] 市场份额
- [ ] 竞争策略
- [ ] 优势劣势

## 用户研究
- [ ] 目标用户
- [ ] 用户需求
- [ ] 使用行为
- [ ] 满意度
```

### 智能提问算法

```python
class QuestionOptimizer:
    def __init__(self):
        self.question_types = {
            "academic": self.academic_questions,
            "technical": self.technical_questions,
            "market": self.market_questions,
            "policy": self.policy_questions
        }

    def generate_questions(self, question_type, context):
        """
        根据问题类型生成相关问题
        """
        questions = []

        # 基础维度问题
        base_questions = self.get_base_questions()
        questions.extend(base_questions)

        # 特定类型问题
        type_questions = self.question_types[question_type](context)
        questions.extend(type_questions)

        # 动态问题生成
        dynamic_questions = self.generate_dynamic_questions(context)
        questions.extend(dynamic_questions)

        return questions

    def academic_questions(self, context):
        """学术研究特定问题"""
        return [
            "研究的具体理论框架是什么？",
            "需要实证研究还是理论研究？",
            "目标期刊或会议的定位是什么？",
            "样本规模和研究周期要求？"
        ]

    def technical_questions(self, context):
        """技术研究特定问题"""
        return [
            "目标技术平台和版本要求？",
            "性能指标的具体要求？",
            "集成和部署环境？",
            "安全和合规要求？"
        ]

    def market_questions(self, context):
        """市场研究特定问题"""
        return [
            "目标市场的地理范围？",
            "时间跨度要求？",
            "关键成功指标？",
            "预算和资源限制？"
        ]
```

### 优化质量评估

#### 优化成功标准
```markdown
- 问题清晰度：评分 >= 8/10
- 范围明确性：评分 >= 8/10
- 目标可达成性：评分 >= 7/10
- 受众针对性：评分 >= 8/10
- 输出可行性：评分 >= 8/10
```

#### 优化失败处理
```markdown
- 重新提问：关键维度信息不足
- 问题分解：过于复杂的问题分解
- 概念澄清：术语和概念不明确
- 范围调整：研究范围过大或过小
```

### 实施建议

#### 系统要求
- 自然语言处理能力
- 上下文理解能力
- 动态问题生成
- 多轮对话支持

#### 性能指标
- 响应时间：< 2秒
- 问题生成准确率：> 90%
- 优化成功率：> 85%
- 用户满意度：> 4/5

#### 扩展功能
- 多语言支持
- 领域知识库
- 历史问题库
- 用户偏好学习

### 相关技能引用
- Skills(research-executor) - 执行优化后的研究任务
- Skills(got-controller) - 控制研究路径优化
- Skills(synthesizer) - 整合研究结果