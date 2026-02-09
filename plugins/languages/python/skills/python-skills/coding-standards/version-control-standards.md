# Python 版本控制规范

## 核心原则

### ✅ 必须遵守

1. **Git 工作流** - 使用 Git Flow 或 GitHub Flow 工作流
2. **分支命名** - 分支名称清晰表达意图
3. **提交信息** - 提交信息清晰描述变更
4. **代码审查** - 所有代码变更必须经过审查
5. **版本标签** - 使用语义化版本号

### ❌ 禁止行为

- 直接提交到主分支
- 提交信息不清晰
- 跳过代码审查
- 不使用版本标签
- 提交语法错误或测试失败的代码

## Git 工作流

### GitHub Flow

```
main (主分支)
    ↑
    │
feature/user-login (功能分支)
```

**流程**：

1. 从 main 分支创建功能分支
2. 在功能分支上开发
3. 提交代码并创建 Pull Request
4. 代码审查通过后合并到 main
5. 删除功能分支

### Git Flow

```
main (主分支)
    ↑
    │
develop (开发分支)
    ↑
    │
feature/user-login (功能分支)
```

**流程**：

1. 从 develop 分支创建功能分支
2. 在功能分支上开发
3. 提交代码并创建 Pull Request 到 develop
4. 代码审查通过后合并到 develop
5. 从 develop 创建 release 分支
6. 测试通过后合并到 main 和 develop
7. 从 main 创建标签

## 分支命名

### 功能分支

```bash
# ✅ 正确 - 清晰的功能分支命名
git checkout -b feature/user-login
git checkout -b feature/add-friend-api
git checkout -b feature/improve-performance

# ❌ 错误 - 不清晰的分支命名
git checkout -b feature1
git checkout -b new-feature
git checkout -b test
```

### 修复分支

```bash
# ✅ 正确 - 清晰的修复分支命名
git checkout -b fix/login-error
git checkout -b fix/memory-leak
git checkout -b hotfix/security-issue

# ❌ 错误 - 不清晰的分支命名
git checkout -b fix1
git checkout -b bugfix
```

### 发布分支

```bash
# ✅ 正确 - 清晰的发布分支命名
git checkout -b release/v1.0.0
git checkout -b release/v2.1.0

# ❌ 错误 - 不清晰的分支命名
git checkout -b release
git checkout -b v1.0.0
```

## 提交信息

### 提交信息格式（Conventional Commits）

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 提交类型

| 类型   | 说明     | 示例                     |
| ------ | -------- | ------------------------ |
| feat   | 新功能   | feat(user): 添加用户登录   |
| fix    | 修复     | fix(auth): 修复认证错误     |
| docs   | 文档     | docs(readme): 更新 README   |
| style  | 格式     | style(format): 格式化代码   |
| refactor | 重构   | refactor(api): 重构 API    |
| test   | 测试     | test(user): 添加用户测试   |
| chore  | 构建/工具 | chore(deps): 更新依赖      |
| perf   | 性能     | perf(db): 优化数据库查询    |
| ci     | CI/CD    | ci(github): 更新工作流      |

### 提交信息示例

```bash
# ✅ 正确 - 清晰的提交信息
git commit -m "feat(user): 添加用户登录功能

实现用户登录接口，支持用户名和密码验证。

- 添加 login 函数
- 添加密码验证逻辑
- 添加登录测试
"

git commit -m "fix(auth): 修复认证中间件错误

修复认证中间件在处理无效令牌时的错误。
"

git commit -m "docs(readme): 更新快速开始指南

更新 README.md 中的快速开始部分，添加更多示例。
"

# ❌ 错误 - 不清晰的提交信息
git commit -m "update"
git commit -m "fix bug"
git commit -m "add feature"
```

### Python 特定提交类型

```bash
# ✅ 正确 - Python 项目特定提交
git commit -m "feat(types): 添加类型注解

为所有公共 API 添加完整的类型注解。
"

git commit -m "chore(deps): 升级到 Python 3.11

更新项目依赖，支持 Python 3.11 新特性。
"

git commit -m "test(pytest): 添加集成测试

使用 pytest 添加端到端集成测试。
"

git commit -m "fix(typing): 修复类型注解错误

修复 Optional 类型的错误使用。
"

git commit -m "style(ruff): 应用 Ruff 格式化

使用 Ruff 统一代码格式。
"
```

## Pull Request

### PR 标题

```markdown
# ✅ 正确 - 清晰的 PR 标题
feat(user): 添加用户登录功能
fix(auth): 修复认证中间件错误
docs(readme): 更新快速开始指南

# ❌ 错误 - 不清晰的 PR 标题
update
fix bug
add feature
```

### PR 描述

```markdown
# ✅ 正确 - 完整的 PR 描述
## 变更说明

添加用户登录功能，支持用户名和密码验证。

## 变更内容

- 添加 `login` 函数
- 添加密码验证逻辑
- 添加登录测试
- 更新 API 文档

## 测试

- [x] 单元测试通过
- [x] 集成测试通过
- [x] 手动测试通过

## 类型检查

- [x] mypy 类型检查通过

## 代码质量

- [x] Ruff 检查通过
- [x] Ruff 格式化已应用

## 截图

（如果有 UI 变更，添加截图）

## 相关 Issue

Closes #123

# ❌ 错误 - 不完整的 PR 描述
添加用户登录功能。
```

### PR 审查清单

```markdown
## 审查清单

- [ ] 代码符合 PEP 8 规范
- [ ] 类型注解完整
- [ ] 测试覆盖充分
- [ ] 文档已更新
- [ ] 无语法错误
- [ ] 无测试失败
- [ ] 提交信息清晰
- [ ] 变更范围合理
- [ ] mypy 检查通过
- [ ] Ruff 检查通过
```

## 版本标签

### 语义化版本

```
MAJOR.MINOR.PATCH

MAJOR：不兼容的 API 变更
MINOR：向后兼容的功能性新增
PATCH：向后兼容的问题修正
```

### 版本标签示例

```bash
# ✅ 正确 - 语义化版本标签
git tag -a v1.0.0 -m "首次发布"
git tag -a v1.1.0 -m "添加用户登录功能"
git tag -a v1.1.1 -m "修复登录错误"

# ❌ 错误 - 不规范的版本标签
git tag -a 1.0.0 -m "首次发布"
git tag -a v1 -m "首次发布"
git tag -a release -m "首次发布"
```

### Python 版本标签

```bash
# ✅ 正确 - 使用 Python 包版本
# 在 pyproject.toml 中更新版本
# 然后
git add pyproject.toml
git commit -m "chore(version): bump version to 1.1.0"
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0

# ✅ 正确 - 使用 setuptools_scm 自动版本
# pyproject.toml 配置
[project]
dynamic = ["version"]

[tool.setuptools_scm]
write_to = "src/myproject/_version.py"

# 标签自动成为版本号
git tag v1.0.0
python -c "import myproject; print(myproject.__version__)"
# 输出: 1.0.0
```

### 发布流程

```bash
# 1. 创建发布分支
git checkout -b release/v1.0.0

# 2. 更新版本号
# 编辑 pyproject.toml
# version = "1.0.0"

# 3. 运行测试
uv run pytest

# 4. 运行类型检查
uv run mypy src/

# 5. 运行代码检查
uv run ruff check .
uv run ruff format .

# 6. 更新 CHANGELOG
# 编辑 CHANGELOG.md

# 7. 提交变更
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): prepare for v1.0.0"

# 8. 合并到 main
git checkout main
git merge release/v1.0.0

# 9. 创建标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 10. 推送标签
git push origin v1.0.0

# 11. 构建和发布
uv build
uv publish

# 12. 合并到 develop（如果使用 Git Flow）
git checkout develop
git merge release/v1.0.0

# 13. 删除发布分支
git branch -d release/v1.0.0
```

## .gitignore 配置

### Python 项目标准 .gitignore

```gitignore
# ✅ 正确 - 完整的 Python .gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# poetry
poetry.lock

# pdm
.pdm.toml

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# Project specific
*.db
*.sqlite
data/
cache/
logs/
*.log

# uv
.uv/
uv.lock

# ruff
.ruff_cache/
```

## 预提交钩子（pre-commit）

### pre-commit 配置

```yaml
# .pre-commit-config.yaml
repos:
  # 通用检查
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: detect-private-key
      - id: mixed-line-ending

  # Ruff - Python 代码格式化和检查
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.14
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # mypy - 类型检查
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic
          - types-requests
        args: [--strict, --ignore-missing-imports]

  # bandit - 安全检查
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
        additional_dependencies: ["bandit[toml]"]

  # safety - 依赖安全检查
  - repo: https://github.com/Lucas-C/pre-commit-hooks-safety
    rev: v1.3.3
    hooks:
      - id: python-safety-dependencies-check
        files: pyproject.toml
```

### 安装和使用 pre-commit

```bash
# ✅ 安装 pre-commit
uv pip install pre-commit

# ✅ 安装钩子
pre-commit install

# ✅ 手动运行所有钩子
pre-commit run --all-files

# ✅ 运行特定钩子
pre-commit run ruff --all-files

# ✅ 跳过钩子（不推荐）
git commit --no-verify -m "message"

# ✅ 更新钩子版本
pre-commit autoupdate

# ✅ 移除钩子
pre-commit uninstall
```

### 本地预提交钩子

```bash
# .git/hooks/pre-commit
#!/bin/bash
set -e

echo "运行预提交检查..."

# 运行 Ruff
echo "运行 Ruff 检查..."
uv run ruff check .
uv run ruff format --check .

# 运行 mypy
echo "运行类型检查..."
uv run mypy src/

# 运行测试
echo "运行测试..."
uv run pytest

echo "预提交检查通过！"
```

## 提交最佳实践

### 提交前检查清单

```bash
# ✅ 正确 - 提交前检查
#!/bin/bash
# check-before-commit.sh

echo "提交前检查..."

# 1. 格式化代码
echo "格式化代码..."
uv run ruff format .
uv run ruff check --fix .

# 2. 类型检查
echo "类型检查..."
uv run mypy src/

# 3. 运行测试
echo "运行测试..."
uv run pytest

# 4. 检查是否有 TODO/FIXME
echo "检查待办事项..."
if git diff --cached | grep -q "TODO\|FIXME"; then
    echo "警告：提交包含 TODO 或 FIXME"
    read -p "是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "检查完成！"
```

### 提交流程

```bash
# ✅ 正确 - 标准提交流程
# 1. 查看变更
git status

# 2. 暂存文件
git add file.py
# 或暂存所有变更
git add .

# 3. 检查差异
git diff --cached

# 4. 运行检查
uv run ruff check .
uv run ruff format .
uv run mypy src/
uv run pytest

# 5. 提交
git commit -m "feat(user): 添加用户登录功能"

# 6. 推送
git push origin feature/user-login
```

### 交互式暂存

```bash
# ✅ 正确 - 交互式暂存文件块
git add -p

# ✅ 正确 - 交互式暂存文件
git add -i

# ✅ 正确 - 修改最后一次提交
git commit --amend

# ✅ 正确 - 修改提交信息
git commit --amend -m "new message"
```

## 检查清单

提交代码前，确保：

- [ ] 使用正确的分支命名
- [ ] 提交信息清晰描述变更
- [ ] 提交信息符合 Conventional Commits 格式
- [ ] 代码已通过类型检查（mypy）
- [ ] 代码已通过代码检查（ruff）
- [ ] 代码已通过测试（pytest）
- [ ] 代码已通过预提交钩子
- [ ] 文档已更新
- [ ] 无语法错误
- [ ] 无测试失败
- [ ] 使用语义化版本号
- [ ] 发布时创建版本标签
