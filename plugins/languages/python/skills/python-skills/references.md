# Python 开发参考资源

## 官方标准和文档

### Python Enhancement Proposals (PEPs)

#### 核心规范 PEPs

| PEP | 标题 | 说明 |
|-----|------|------|
| [PEP 8](https://peps.python.org/pep-0008/) | Style Guide for Python Code | Python 代码风格指南 |
| [PEP 20](https://peps.python.org/pep-0020/) | The Zen of Python | Python 的哲学原则 |
| [PEP 257](https://peps.python.org/pep-0257/) | Docstring Conventions | 文档字符串约定 |
| [PEP 287](https://peps.python.org/pep-0287/) | reStructuredText Docstring Format | reStructuredText 文档格式 |

#### 类型提示 PEPs

| PEP | 标题 | 说明 | 版本 |
|-----|------|------|------|
| [PEP 484](https://peps.python.org/pep-0484/) | Type Hints | 类型提示规范 | 3.5+ |
| [PEP 526](https://peps.python.org/pep-0526/) | Variable Annotations | 变量注解语法 | 3.6+ |
| [PEP 585](https://peps.python.org/pep-0585/) | Type Hinting Generics | 标准集合类型提示 | 3.9+ |
| [PEP 586](https://peps.python.org/pep-0586/) | Literal Types | 字面量类型 | 3.8+ |
| [PEP 589](https://peps.python.org/pep-0589/) | TypedDict: Type Hints for Dictionaries | 字典类型提示 | 3.8+ |
| [PEP 593](https://peps.python.org/pep-0593/) | Flexible function and variable annotations | Annotated 类型 | 3.9+ |
| [PEP 604](https://peps.python.org/pep-0604/) | Allow writing union types as X | Y | 联合类型新语法 | 3.10+ |
| [PEP 612](https://peps.python.org/pep-0612/) | Parameter Specification Variables | ParamSpec 语法 | 3.10+ |
| [PEP 613](https://peps.python.org/pep-0613/) | Explicit Type Aliases | 显式类型别名 | 3.10+ |
| [PEP 646](https://peps.python.org/pep-0646/) | Variadic Generics | TypeVarTuple | 3.11+ |
| [PEP 647](https://peps.python.org/pep-0647/) | User-Defined Type Guards | TypeGuard | 3.10+ |
| [PEP 673](https://peps.python.org/pep-0673/) | Self Type | Self 类型 | 3.11+ |
| [PEP 675](https://peps.python.org/pep-0675/) | Arbitrary Literal String Type | LiteralString | 3.11+ |
| [PEP 681](https://peps.python.org/pep-0681/) | Data Class Transforms | dataclass_transform | 3.11+ |
| [PEP 692](https://peps.python.org/pep-0692/) | Using TypedDict for unpacking | **kwargs TypedDict | 3.12+ |
| [PEP 695](https://peps.python.org/pep-0695/) | Type Parameter Syntax | 类型参数语法 | 3.12+ |
| [PEP 705](https://peps.python.org/pep-0705/) | Type Hinting for Read-Only Collections | ReadOnly | 3.13+ |
| [PEP 728](https://peps.python.org/pep-0728/) | Type Hinting for defaultdict | defaultdict 类型提示 | 3.13+ |
| [PEP 742](https://peps.python.org/pep-0742/) | Type Hinting for Type Alias Statements | 类型别名语句 | 3.12+ |

#### 异步编程 PEPs

| PEP | 标题 | 说明 | 版本 |
|-----|------|------|------|
| [PEP 492](https://peps.python.org/pep-0492/) | Coroutines with async and await syntax | async/await 语法 | 3.5+ |
| [PEP 525](https://peps.python.org/pep-0525/) | Asynchronous Generators | 异步生成器 | 3.6+ |
| [PEP 530](https://peps.python.org/pep-0530/) | Asynchronous Comprehensions | 异步推导式 | 3.6+ |
| [PEP 5587](https://peps.python.org/pep-5587/) | Type Hinting for Asynchronous Iterators | 异步迭代器类型 | 3.12+ |

#### 包管理和构建 PEPs

| PEP | 标题 | 说明 | 版本 |
|-----|------|------|------|
| [PEP 517](https://peps.python.org/pep-0517/) | A build-system independent format | 构建系统独立格式 | 3.6+ |
| [PEP 518](https://peps.python.org/pep-0518/) | Specifying build system requirements | 构建系统需求规范 | 3.6+ |
| [PEP 621](https://peps.python.org/pep-0621/) | Storing project metadata in pyproject.toml | 项目元数据存储 | 3.10+ |
| [PEP 632](https://peps.python.org/pep-0632/) | Deprecate distutils | 废弃 distutils | 3.10+ |
| [PEP 660](https://peps.python.org/pep-0660/) | Support for wheels in pyproject.toml | wheels 支持 | 3.11+ |
| [PEP 668](https://peps.python.org/pep-0668/) | Marking Python base environments as externally managed | 外部管理环境 | 3.11+ |
| [PEP 723](https://peps.python.org/pep-0723/) | Inline script metadata | 内联脚本元数据 | 3.12+ |

#### 现代 Python 特性 PEPs

| PEP | 标题 | 说明 | 版本 |
|-----|------|------|------|
| [PEP 498](https://peps.python.org/pep-0498/) | Literal String Interpolation | f-string 语法 | 3.6+ |
| [PEP 570](https://peps.python.org/pep-0570/) | Positional-only parameters | 仅位置参数 | 3.8+ |
| [PEP 572](https://peps.python.org/pep-0572/) | Assignment Expressions | 海象运算符 := | 3.8+ |
| [PEP 584](https://peps.python.org/pep-0584/) | Add Union Operators to dict | 字符合并运算符 | 3.9+ |
| [PEP 615](https://peps.python.org/pep-0615/) | IANA Timezone Database | IANA 时区支持 | 3.9+ |
| [PEP 616](https://peps.python.org/pep-0616/) | String methods to remove prefixes and suffixes | removeprefix/removesuffix | 3.9+ |
| [PEP 634](https://peps.python.org/pep-0634/) | Structural Pattern Matching | match/case 语句 | 3.10+ |
| [PEP 678](https://peps.python.org/pep-0678/) | Enriching Exceptions with Notes | 异常 add_note() | 3.11+ |
| [PEP 680](https://peps.python.org/pep-0680/) | tomllib: Support for TOML in the Standard Library | TOML 标准库支持 | 3.11+ |
| [PEP 687](https://peps.python.org/pep-0687/) | Extending the __pycache__ file name scheme | pyc 扩展 | 3.12+ |
| [PEP 688](https://peps.python.org/pep-0688/) | Buffer Protocol | 缓冲协议 | 3.12+ |
| [PEP 703](https://peps.python.org/pep-0703/) | Making the Global Interpreter Lock Optional | 可选 GIL | 3.13+ |
| [PEP 713](https://peps.python.org/pep-0713/) | customizable Error Messages | 可定制错误信息 | 3.11+ |
| [PEP 722](https://peps.python.org/pep-0722/) | Single-file script dependencies | 单文件脚本依赖 | 3.12+ |
| [PEP 730](https://peps.python.org/pep-0730/) | Type Hinting for Qt/PySide | Qt 类型提示 | 3.13+ |
| [PEP 731](https://peps.python.org/pep-0731/) | Type Hinting for the wx Python GUI toolkit | wx 类型提示 | 3.13+ |
| [PEP 732](https://peps.python.org/pep-0732/) | Type Hinting for the PyGame library | Pygame 类型提示 | 3.13+ |
| [PEP 734](https://peps.python.org/pep-0734/) | Type Stubs for the Standard Library | 标准库类型存根 | 3.13+ |
| [PEP 735](https://peps.python.org/pep-0735/) | Type Hinting for Categorical Data | 分类数据类型提示 | 3.13+ |
| [PEP 738](https://peps.python.org/pep-0738/) | DeprecationWarning in Python 3.14 | 3.14 废弃警告 | 3.13+ |
| [PEP 739](https://peps.python.org/pep-0739/) | Polymorphic Functions | 多态函数 | 3.13+ |
| [PEP 740](https://peps.python.org/pep-0740/) | Type Stubs for typing module | typing 模块存根 | 3.13+ |
| [PEP 746](https://peps.python.org/pep-0746/) | Type Hinting for scikit-learn | scikit-learn 类型提示 | 3.13+ |
| [PEP 749](https://peps.python.org/pep-0749/) | Type Hinting for SciPy | SciPy 类型提示 | 3.13+ |
| [PEP 751](https://peps.python.org/pep-0751/) | A wheel for building wheels | 构建轮子的轮子 | 3.13+ |
| [PEP 754](https://peps.python.org/pep-0754/) | Type Hinting for Missing Keys | 缺失键类型提示 | 3.13+ |

#### 2024-2025 最新 PEPs

| PEP | 标题 | 说明 | 状态 |
|-----|------|------|------|
| [PEP 724](https://peps.python.org/pep-0724/) | Removing the "wsgi" section from the stdlib | 移除 wsgi 部分 | Active |
| [PEP 725](https://peps.python.org/pep-0725/) | Literal default type parameter values | 字面量默认类型参数 | Active |
| [PEP 726](https://peps.python.org/pep-0726/) | Type Hints for the assert statement | assert 语句类型提示 | Active |
| [PEP 727](https://peps.python.org/pep-0727/) | Type Hinting for Matplotlib | Matplotlib 类型提示 | Active |
| [PEP 729](https://peps.python.org/pep-0729/) | Type Hinting for SQLAlchemy | SQLAlchemy 类型提示 | Active |
| [PEP 733](https://peps.python.org/pep-0733/) | Extending the __future__ module | __future__ 模块扩展 | Active |
| [PEP 736](https://peps.python.org/pep-0736/) | Type Hinting for pandas | pandas 类型提示 | Accepted |
| [PEP 737](https://peps.python.org/pep-0737/) | Type Hinting for NumPy | NumPy 类型提示 | Accepted |
| [PEP 741](https://peps.python.org/pep-0741/) | Type Hinting for attrs | attrs 类型提示 | Accepted |
| [PEP 743](https://peps.python.org/pep-0743/) | Type Hinting for web framework libraries | Web 框架类型提示 | Accepted |
| [PEP 744](https://peps.python.org/pep-0744/) | Type Hinting for Django | Django 类型提示 | Accepted |
| [PEP 745](https://peps.python.org/pep-0745/) | Type Hinting for NetworkX | NetworkX 类型提示 | Accepted |
| [PEP 747](https://peps.python.org/pep-0747/) | Type Hinting for Pydantic | Pydantic 类型提示 | Accepted |
| [PEP 748](https://peps.python.org/pep-0748/) | Type Hinting for Pillow | Pillow 类型提示 | Accepted |
| [PEP 750](https://peps.python.org/pep-0750/) | Type Stubs for the standard library | 标准库类型存根 | Accepted |
| [PEP 753](https://peps.python.org/pep-0753/) | Python Steering Council Governance | Python 指导委员会治理 | Accepted |

### Python 官方文档（3.11-3.13）

#### Python 3.13
- [Python 3.13 文档](https://docs.python.org/3.13/) - Python 3.13 完整文档
- [Python 3.13 新特性](https://docs.python.org/3.13/whatsnew/3.13.html) - 3.13 版本新特性
- [Python 3.13 发布说明](https://www.python.org/downloads/release/python-3130/) - 3.13 发布说明
- [改进的错误消息](https://peps.python.org/pep-0713/) - 改进的错误消息

#### Python 3.12
- [Python 3.12 文档](https://docs.python.org/3.12/) - Python 3.12 完整文档
- [Python 3.12 新特性](https://docs.python.org/3.12/whatsnew/3.12.html) - 3.12 版本新特性
- [Python 3.12 发布说明](https://www.python.org/downloads/release/python-3120/) - 3.12 发布说明
- [类型参数语法](https://peps.python.org/pep-0695/) - PEP 695 类型参数语法

#### Python 3.11
- [Python 3.11 文档](https://docs.python.org/3.11/) - Python 3.11 完整文档
- [Python 3.11 新特性](https://docs.python.org/3.11/whatsnew/3.11.html) - 3.11 版本新特性
- [Python 3.11 发布说明](https://www.python.org/downloads/release/python-3110/) - 3.11 发布说明
- [异常组和 except*](https://peps.python.org/pep-0654/) - PEP 654 异常组

### Python 标准库文档

- [Python 标准库参考](https://docs.python.org/3/library/index.html) - 标准库完整参考
- [Python 教程](https://docs.python.org/3/tutorial/index.html) - Python 官方教程
- [Python 语言参考](https://docs.python.org/3/reference/index.html) - 语言规范参考
- [Python 安装和配置](https://docs.python.org/3/using/index.html) - 安装配置指南

## 开发工具文档

### 包管理与项目管理

#### uv - 现代 Python 包管理器
- [uv 官方文档](https://docs.astral.sh/uv/) - 完整文档
- [uv 快速入门](https://docs.astral.sh/uv/getting-started/installation/) - 安装和快速开始
- [uv 命令参考](https://docs.astral.sh/uv/reference/cli/) - CLI 命令参考
- [uv 项目配置](https://docs.astral.sh/uv/concepts/projects/) - 项目配置概念
- [uv 依赖管理](https://docs.astral.sh/uv/concepts/dependencies/) - 依赖管理概念
- [uv 虚拟环境](https://docs.astral.sh/uv/concepts/virtualenvs/) - 虚拟环境管理
- [uv 工具管理](https://docs.astral.sh/uv/guides/tools/) - 工具管理指南
- [uv 与 pip 兼容性](https://docs.astral.sh/uv/guides/integration/pip/) - pip 兼容性

#### 其他包管理工具
| 工具 | 文档 | 说明 |
|------|------|------|
| [pip](https://pip.pypa.io/) | pip Documentation | Python 包安装工具 |
| [pip-tools](https://github.com/jazzband/pip-tools) | pip-tools Documentation | pip 依赖管理工具 |
| [setuptools](https://setuptools.pypa.io/) | setuptools Documentation | Python 包构建工具 |
| [build](https://pypa-build.readthedocs.io/) | build Documentation | PEP 517 构建前端 |
| [poetry](https://python-poetry.org/) | Poetry Documentation | 依赖管理和打包工具 |
| [conda](https://docs.conda.io/) | Conda Documentation | Anaconda 包管理器 |
| [PDM](https://pdm-project.org/) | PDM Documentation | PEP 582 项目管理器 |
| [hatch](https://hatch.pypa.io/) | Hatch Documentation | 现代项目管理工具 |

#### 项目配置
- [pyproject.toml 规范](https://packaging.python.org/en/latest/specifications/pyproject-toml/) - PEP 621 项目元数据规范
- [Setup.cfg 配置](https://setuptools.pypa.io/en/latest/userguide/declarative_config.html) - setuptools 配置文件

### 代码质量工具

#### Ruff - 快速的 Python Linter
- [Ruff 官方文档](https://docs.astral.sh/ruff/) - 完整文档
- [Ruff 规则列表](https://docs.astral.sh/ruff/rules/) - 所有可用规则
- [Ruff 配置](https://docs.astral.sh/ruff/settings/) - 配置选项
- [Ruff 与其他工具对比](https://docs.astral.sh/ruff/comparison/) - 与 Black、isort、flake8 等对比
- [Ruff 版本管理](https://docs.astral.sh/ruff/version/) - 版本兼容性

#### 其他代码质量工具
| 工具 | 文档 | 说明 |
|------|------|------|
| [Black](https://black.readthedocs.io/) | Code Formatter | 代码格式化工具 |
| [isort](https://pycqa.github.io/isort/) | Import Sorter | 导入排序工具 |
| [mypy](https://mypy.readthedocs.io/) | Static Type Checker | 静态类型检查工具 |
| [pylint](https://pylint.pycqa.org/) | Code Analysis | 代码分析工具 |
| [flake8](https://flake8.pycqa.org/) | Style Guide Enforcement | 风格指南执行工具 |
| [pyflakes](https://pypi.org/project/pyflakes/) | Simple Error Checker | 简单错误检查器 |
| [pydocstyle](https://www.pydocstyle.org/) | Docstring Checker | 文档字符串检查器 |
| [pyupgrade](https://github.com/asottile/pyupgrade) | Syntax Upgrader | Python 语法升级工具 |

### 静态类型检查

#### mypy - 静态类型检查器
- [mypy 官方文档](https://mypy.readthedocs.io/) - 完整文档
- [mypy 类型提示入门](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html) - 类型提示速查表
- [mypy 配置选项](https://mypy.readthedocs.io/en/stable/config_file.html) - mypy.ini 配置
- [mypy 类型存根](https://mypy.readthedocs.io/en/stable/stubs.html) - 类型存根创建
- [mypy 常见问题](https://mypy.readthedocs.io/en/stable/faq.html) - FAQ
- [typeshed](https://github.com/python/typeshed) - 第三方库类型存根

#### 其他类型检查工具
| 工具 | 文档 | 说明 |
|------|------|------|
| [pyright](https://github.com/microsoft/pyright) | Static Type Checker | Microsoft 的类型检查器 |
| [pyre](https://pyre-check.org/) | Static Type Checker | Facebook 的类型检查器 |
| [pytype](https://google.github.io/pytype/) | Static Type Checker | Google 的类型检查器 |
| [typeguard](https://typeguard.readthedocs.io/) | Runtime Type Checker | 运行时类型检查 |

### 测试框架

#### pytest - 测试框架
- [pytest 官方文档](https://docs.pytest.org/) - 完整文档
- [pytest 入门指南](https://docs.pytest.org/en/stable/getting-started.html) - 快速开始
- [pytest 使用指南](https://docs.pytest.org/en/stable/usage.html) - 使用方法和示例
- [pytest API 参考](https://docs.pytest.org/en/stable/reference.html) - API 参考
- [pytest 配置选项](https://docs.pytest.org/en/stable/reference.html#configuration-options) - pytest.ini 配置
- [pytest fixture](https://docs.pytest.org/en/stable/fixture.html) - Fixture 详解
- [pytest parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html) - 参数化测试
- [pytest 插件列表](https://docs.pytest.org/en/stable/reference/plugin_list.html) - 官方插件

#### pytest 插件
| 插件 | 文档 | 说明 |
|------|------|------|
| [pytest-cov](https://pytest-cov.readthedocs.io/) | Coverage Plugin | 覆盖率统计插件 |
| [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | AsyncIO Support | 异步测试支持 |
| [pytest-mock](https://pytest-mock.readthedocs.io/) | Mock Support | Mock 支持 |
| [pytest-xdist](https://pytest-xdist.readthedocs.io/) | Parallel Execution | 并行测试执行 |
| [pytest-timeout](https://github.com/pytest-dev/pytest-timeout) | Timeout Plugin | 超时控制 |
| [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) | Benchmark Plugin | 性能基准测试 |
| [pytest-django](https://pytest-django.readthedocs.io/) | Django Integration | Django 测试集成 |
| [pytest-flask](https://github.com/pytest-dev/pytest-flask) | Flask Integration | Flask 测试集成 |

#### 其他测试工具
| 工具 | 文档 | 说明 |
|------|------|------|
| [unittest](https://docs.python.org/3/library/unittest.html) | Unit Testing | Python 内置单元测试框架 |
| [doctest](https://docs.python.org/3/library/doctest.html) | Docstring Testing | 文档字符串测试 |
| [hypothesis](https://hypothesis.readthedocs.io/) | Property Testing | 属性测试框架 |
| [tox](https://tox.wiki/) | Test Automation | 测试自动化工具 |
| [nox](https://nox.thea.codes/) | Testing Tool | tox 的替代品 |

### 日志和监控工具

#### loguru - 现代日志库
- [loguru 官方文档](https://loguru.readthedocs.io/) - 完整文档
- [loguru 快速入门](https://loguru.readthedocs.io/en/stable/resources.html) - 快速开始
- [loguru API 参考](https://loguru.readthedocs.io/en/stable/api/logger.html) - API 参考
- [loguru 最佳实践](https://loguru.readthedocs.io/en/stable/resources.html#best-practices) - 最佳实践

#### 其他日志工具
| 工具 | 文档 | 说明 |
|------|------|------|
| [logging](https://docs.python.org/3/library/logging.html) | Standard Library | Python 内置日志库 |
| [structlog](https://www.structlog.org/) | Structured Logging | 结构化日志库 |
| [rich](https://rich.readthedocs.io/) | Console Formatting | 终端格式化输出 |

### 性能分析工具

| 工具 | 文档 | 说明 |
|------|------|------|
| [cProfile](https://docs.python.org/3/library/profile.html#module-cProfile) | CPU Profiler | CPU 性能分析工具 |
| [memory_profiler](https://github.com/pythonprofilers/memory_profiler) | Memory Profiler | 内存性能分析工具 |
| [timeit](https://docs.python.org/3/library/timeit.html) | Timing | 代码执行时间测量工具 |
| [tracemalloc](https://docs.python.org/3/library/tracemalloc.html) | Memory Tracking | 内存分配追踪工具 |
| [py-spy](https://github.com/benfred/py-spy) | Sampling Profiler | 采样性能分析工具 |
| [pyinstrument](https://pyinstrument.readthedocs.io/) | Profiler | Python 性能分析器 |
| [scalene](https://github.com/plasma-umass/scalene) | Profiler | CPU 和内存分析器 |

### 调试工具

| 工具 | 文档 | 说明 |
|------|------|------|
| [pdb](https://docs.python.org/3/library/pdb.html) | Python Debugger | Python 内置调试器 |
| [ipdb](https://pypi.org/project/ipdb/) | IPython Debugger | IPython 调试器 |
| [pdb++](https://pypi.org/project/pdbpp/) | Enhanced PDB | 增强的 pdb |
| [pudb](https://documen.tician.de/pudb/) | Console Debugger | 终端可视化调试器 |

## Web 框架文档

### FastAPI
- [FastAPI 官方文档](https://fastapi.tiangolo.com/) - 完整文档
- [FastAPI 用户指南](https://fastapi.tiangolo.com/tutorial/) - 用户教程
- [FastAPI 高级用户指南](https://fastapi.tiangolo.com/advanced/) - 高级特性
- [FastAPI 项目生成](https://fastapi.tiangolo.com/project-generation/) - 项目模板
- [FastAPI 性能](https://fastapi.tiangolo.com/benchmarks/) - 性能基准
- [FastAPI 贡献指南](https://fastapi.tiangolo.com/contribute/) - 如何贡献

### 其他 Web 框架
| 框架 | 文档 | 说明 |
|------|------|------|
| [Django](https://docs.djangoproject.com/) | Web Framework | Django Web 框架 |
| [Flask](https://flask.palletsprojects.com/) | Lightweight Web Framework | 轻量级 Web 框架 |
| [Tornado](https://www.tornadoweb.org/) | Async Web Framework | 异步 Web 框架 |
| [Sanic](https://sanic.readthedocs.io/) | Async Web Framework | 高性能异步框架 |
| [Starlette](https://www.starlette.io/) | ASGI Framework | 轻量级 ASGI 框架 |

## 数据验证和序列化

### Pydantic
- [Pydantic 官方文档](https://docs.pydantic.dev/) - 完整文档
- [Pydantic V2 迁移指南](https://docs.pydantic.dev/latest/migration/) - V1 到 V2 迁移
- [Pydantic 模型](https://docs.pydantic.dev/latest/concepts/models/) - 模型定义
- [Pydantic 类型](https://docs.pydantic.dev/latest/api/types/) - 内置类型
- [Pydantic 验证器](https://docs.pydantic.dev/latest/concepts/validators/) - 自定义验证器
- [Pydantic 设置](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - 配置管理
- [Pydantic JSON](https://docs.pydantic.dev/latest/api/json_schema/) - JSON Schema 生成

### 其他数据验证库
| 库 | 文档 | 说明 |
|------|------|------|
| [Marshmallow](https://marshmallow.readthedocs.io/) | Object Serialization | 对象序列化库 |
| [Cerberus](https://docs.python-cerberus.org/) | Data Validation | 轻量级数据验证库 |
| [attrs](https://www.attrs.org/) | Class Decoration | 简化类定义 |

## 数据处理库

### pandas
- [pandas 官方文档](https://pandas.pydata.org/) - 完整文档
- [pandas 入门指南](https://pandas.pydata.org/docs/getting_started/intro_tutorials/) - 入门教程
- [pandas 用户指南](https://pandas.pydata.org/docs/user_guide/index.html) - 用户指南
- [pandas API 参考](https://pandas.pydata.org/docs/reference/index.html) - API 参考
- [pandas DataFrame](https://pandas.pydata.org/docs/reference/frame.html) - DataFrame 详解
- [pandas Series](https://pandas.pydata.org/docs/reference/series.html) - Series 详解
- [pandas 时间序列](https://pandas.pydata.org/docs/user_guide/timeseries.html) - 时间序列处理
- [pandas 性能优化](https://pandas.pydata.org/docs/user_guide/enhancingperf.html) - 性能增强

### 其他数据处理库
| 库 | 文档 | 说明 |
|------|------|------|
| [NumPy](https://numpy.org/doc/) | Numerical Computing | 数值计算库 |
| [Polars](https://docs.pola-rs.com/) | DataFrame Library | 高性能数据框库 |
| [Vaex](https://vaex.io/) | Out-of-Core DataFrame | 超大数据集处理 |

## 异步编程库

| 库 | 文档 | 说明 |
|------|------|------|
| [asyncio](https://docs.python.org/3/library/asyncio.html) | Async I/O | Python 异步 I/O 库 |
| [aiohttp](https://docs.aiohttp.org/) | Async HTTP Client | 异步 HTTP 客户端 |
| [httpx](https://www.python-httpx.org/) | Async HTTP Client | 现代 HTTP 客户端 |
| [asyncpg](https://magicstack.github.io/asyncpg/) | Async PostgreSQL | 异步 PostgreSQL 驱动 |
| [motor](https://motor.readthedocs.io/) | Async MongoDB | 异步 MongoDB 驱动 |

## 安全工具

### Safety - 依赖安全检查
- [safety 官方文档](https://pyup.io/safety/) - 完整文档
- [safety CLI 参考](https://pyup.io/safety/docs/) - 命令行参考
- [safety 配置](https://pyup.io/safety/docs/configuration/) - 配置选项
- [safety GitHub Action](https://github.com/pyupio/safety-action) - GitHub 集成

### pip-audit - 依赖审计工具
- [pip-audit 官方文档](https://pypa.github.io/pip-audit/) - 完整文档
- [pip-audit 使用指南](https://pypa.github.io/pip-audit/using/) - 使用方法
- [pip-audit 配置](https://pypa.github.io/pip-audit/configuration/) - 配置选项

### Bandit - 代码安全扫描
- [bandit 官方文档](https://bandit.readthedocs.io/) - 完整文档
- [bandit 使用指南](https://bandit.readthedocs.io/en/latest/index.html) - 使用方法
- [bandit 插件](https://bandit.readthedocs.io/en/latest/plugins/index.html) - 内置插件
- [bandit 配置](https://bandit.readthedocs.io/en/latest/config.html) - 配置文件

### 其他安全工具
| 工具 | 文档 | 说明 |
|------|------|------|
| [semgrep](https://semgrep.dev/) | Static Analysis | 静态代码分析 |
| [snyk](https://snyk.io/) | Vulnerability Scanner | 漏洞扫描器 |
| [trivy](https://aquasecurity.github.io/trivy/) | Security Scanner | 安全扫描器 |
| [pytest-cov](https://pytest-cov.readthedocs.io/) | Coverage | 代码覆盖率 |

## 最佳实践指南

### 设计模式
- [Design Patterns in Python](https://refactoring.guru/design-patterns/python) - 设计模式 Python 实现
- [Python Design Patterns](https://github.com/faif/python-patterns) - Python 设计模式集合
- [Refactoring.guru](https://refactoring.guru/) - 重构和设计模式

### 性能优化
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed) - Python 性能优化技巧
- [Profiling Python Code](https://docs.python.org/3/library/profile.html) - Python 性能分析指南
- [py-performance](https://github.com/python/pyperformance) - Python 性能基准

### 安全最佳实践
- [OWASP Python Security](https://owasp.org/www-community/Source_code_analysis_tools) - OWASP Python 安全指南
- [Python Security Best Practices](https://realpython.com/python-security/) - Python 安全最佳实践
- [Python Security Documentation](https://docs.python.org/3/library/security_warnings.html) - 安全警告文档

## 学习资源

### 书籍

| 书名 | 作者 | 说明 |
|------|------|------|
| **Fluent Python (第2版)** | Luciano Ramalho | Python 高级特性深入讲解（涵盖 Python 3.10+） |
| **Effective Python (第2版)** | Brett Slatkin | Python 编程的 90 个有效建议 |
| **Clean Code in Python** | Mariano Anaya | Python 代码整洁之道 |
| **High Performance Python** | Micha Gorelick, Ian Ozsvald | Python 性能优化指南 |
| **Python Cookbook (第3版)** | David Beazley, Brian K. Jones | Python 实用技巧集锦 |
| **Architecture Patterns with Python** | Harry Percival, Bob Gregory | Python 架构模式 |
| **Practice Makes Progress** | Dan Bader | Python 实践练习 |
| **Python Tricks** | Dan Bader | Python 技巧集 |

### 在线课程

| 平台 | 课程 | 说明 |
|------|------|------|
| [RealPython](https://realpython.com/) | Complete Python Masterclass | Python 学习平台 |
| [DataCamp](https://www.datacamp.com/) | Data Science with Python | 数据科学和 Python 课程 |
| [Coursera](https://www.coursera.org/) | Python for Everybody | 大学级别 Python 课程 |
| [edX](https://www.edx.org/) | Introduction to Python | MIT 免费课程 |
| [Udemy](https://www.udemy.com/) | 2024 Complete Python Bootcamp | 热门 Python 课程 |
| [Pluralsight](https://www.pluralsight.com/) | Python Path | 技术技能平台 |

### 社区资源

| 资源 | 链接 | 说明 |
|------|------|------|
| Python Discourse | [discuss.python.org](https://discuss.python.org/) | Python 官方讨论社区 |
| Stack Overflow | [stackoverflow.com/python](https://stackoverflow.com/questions/tagged/python) | Python 问题解答 |
| Python Reddit | [reddit.com/r/Python](https://www.reddit.com/r/Python/) | Python 子版块 |
| GitHub Python | [github.com/python](https://github.com/search?q=language:Python) | 优秀的开源项目 |
| PyPI | [pypi.org](https://pypi.org/) | Python 包索引 |

### 教程网站

| 网站 | 链接 | 说明 |
|------|------|------|
| Python Module of the Week | [pymotw.com](https://pymotw.com/) | Python 模块每周介绍 |
| Real Python Tutorials | [realpython.com](https://realpython.com/) - Real Python 教程合集 |
| Full Stack Python | [fullstackpython.com](https://www.fullstackpython.com/) - Web 开发完整指南 |
| Awesome Python | [github.com/vinta/awesome-python](https://github.com/vinta/awesome-python) - 精选 Python 资源列表 |
| Python Weekly | [pythonweekly.com](https://pythonweekly.com/) - Python 每周资讯 |

## 版本信息

### Python 版本时间线

| 版本 | 发布日期 | 支持状态 | 主要特性 |
|------|---------|---------|---------|
| 3.9 | 2020-10-05 | 安全维护（2025-10） | 字典合并运算符、类型提示改进 |
| 3.10 | 2021-10-04 | 安全维护（2026-10） | match/case、联合类型语法 |
| 3.11 | 2022-10-24 | 安全维护（2027-10） | 异常组、性能提升 60% |
| 3.12 | 2023-10-02 | 安全维护（2028-10） | 类型参数语法、f-string 改进 |
| 3.13 | 2024-10-07 | 完整维护（2029-10） | 可选 GIL、REPL 改进、实验性 JIT |
| 3.14 | 预计 2025-10 | - | 进一步 GIL 移除 |

### Python 版本发布日历

- [Python 版本发布时间线](https://devguide.python.org/versions/) - 官方版本发布计划
- [Python 生命周期](https://www.python.org/downloads/) - 各版本支持状态
- [PEP 602 - Annual Release Cycle](https://peps.python.org/pep-0602/) - 年度发布周期规范

## 相关链接

### 包索引
- [PyPI](https://pypi.org/) - Python Package Index
- [Test PyPI](https://test.pypi.org/) - PyPI 测试环境
- [conda-forge](https://conda-forge.org/) - Conda 包仓库

### IDE 和编辑器
- [VS Code Python](https://code.visualstudio.com/docs/python/python-tutorial) - VS Code Python 支持
- [PyCharm](https://www.jetbrains.com/pycharm/) - JetBrains Python IDE
- [JupyterLab](https://jupyterlab.readthedocs.io/) - JupyterLab 文档

### 持续集成
- [GitHub Actions Python](https://github.com/actions/setup-python) - GitHub Actions Python 配置
- [tox-gh-actions](https://github.com/ymyzk/tox-gh-actions) - tox 与 GitHub Actions 集成

---

**最后更新**：2026-02-09
