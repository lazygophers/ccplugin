---
description: 文档生成 - README、API文档、代码注释、CHANGELOG、架构图
user-invocable: false
context: fork
model: sonnet
---

# 文档生成（Documentation Generation）

本 Skill 提供系统化的文档生成指导，从项目README到API文档，确保文档完整、准确、易读。

## 概览

**核心能力**：
1. **README生成** - 项目概览、安装指南、使用示例
2. **API文档** - 接口说明、参数描述、返回值
3. **代码注释** - 函数注释、类注释、模块注释
4. **CHANGELOG** - 版本历史、变更记录
5. **架构图** - 系统架构、模块关系、数据流

**文档类型**：
- **用户文档**：README、使用指南、FAQ
- **开发文档**：API文档、架构文档、贡献指南
- **维护文档**：CHANGELOG、部署文档、故障排查

## 执行流程

### 阶段1：README生成

**目标**：创建完整的项目README

**步骤**：
1. **标准结构**：
   ```markdown
   # 项目名称

   简要描述（1-2句话）

   ## 特性

   - 特性1
   - 特性2
   - 特性3

   ## 安装

   ```bash
   npm install package-name
   ```

   ## 快速开始

   ```javascript
   const pkg = require('package-name');
   pkg.doSomething();
   ```

   ## API文档

   [详细API文档链接]

   ## 配置

   | 选项 | 类型 | 默认值 | 描述 |
   |------|------|--------|------|
   | option1 | string | "default" | 选项说明 |

   ## 示例

   更多示例请参见 [examples/](./examples/)

   ## 贡献

   请阅读 [CONTRIBUTING.md](./CONTRIBUTING.md)

   ## 许可证

   [MIT](./LICENSE)
   ```

2. **关键要素**：
   - **标题和描述**：清晰说明项目用途
   - **徽章**（可选）：构建状态、覆盖率、版本号
   - **安装指南**：详细的安装步骤
   - **快速开始**：最简单的使用示例
   - **API文档**：核心API说明或文档链接
   - **配置选项**：可配置参数说明
   - **示例**：常见使用场景
   - **许可证**：开源许可证

3. **最佳实践**：
   - 使用清晰的标题层级
   - 代码示例可复制粘贴即可运行
   - 提供多语言示例（如适用）
   - 添加截图或GIF（如UI项目）

### 阶段2：API文档生成

**目标**：生成清晰的API文档

**步骤**：
1. **函数文档**：
   ```python
   def calculate_total(items: List[Item], discount: float = 0) -> float:
       """计算订单总金额

       Args:
           items: 订单项列表
           discount: 折扣率（0-1之间），默认为0

       Returns:
           float: 总金额（已应用折扣）

       Raises:
           ValueError: 如果discount不在0-1之间

       Examples:
           >>> items = [Item(price=10), Item(price=20)]
           >>> calculate_total(items, discount=0.1)
           27.0
       """
       if not 0 <= discount <= 1:
           raise ValueError("Discount must be between 0 and 1")

       subtotal = sum(item.price for item in items)
       return subtotal * (1 - discount)
   ```

2. **类文档**：
   ```python
   class UserService:
       """用户服务类

       提供用户管理相关功能，包括注册、登录、更新资料等。

       Attributes:
           db: 数据库连接
           cache: 缓存实例

       Examples:
           >>> service = UserService(db, cache)
           >>> user = service.register("test@example.com", "password")
       """

       def __init__(self, db: Database, cache: Cache):
           """初始化用户服务

           Args:
               db: 数据库连接实例
               cache: 缓存实例
           """
           self.db = db
           self.cache = cache
   ```

3. **自动生成工具**：
   - **Python**：Sphinx、pdoc、mkdocs
   - **JavaScript**：JSDoc、TypeDoc、Docusaurus
   - **Go**：godoc、pkgsite
   - **Java**：Javadoc

### 阶段3：代码注释规范

**目标**：编写清晰、有用的代码注释

**步骤**：
1. **函数注释**（必须）：
   ```typescript
   /**
    * 发送电子邮件
    *
    * @param to - 收件人邮箱地址
    * @param subject - 邮件主题
    * @param body - 邮件正文
    * @returns Promise<boolean> - 发送是否成功
    * @throws EmailError - 当SMTP服务器不可用时
    *
    * @example
    * ```typescript
    * await sendEmail('user@example.com', 'Hello', 'Welcome!');
    * ```
    */
   async function sendEmail(
     to: string,
     subject: string,
     body: string
   ): Promise<boolean> {
     // 实现...
   }
   ```

2. **复杂逻辑注释**（推荐）：
   ```python
   # 使用二分查找优化性能（O(log n)）
   def binary_search(arr, target):
       left, right = 0, len(arr) - 1

       while left <= right:
           mid = (left + right) // 2

           # 如果中间元素等于目标，返回索引
           if arr[mid] == target:
               return mid
           # 目标在左半部分
           elif arr[mid] > target:
               right = mid - 1
           # 目标在右半部分
           else:
               left = mid + 1

       return -1
   ```

3. **TODO注释**：
   ```javascript
   // TODO: 添加错误重试逻辑
   // FIXME: 修复并发条件下的竞态问题
   // HACK: 临时方案，需要重构
   // NOTE: 这里必须使用同步方式，不能改为异步
   ```

### 阶段4：CHANGELOG生成

**目标**：维护清晰的版本历史

**步骤**：
1. **标准格式**（Keep a Changelog）：
   ```markdown
   # Changelog

   All notable changes to this project will be documented in this file.

   The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
   and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

   ## [Unreleased]
   ### Added
   - 新功能预览

   ## [1.2.0] - 2026-03-20
   ### Added
   - JWT authentication (#123)
   - User profile management (#124)

   ### Changed
   - Updated API response format (#128)

   ### Deprecated
   - Old authentication endpoint `/auth/login`

   ### Removed
   - Unused legacy code

   ### Fixed
   - Login timeout issue (#126)

   ### Security
   - Fixed SQL injection vulnerability (#130)

   ## [1.1.0] - 2026-02-15
   ### Added
   - User registration feature

   ## [1.0.0] - 2026-01-01
   ### Added
   - Initial release
   ```

2. **分类规范**：
   - **Added**：新功能
   - **Changed**：现有功能变更
   - **Deprecated**：即将移除的功能
   - **Removed**：已移除的功能
   - **Fixed**：Bug修复
   - **Security**：安全相关变更

3. **自动生成**：
   ```bash
   # 基于git提交历史生成
   npx conventional-changelog -p angular -i CHANGELOG.md -s
   ```

### 阶段5：架构图生成

**目标**：可视化系统架构

**步骤**：
1. **Mermaid图**（推荐）：
   ```markdown
   ```mermaid
   graph TD
       A[用户] --> B[API网关]
       B --> C[用户服务]
       B --> D[订单服务]
       C --> E[数据库]
       D --> E
       D --> F[消息队列]
   ```
   ```

2. **架构图类型**：
   - **系统架构图**：整体系统组件
   - **模块关系图**：模块间依赖
   - **数据流图**：数据流向
   - **部署架构图**：服务器和网络拓扑

3. **工具选择**：
   - **在线工具**：draw.io、Excalidraw
   - **代码生成**：Mermaid、PlantUML
   - **专业工具**：Lucidchart、Visio

## 文档最佳实践

### 文档原则

1. **清晰简洁**：
   - 使用简单语言
   - 避免行话和缩写
   - 一句话一个意思

2. **完整准确**：
   - 覆盖所有公共API
   - 示例可运行
   - 及时更新

3. **用户友好**：
   - 从用户角度编写
   - 提供快速开始指南
   - 包含常见问题

4. **结构化**：
   - 清晰的标题层级
   - 逻辑顺序
   - 目录导航

### 注释原则

**必须注释**：
- 公共API（函数、类、模块）
- 复杂算法
- 非显而易见的逻辑
- 魔法数字

**不需要注释**：
- 显而易见的代码
- 变量命名已经很清楚的
- 重复代码逻辑的

**好的注释**：
```python
# 使用指数退避算法重试，避免服务器过载
max_retries = 3
```

**不好的注释**：
```python
# 设置最大重试次数为3
max_retries = 3
```

### 文档维护

- **代码变更时更新文档**
- **定期审查文档准确性**
- **使用文档生成工具**
- **文档测试（示例代码可运行）**

## 工具集成

### 文档生成工具

**Python**：
- Sphinx - 功能强大、可扩展
- MkDocs - Markdown友好
- pdoc - 轻量级

**JavaScript/TypeScript**：
- JSDoc - 标准注释格式
- TypeDoc - TypeScript专用
- Docusaurus - React文档站点

**Go**：
- godoc - 内置工具
- pkgsite - Go官方文档站点

**通用**：
- Markdown - 轻量级标记语言
- AsciiDoc - 功能丰富的文档格式

### CI集成

```yaml
# GitHub Actions - 自动生成文档
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build docs
        run: npm run docs:build
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

## 输出格式

### 文档清单

```markdown
## 文档清单

### ✅ 必需文档
- [x] README.md - 项目概览
- [x] API.md - API文档
- [x] CHANGELOG.md - 版本历史
- [x] LICENSE - 开源许可证

### 📋 推荐文档
- [x] CONTRIBUTING.md - 贡献指南
- [x] CODE_OF_CONDUCT.md - 行为准则
- [ ] ARCHITECTURE.md - 架构文档
- [ ] DEPLOYMENT.md - 部署指南

### 📚 可选文档
- [ ] FAQ.md - 常见问题
- [ ] TROUBLESHOOTING.md - 故障排查
- [ ] MIGRATION.md - 迁移指南
```

## 相关 Skills

- **code-review** - 代码审查（注释质量检查）
- **architecture-review** - 架构评审（架构文档生成）
- **git-workflow** - Git工作流（CHANGELOG维护）
