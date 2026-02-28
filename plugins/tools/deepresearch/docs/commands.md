# 命令系统

Deep Research 插件提供深度研究命令。

## 命令列表

| 命令 | 描述 | 用法 |
|------|------|------|
| `/deep-research` | 执行深度研究 | `/deep-research <type> [options]` |

## /deep-research - 执行深度研究

### 研究类型

| 类型 | 描述 | 示例 |
|------|------|------|
| `本地代码分析` | 分析本地代码库 | `/deep-research 本地代码分析 --scope ./src` |
| `github项目研究` | 研究 GitHub 项目 | `/deep-research github项目研究 --project facebook/react` |
| `依赖包分析` | 分析第三方依赖 | `/deep-research 依赖包分析 --security` |
| `关键词探索` | 深度主题研究 | `/deep-research 关键词探索 "微服务架构"` |
| `架构分析` | 分析系统架构 | `/deep-research 架构分析 --design-doc ./architecture.md` |
| `技术方案搜索` | 搜索对比技术方案 | `/deep-research 技术方案搜索 "REST vs GraphQL"` |

### 选项

| 选项 | 描述 |
|------|------|
| `--scope` | 指定分析范围 |
| `--project` | 指定 GitHub 项目 |
| `--security` | 启用安全分析 |
| `--design-doc` | 指定设计文档 |

### 使用示例

**本地代码分析**：

```bash
/deep-research 本地代码分析 --scope ./src
```

**GitHub 项目研究**：

```bash
/deep-research github项目研究 --project facebook/react
```

**依赖包安全分析**：

```bash
/deep-research 依赖包分析 --security
```

**关键词探索**：

```bash
/deep-research 关键词探索 "微服务架构最佳实践"
```

## 研究流程

1. **问题优化** - 将模糊问题转化为结构化研究计划
2. **多智能体研究** - 并行执行多维度研究任务
3. **引用验证** - A-E级质量评估和链式验证
4. **知识合成** - 自动整合多源发现生成综合报告

## 输出格式

```markdown
# 研究报告：[主题]

## 摘要

简要总结研究发现。

## 主要发现

### 发现1
- 来源：[A级]
- 内容：...

### 发现2
- 来源：[B级]
- 内容：...

## 建议

1. 建议1
2. 建议2

## 参考资料

- [1] 来源1 [A级]
- [2] 来源2 [B级]
```
