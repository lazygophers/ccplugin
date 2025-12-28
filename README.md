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

### 安装插件

#### 方法 1：使用远程安装（推荐）

Claude Code 支持直接从 GitHub 安装插件：

```json
{
  "plugins": [
    {
      "source": "github",
      "repo": "lazygophers/ccplugin",
      "path": "plugins/memory"
    },
    {
      "source": "github",
      "repo": "lazygophers/ccplugin",
      "path": "plugins/context"
    },
    {
      "source": "github",
      "repo": "lazygophers/ccplugin",
      "path": "plugins/task"
    },
    {
      "source": "github",
      "repo": "lazygophers/ccplugin",
      "path": "plugins/knowledge"
    }
  ]
}
```

Claude Code 会自动：
- 下载插件代码
- 创建虚拟环境
- 安装依赖
- 启动 MCP Server

#### 方法 2：本地安装

如果需要修改插件或离线使用，可以手动安装：

```bash
# 1. 下载特定插件
# 方式 1: 使用 GitHub CLI
gh repo clone lazygophers/ccplugin -- --depth=1 --filter=blob:none --sparse
cd ccplugin
git sparse-checkout set plugins/memory

# 方式 2: 直接下载单个插件目录
# 访问 https://github.com/lazygophers/ccplugin/tree/master/plugins/memory
# 点击 "Code" -> "Download ZIP"

# 2. 进入插件目录
cd plugins/memory

# 3. 安装依赖
uv venv
source .venv/bin/activate  # Linux/macOS
uv pip install -e ".[dev]"

# 4. 配置 Claude Code
# 在配置中指定本地路径：
```

```json
{
  "plugins": [
    {
      "path": "/absolute/path/to/ccplugin/plugins/memory"
    }
  ]
}
```

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

```bash
# 方式 1: 使用 GitHub CLI 克隆仓库
gh repo clone lazygophers/ccplugin
cd ccplugin

# 方式 2: 使用 HTTPS 克隆
git clone https://github.com/lazygophers/ccplugin.git
cd ccplugin

# 进入特定插件进行开发
cd plugins/memory
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 运行测试
uv run pytest

# 代码格式化
uv run black src/
uv run ruff check src/ --fix

# 类型检查
uv run mypy src/
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
