---
description: 规划项目任务 - 分析需求、制定多级任务清单、更新到项目task中
argument-hint: [feature-name] [options]
allowed-tools: Read, Edit, Write, Bash(uv*,uvx*)
model: sonnet
---

# plan

## 命令描述

规划项目功能的任务清单，通过系统化分析生成详细的多级任务，并自动更新到项目的 task 系统中。

## 工作流描述

1. **需求分析**：理解功能需求、业务目标和关键场景
2. **项目调研**：阅读当前项目的架构、实现模式和相似功能的设计
3. **任务设计**：制定多级任务清单，包括文档、数据库、API、各端开发及测试
4. **任务入库**：通过 uvx 方式将生成的任务批量更新到项目的 task 系统中

## 命令执行方式

### 使用方法

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add <title> [options]
```

### 执行时机

- 开发新功能之前进行系统规划
- 需要确保功能开发的完整性和一致性
- 为多人协作创建清晰的任务清单
- 需要按照项目的既有模式进行功能设计

### 执行参数

- `<title>`: 任务标题（必需）
- `--description` / `-d`: 任务描述
- `--type` / `-t`: 任务类型 (feature/bug/refactor/test/docs/config)
- `--status` / `-s`: 任务状态 (pending/in_progress/completed/blocked/cancelled)
- `--acceptance` / `-a`: 验收标准
- `--depends` / `-D`: 依赖任务ID（逗号分隔）
- `--parent` / `-p`: 父任务ID（创建子任务）

### 命令说明

- 命令会根据指定的参数创建任务
- 支持创建父任务和子任务的层级结构
- 通过 `--parent` 参数可以创建子任务，建立任务间的从属关系
- 可以指定任务的类型、状态、验收标准等详细信息

## 任务清单结构

规划生成的任务应包含以下部分：

### 必需部分

- **文档设计**（必须）
  - 类型：`docs`
  - 示例：API 接口文档设计、数据模型文档、架构决策记录

### 可选部分

- **数据库设计**（当功能涉及数据存储时）
  - 类型：`docs` 或可创建类似类型
  - 示例：数据库模型设计、迁移脚本、索引优化

- **API/Proto 设计**（当功能需要接口规范时）
  - 类型：`docs`
  - 示例：接口规范设计、Proto 定义

- **各端开发及测试**（根据平台）
  - 开发任务：类型 `feature`
  - 单元测试：类型 `test`
  - 集成测试：类型 `test`

- **集成测试**
  - 类型：`test`
  - 示例：端到端测试、跨端集成测试、性能测试

## 示例

### 基本用法 - 规划用户认证系统

#### 步骤 1: 创建主任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "用户认证系统" \
  --type feature \
  --priority high \
  --description "完整的用户认证系统实现"
```

返回任务 ID，假设为 `abc123`

#### 步骤 2: 创建文档设计子任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "认证系统 API 文档设计" \
  --parent abc123 \
  --type docs \
  --description "设计用户认证相关的 API 接口规范" \
  --acceptance "API 文档清晰完整，包含所有接口"
```

#### 步骤 3: 创建数据库设计子任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "用户表和令牌表设计" \
  --parent abc123 \
  --type docs \
  --description "设计用户表、令牌表、权限表的数据库模型" \
  --acceptance "数据模型设计完整，包含索引和约束"
```

#### 步骤 4: 创建后端开发子任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "后端认证功能开发" \
  --parent abc123 \
  --type feature \
  --description "实现用户注册、登录、令牌刷新等功能" \
  --depends "用户表和令牌表设计" \
  --acceptance "所有认证接口都能正确处理"
```

#### 步骤 5: 创建后端测试子任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "后端认证功能单元测试" \
  --parent abc123 \
  --type test \
  --description "编写认证功能的单元测试" \
  --depends "后端认证功能开发" \
  --acceptance "测试覆盖率 >80%"
```

#### 步骤 6: 创建前端开发子任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "Web 端认证功能开发" \
  --parent abc123 \
  --type feature \
  --description "实现 Web 端的登录、注册界面和认证逻辑" \
  --depends "认证系统 API 文档设计" \
  --acceptance "登录/注册流程完整可用"
```

#### 步骤 7: 创建前端测试子任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "Web 端认证功能测试" \
  --parent abc123 \
  --type test \
  --description "编写 Web 端认证功能的测试用例" \
  --depends "Web 端认证功能开发" \
  --acceptance "主要流程都有对应的测试"
```

#### 步骤 8: 创建集成测试子任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "认证系统端到端测试" \
  --parent abc123 \
  --type test \
  --description "测试整个认证流程的端到端场景" \
  --depends "后端认证功能单元测试,Web 端认证功能测试" \
  --acceptance "所有认证场景都能正确工作"
```

### 多平台应用规划示例

为支付功能创建任务：

```bash
# 主任务
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "支付功能" \
  --type feature \
  --description "完整的支付处理系统"

# 文档（main_id 为上面创建的任务 ID）
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "支付 API 文档" \
  --parent main_id \
  --type docs

# 数据库
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "支付订单表设计" \
  --parent main_id \
  --type docs

# Web 端
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "Web 端支付功能开发" \
  --parent main_id \
  --type feature

uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "Web 端支付测试" \
  --parent main_id \
  --type test

# Mobile 端
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "Mobile 端支付功能开发" \
  --parent main_id \
  --type feature

uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "Mobile 端支付测试" \
  --parent main_id \
  --type test

# 集成测试
uvx --from git+https://github.com/lazygophers/ccplugin task add \
  "支付流程集成测试" \
  --parent main_id \
  --type test
```

## 任务设计原则

- ✅ **文档优先**：每个功能都需要详细的文档
- ✅ **独立可测试**：每个任务都应该独立且可验证
- ✅ **清晰依赖**：使用 `--depends` 标注任务间的前置依赖关系
- ✅ **多端独立**：多端功能各自独立开发，共享文档和设计
- ✅ **完整测试**：包括单元测试、集成测试、端到端测试

## 工作流步骤

### 1. 需求分析

- 与产品方充分沟通，理解功能核心需求
- 明确功能边界和关键场景
- 识别技术挑战点
- 确定是否涉及多个系统或平台

### 2. 项目调研

- 阅读项目现有架构和技术栈文档
- 学习相似功能的实现模式
- 理解代码组织方式和文件结构
- 参考相似功能的任务拆分方式

### 3. 任务设计

基于调研结果，设计多级任务清单：

```
功能模块 (parent_id)
├── 文档设计 (type: docs)
│   ├── API 接口文档
│   ├── 数据模型文档
│   └── 架构文档
├── 数据库设计 (type: docs, 如需)
│   ├── 模型设计
│   ├── 迁移脚本
│   └── 性能优化
├── 开发测试 (type: feature/test)
│   ├── Web 端 (开发 + 单元测试 + 集成测试)
│   ├── Mobile 端 (开发 + 单元测试 + 集成测试)
│   └── Backend 端 (开发 + 单元测试 + 集成测试)
└── 集成测试 (type: test)
    ├── 端到端测试
    ├── 跨端集成
    └── 性能/安全测试
```

### 4. 任务入库

通过批量 uvx 命令将所有任务更新到项目的 task 系统中。

## 相关 Skills

参考以下 Skill 获得更多指导：
- 项目结构分析：`@${CLAUDE_PLUGIN_ROOT}/skills/project-onboarding/SKILL.md`
- 测试策略：`@${CLAUDE_PLUGIN_ROOT}/skills/test-strategy/SKILL.md`
- 代码质量标准：`@${CLAUDE_PLUGIN_ROOT}/skills/code-review-standards/SKILL.md`

## 检查清单

在执行规划前，确保满足以下条件：

- [ ] 已与产品方确认功能需求清晰
- [ ] 已阅读项目的架构文档
- [ ] 已参考相似功能的实现
- [ ] 已确定是否需要数据库设计
- [ ] 已确定是否需要 API 文档设计
- [ ] 已确定目标平台（Web/Mobile/Desktop/Backend）
- [ ] 已确定任务的依赖关系

## 注意事项

- **深入需求理解**：与产品/需求方充分沟通，确保理解清晰准确
- **学习项目模式**：花时间查看相似功能的实现，保持与项目的一致性
- **任务粒度适中**：任务应该粒度适中，可以独立完成和验证
- **文档先行**：所有开发任务前必须完成文档设计
- **测试全覆盖**：每个功能点都应该有对应的单元测试和集成测试任务
- **依赖关系准确**：使用 `--depends` 参数确保任务间的依赖关系正确

## 常见问题

### Q: 如何确定是否需要数据库设计任务？
**A**: 如果功能涉及数据的存储或查询，需要数据库设计任务。包括需要设计数据表、建立索引或编写迁移脚本的情况。

### Q: 多平台应该如何拆分任务？
**A**: 每个平台的功能开发、单元测试都是独立任务。但文档设计、API 设计、数据库设计可以共享，不需要为每个平台重复设计。

### Q: 集成测试和单元测试如何区分？
**A**: 单元测试是模块级测试，测试单个函数或类的功能。集成测试是模块间交互测试，测试不同模块的协作。

### Q: 如何处理跨模块的功能规划？
**A**: 将跨模块部分分别在各自的模块中规划任务，然后添加集成测试任务来验证模块间的交互。

### Q: 任务间的依赖关系如何指定？
**A**: 使用 `--depends` 参数指定任务的前置依赖。例如：`--depends "文档ID,数据库ID"`。

## 其他信息

### 性能考虑

- 规划较大功能时（超过 20 个任务），可能需要较长时间进行分析和设计
- 首次规划可能花费更多时间用于项目调研，后续会更快

### 兼容性

- 适用于所有项目类型（Web、Mobile、Backend、混合）
- 支持任何数据库类型的设计任务
- 支持任何 API 设计方式（REST、GraphQL、RPC 等）

### 扩展和自定义

- 可以基于项目特殊需求调整任务类型和结构
- 可以为特定平台或框架添加额外的任务类型
- 可以根据团队工作方式调整任务的依赖关系
