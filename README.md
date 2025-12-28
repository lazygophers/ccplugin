# CC Plugin Marketplace

Claude Code 插件市场 - 提供记忆、上下文、任务和知识库管理的独立插件集合。

## 概述

本仓库是一个插件市场，包含多个独立的 Claude Code 插件。每个插件都可以**独立安装和使用**，用户可以根据需求选择安装部分或全部插件。

## 可用插件

### 🧠 Memory Plugin - 记忆管理插件

基于知识图谱的记忆存储和检索系统。

**功能**：
- 长期记忆存储
- 标签化检索
- 元数据关联
- 知识图谱关系

**安装**: [plugins/memory/](plugins/memory/)

---

### 📝 Context Plugin - 上下文管理插件

会话上下文的持久化和恢复系统。

**功能**：
- 会话上下文保存
- 多角色上下文追踪
- 历史上下文检索
- 跨会话工作流

**安装**: [plugins/context/](plugins/context/)

---

### ✅ Task Plugin - 任务管理插件

开发任务的创建和管理系统。

**功能**：
- 结构化任务创建
- 优先级和状态管理
- 标签过滤
- 任务依赖关系

**安装**: [plugins/task/](plugins/task/)

---

### 📚 Knowledge Plugin - 知识库管理插件

基于向量数据库的知识管理系统。

**功能**：
- 向量数据库存储
- 语义搜索
- 多源知识整合
- 知识图谱关联

**安装**: [plugins/knowledge/](plugins/knowledge/)

---

## 快速开始

### 前置要求

- Claude Code >= 1.0.0
- Python >= 3.10
- uv (推荐) 或 pip

### 添加插件市场

首先将本市场添加到 Claude Code：

```
/marketplace add lazygophers/ccplugin
```

这会将 CC Plugin Marketplace 添加到您的可用市场列表中。

### 安装插件

#### 使用 `/plugin` 命令安装（推荐）

添加市场后，在 Claude Code 中直接使用命令安装插件：

```
# 安装单个插件
/plugin install lazygophers/ccplugin/plugins/memory

# 安装所有插件
/plugin install lazygophers/ccplugin/plugins/memory
/plugin install lazygophers/ccplugin/plugins/context
/plugin install lazygophers/ccplugin/plugins/task
/plugin install lazygophers/ccplugin/plugins/knowledge
```

Claude Code 会自动完成：
- ✅ 从 GitHub 下载插件代码
- ✅ 创建 Python 虚拟环境
- ✅ 安装所需依赖
- ✅ 启动 MCP Server
- ✅ 配置插件设置

安装完成后，插件即可使用，无需手动配置。

#### 查看和管理插件

```
# 列出已安装的插件
/plugin list

# 更新插件
/plugin update lazygophers/ccplugin/plugins/memory

# 卸载插件
/plugin uninstall memory
```

#### 管理市场

```
# 列出所有已添加的市场
/marketplace list

# 更新市场信息
/marketplace update lazygophers/ccplugin

# 移除市场
/marketplace remove lazygophers/ccplugin
```

## 使用示例

安装插件后，即可在 Claude Code 中使用插件提供的功能：

### Memory Plugin - 存储和检索记忆

```
存储一条记忆：重要的项目决策是使用 PostgreSQL 数据库
标签：database, decision

搜索记忆：数据库相关的决策
```

### Context Plugin - 保存会话上下文

```
保存当前讨论到上下文，会话ID: feature-123

恢复会话 feature-123 的历史上下文
```

### Task Plugin - 管理开发任务

```
创建任务：实现用户登录功能
优先级：高
类型：feature

列出所有进行中的任务

查看任务详情：tk-001
```

### Knowledge Plugin - 知识库搜索

```
添加知识：Python 最佳实践文档
来源：官方文档

搜索知识：Python 异步编程
```

详细使用方法请查看各插件的 README 文档。

## 项目结构

```
ccplugin/                        # 插件市场根目录
├── marketplace.json             # 市场元数据
├── README.md                    # 本文件
├── plugins/                     # 插件目录
│   ├── memory/                  # 记忆管理插件
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── src/memory/
│   │   │   ├── server.py        # MCP Server
│   │   │   └── ...
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   ├── context/                 # 上下文管理插件
│   │   ├── .claude-plugin/
│   │   ├── src/context/
│   │   ├── tests/
│   │   └── README.md
│   ├── task/                    # 任务管理插件
│   │   ├── .claude-plugin/
│   │   ├── src/task/
│   │   ├── tests/
│   │   └── README.md
│   └── knowledge/               # 知识库管理插件
│       ├── .claude-plugin/
│       ├── src/knowledge/
│       ├── tests/
│       └── README.md
└── docs/                        # 市场文档
    ├── 插件能力说明.md
    ├── 快速开始.md
    └── ...
```

## 插件独立性

每个插件都是**完全独立**的：

- ✅ 独立的 MCP Server
- ✅ 独立的依赖管理 (pyproject.toml)
- ✅ 独立的配置文件 (.claude-plugin/plugin.json)
- ✅ 独立的测试套件
- ✅ 可单独安装和卸载

## 技术栈

**共同依赖**：
- MCP SDK >= 1.1.0
- Pydantic >= 2.0
- Python >= 3.10

**插件特定依赖**：
- Memory: NetworkX (知识图谱)
- Context: SQLAlchemy (会话存储)
- Task: SQLAlchemy (任务数据库)
- Knowledge: ChromaDB (向量数据库)

## 开发

### 开发环境设置

> 仅供插件开发者使用。普通用户请使用 `/plugin install` 命令安装。

如果您想修改或开发插件，请按以下步骤设置开发环境：

```bash
# 1. 克隆仓库（开发者模式）
git clone https://github.com/lazygophers/ccplugin.git
cd ccplugin

# 2. 进入特定插件目录
cd plugins/memory

# 3. 创建开发环境
uv venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 4. 安装开发依赖
uv pip install -e ".[dev]"

# 5. 运行测试
uv run pytest

# 6. 代码质量检查
uv run black src/       # 格式化
uv run ruff check src/  # 代码检查
uv run mypy src/        # 类型检查
```

### 添加新插件

1. 在 `plugins/` 下创建新目录
2. 参考现有插件结构创建文件
3. 在 `marketplace.json` 中注册插件
4. 添加插件文档

## 路线图

**v0.1.0** (当前)
- [x] 插件市场基础架构
- [x] 4 个插件的接口实现
- [x] 完整的测试覆盖

**v0.2.0** (计划)
- [ ] Memory Plugin 完整实现
  - [ ] NetworkX 知识图谱
  - [ ] 关系推理
  - [ ] 记忆合并

**v0.3.0** (计划)
- [ ] Context Plugin 完整实现
  - [ ] SQLAlchemy 会话存储
  - [ ] 上下文压缩
  - [ ] 智能摘要

**v0.4.0** (计划)
- [ ] Task Plugin 完整实现
  - [ ] 任务依赖管理
  - [ ] 状态流转
  - [ ] 优先级调度

**v0.5.0** (计划)
- [ ] Knowledge Plugin 完整实现
  - [ ] ChromaDB 向量检索
  - [ ] 多模态支持
  - [ ] 知识图谱整合

## 贡献

欢迎贡献！请：

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 支持

如有问题或建议，请在 [GitHub Issues](https://github.com/lazygophers/ccplugin/issues) 上创建 issue。

## 作者

luoxin

---

**注意**: 每个插件都有独立的文档和使用说明，请查看各插件目录下的 README.md 文件。
