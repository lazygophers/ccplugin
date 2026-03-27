---
description: 代码检查器 - 本地+GitHub统一代码分析接口，支持质量/债务/性能检测
user-invocable: false
context: fork
model: sonnet
memory: project
---

# 代码检查器（Code Inspector）

## 核心职责

提供本地代码库和GitHub远程仓库的统一分析接口。

## 激活时机

代码分析类任务（code-analyst调用）或项目评估任务（project-assessor调用）。

## 统一接口

### 本地代码分析

```
analyze_code(
    path="./src",
    depth="full",  # quick | moderate | full
    focus=["quality", "debt", "performance"]
)
```

### GitHub代码分析

```
analyze_github(
    repo="facebook/react",
    branch="main",
    depth="full",
    focus=["health", "security", "community"]
)
```

---

## 本地分析能力

### 1. 静态分析

**圈复杂度检测**：
- 函数复杂度（McCabe）
- 认知复杂度（Cognitive Complexity）
- 阈值：>10警告，>20错误

**代码重复检测**：
- 重复代码块识别
- 重复率计算（%）
- 建议：<5%

### 2. 依赖分析

**依赖关系图**：
- 模块依赖可视化
- 循环依赖检测
- 耦合度分析

**依赖版本**：
- 过时依赖识别
- 安全漏洞扫描（CVE）
- 许可证合规检查

### 3. 测试覆盖率

**覆盖率统计**：
- 行覆盖率（Line Coverage）
- 分支覆盖率（Branch Coverage）
- 函数覆盖率（Function Coverage）
- 目标：≥80%

### 4. 代码质量

**质量指标**：
- 命名规范检查
- 注释完整度
- 函数长度（建议<50行）
- 文件长度（建议<500行）

---

## GitHub 分析能力

### 1. 项目健康度

**活跃度评分（40%权重）**：
- Commit频率（月均>10）
- Issue响应时间（<24h）
- PR合并速度（<7天）

**质量评分（30%权重）**：
- 代码审查率（PR→Review）
- 测试覆盖率（≥80%）
- CI/CD通过率（≥95%）

**社区评分（20%权重）**：
- Stars增长趋势
- Contributors数量
- Issue/PR参与度

**维护评分（10%权重）**：
- 最后更新时间（<3个月）
- 依赖更新频率
- 安全漏洞修复速度

### 2. GitHub CLI（gh 命令）

使用 `gh` 命令替代 GitHub MCP 工具：
```
gh repo view             - 仓库基本信息
gh issue list            - Issue列表
gh pr list               - PR列表
gh api repos/{owner}/{repo}/contents/{path} - 文件内容
gh api repos/{owner}/{repo}/search - 仓库搜索
gh issue view            - Issue详情
gh repo clone            - 克隆仓库
```

### 3. 趋势分析

**GitHub统计**：
- Stars历史趋势
- Fork/Watch比率
- 贡献者增长曲线
- Issue关闭率

---

## 质量指标定义

### 代码质量评分（0-10）

```
质量分 = 可读性(30%) + 可维护性(30%) + 可测试性(20%) + 安全性(20%)
```

**可读性**：命名、注释、代码组织
**可维护性**：模块化、耦合度、复杂度
**可测试性**：依赖注入、接口抽象
**安全性**：注入漏洞、敏感信息

### 项目健康度评分（0-10）

```
健康分 = 活跃度(40%) + 质量(30%) + 社区(20%) + 维护(10%)
```

---

## 详细文档

- [local-analysis.md](local-analysis.md) - 本地分析方法详解
- [github-integration.md](github-integration.md) - GitHub集成和API使用
- [metrics.md](metrics.md) - 质量指标定义

---

## 使用示例

```python
# 本地分析
result = analyze_code(
    path="./src",
    depth="full",
    focus=["quality", "debt"]
)

# GitHub分析
health = analyze_github(
    repo="facebook/react",
    depth="moderate",
    focus=["health", "security"]
)
```
