# Planner 上下文学习指南

## 概述

基于 [Agentic Context Engineering](https://arxiv.org/html/2602.20478v1) 和 [Claude Code 记忆系统](https://code.claude.com/docs/zh-CN/memory)，planner 采用三层上下文学习策略，系统性地积累项目知识。

## 上下文版本化（Context Versioning）

在每次规划前自动保存上下文快照，支持失败后回滚到已知良好状态。

### 规划前自动保存快照

在进入信息收集阶段前，自动保存当前上下文快照：

```python
print(f"[MindFlow·{user_task}·信息收集/{iteration}·进行中]")

# 保存规划前上下文快照（调用 context-versioning skill）
version_id = save_context_snapshot(
    user_task=user_task,
    iteration=iteration,
    phase="pre-planning",
    context_state=context,
    status="pending",
    metadata={
        "trigger": context.get("replan_trigger"),
        "note": "规划前自动保存"
    }
)

print(f"[MindFlow] 当前上下文快照: {version_id}")
```

### 执行成功后标记快照

在任务执行成功后，更新快照状态为 success：

```python
print(f"[MindFlow·{user_task}·任务执行/{iteration}·completed]")

# 标记快照为成功状态
import hashlib
from pathlib import Path
from datetime import datetime

task_hash = hashlib.md5(user_task.encode('utf-8')).hexdigest()[:12]
snapshot_path = Path(f".claude/context-versions/{task_hash}/v{iteration}.json")

if snapshot_path.exists():
    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)

    snapshot["status"] = "success"
    snapshot["metadata"]["completed_at"] = datetime.now().isoformat()

    with open(snapshot_path, 'w') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"[MindFlow] ✓ 快照 v{iteration} 标记为成功")
```

### 验证失败时回滚支持

在失败调整阶段，支持回滚到上次成功的上下文快照：

```python
if context.get("replan_trigger") == "verification_failed":
    print(f"[MindFlow] 检测到验证失败，评估是否需要回滚上下文...")

    # 查询成功快照历史（调用 context-versioning skill）
    snapshots = list_context_versions(user_task, status_filter="success")

    if snapshots and len(snapshots) > 0:
        print(f"[MindFlow] 找到 {len(snapshots)} 个成功快照，最近: {snapshots[0]['version_id']}")

        user_decision = AskUserQuestion(
            question=f"验证失败，是否回滚到上次成功的上下文快照 {snapshots[0]['version_id']}？",
            options=["回滚上下文", "保持当前上下文", "查看快照对比"]
        )

        if user_decision == "查看快照对比":
            # 对比当前失败快照与最近成功快照
            current_version = f"v{iteration}"
            target_version = snapshots[0]['version_id']
            compare_context_snapshots(user_task, target_version, current_version)

            # 再次询问
            user_decision = AskUserQuestion(
                question="查看对比后，是否回滚上下文？",
                options=["回滚上下文", "保持当前上下文"]
            )

        if user_decision == "回滚上下文":
            # 执行回滚
            restored_snapshot = rollback_context(user_task, target_version=snapshots[0]['version_id'])

            if restored_snapshot:
                # 恢复上下文状态
                context = restored_snapshot["context_state"]
                iteration = restored_snapshot["iteration"]

                print(f"[MindFlow] ✓ 上下文已回滚，从迭代 {iteration} 重新开始")
                goto("计划设计")
    else:
        print(f"[MindFlow] ⚠️ 未找到成功的上下文快照，无法回滚")
```

**详细 API 说明**：参见 `skills/context-versioning/SKILL.md`

---

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

**通过 Memory Bridge 智能检索**：

Memory Bridge 作为记忆系统的适配层，提供三层记忆检索：

#### 1. 情节记忆（Episodic Memory）

检索相似任务的执行历史，提供规划参考：

```python
# 在 Planner 信息收集阶段调用
task_memories = load_task_memories(
    user_task=user_task,
    task_type=determine_task_type(user_task)
)

if task_memories["episodic_memory"]:
    print(f"[MindFlow·Memory] 找到 {len(task_memories['episodic_memory'])} 个相似任务情节")
    for episode in task_memories["episodic_memory"][:3]:
        print(f"  • {episode['task_desc']}")
        print(f"    结果: {episode['result']}, 相似度: {episode['similarity_score']:.2f}")
        print(f"    规划: {episode['plan']['report']}")
        print(f"    用时: {episode['metrics']['duration_minutes']}分钟, 迭代: {episode['metrics']['iterations']}次")
```

**提供的价值**：
- 相似任务的规划模式和分解策略
- 成功/失败经验和使用的 Agent/Skills 组合
- 执行指标（用时、迭代次数、停滞次数）
- 失败情节的恢复措施

#### 2. 语义记忆（Semantic Memory）

加载项目知识和架构约定：

```python
# 语义记忆在 load_task_memories() 中自动加载
if task_memories["semantic_memory"]:
    print(f"[MindFlow·Memory] 已加载 {len(task_memories['semantic_memory'])} 条项目知识")

    # 按领域分类展示
    by_domain = {}
    for memory in task_memories["semantic_memory"]:
        domain = memory.get("domain", "other")
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(memory)

    for domain, memories in by_domain.items():
        print(f"  【{domain}】")
        for m in memories[:2]:  # 每个领域最多显示2条
            print(f"    - {m['title']}: {m['content'][:50]}...")
```

**包含的知识**：
- **架构决策记录**（`project://knowledge/architecture/*`）：设计模式、分层架构
- **代码风格约定**（`project://knowledge/conventions/*`）：命名规范、文件组织
- **技术栈信息**（`project://knowledge/tech-stack/*`）：版本、依赖、构建工具
- **测试策略**（`project://knowledge/testing/*`）：测试框架、覆盖率要求

#### 3. 记忆集成到规划提示

将检索到的记忆作为上下文传递给 Planner：

```python
planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

任务目标：{user_task}
迭代编号：{iteration}

【情节记忆】相似任务参考（共 {len(task_memories["episodic_memory"])} 个）：
{format_episodic_memories(task_memories["episodic_memory"])}

【语义记忆】项目知识（共 {len(task_memories["semantic_memory"])} 条）：
{format_semantic_memories(task_memories["semantic_memory"])}

要求：
1. 参考相似任务的规划模式和分解策略
2. 遵循项目知识中的架构约定和代码风格
3. 复用成功情节中有效的 Agent/Skills 组合
4. 避免失败情节中的已知错误模式
5. 考虑相似任务的执行指标（用时、迭代次数）
6. 分解为原子子任务（MECE）
7. 建立依赖关系（DAG）
8. 定义可量化验收标准
9. 返回简短报告（≤200字）

如果功能已存在，返回空 tasks 数组。
"""
)
```

**使用记忆系统的优势**：
- **智能检索**：基于任务相似度和失败模式匹配，推荐最相关的记忆
- **自动加载**：核心记忆（priority ≤ 2）在会话开始时自动加载
- **跨会话积累**：记忆持久化存储，避免重复学习
- **版本隔离**：Memory Bridge 封装 Memory 插件 API，保持 Loop 稳定性
- **按需读取**：详细内容按需检索，节省上下文空间

**详细 API 说明**：参见 `skills/memory-bridge/SKILL.md`

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
