# Python 开发参考资源

## 官方标准和文档

### Python Enhancement Proposals (PEPs)

| PEP | 标题 | 说明 |
|-----|------|------|
| [PEP 8](https://www.python.org/dev/peps/pep-0008/) | Style Guide for Python Code | Python 代码风格指南 |
| [PEP 20](https://www.python.org/dev/peps/pep-0020/) | The Zen of Python | Python 的哲学原则 |
| [PEP 257](https://www.python.org/dev/peps/pep-0257/) | Docstring Conventions | 文档字符串约定 |
| [PEP 484](https://www.python.org/dev/peps/pep-0484/) | Type Hints | 类型提示规范 |
| [PEP 517](https://www.python.org/dev/peps/pep-0517/) | A build-system independent format | 构建系统独立格式 |
| [PEP 518](https://www.python.org/dev/peps/pep-0518/) | Specifying build system requirements | 构建系统需求规范 |
| [PEP 621](https://www.python.org/dev/peps/pep-0621/) | Storing project metadata in pyproject.toml | 项目元数据存储 |

### 官方文档

- [Python 官方文档](https://docs.python.org/3/) - Python 语言和标准库完整文档
- [Python Tutorial](https://docs.python.org/3/tutorial/) - Python 官方教程
- [Library Reference](https://docs.python.org/3/library/) - 标准库参考

## 开发工具文档

### 包管理与项目管理

| 工具 | 文档 | 说明 |
|------|------|------|
| [uv](https://docs.astral.sh/uv/) | uv Documentation | 快速的 Python 包管理工具 |
| [pip](https://pip.pypa.io/) | pip Documentation | Python 包安装工具 |
| [setuptools](https://setuptools.pypa.io/) | setuptools Documentation | Python 包构建工具 |
| [pyproject.toml](https://packaging.python.org/en/latest/specifications/pyproject-toml/) | PEP 621 Specification | 项目配置文件规范 |

### 代码质量工具

| 工具 | 文档 | 说明 |
|------|------|------|
| [Black](https://black.readthedocs.io/) | Code Formatter | 代码格式化工具 |
| [Ruff](https://docs.astral.sh/ruff/) | Fast Python Linter | 快速的 Python 代码检查工具 |
| [mypy](https://mypy.readthedocs.io/) | Static Type Checker | 静态类型检查工具 |
| [pylint](https://pylint.pycqa.org/) | Code Analysis | 代码分析工具 |
| [flake8](https://flake8.pycqa.org/) | Style Guide Enforcement | 风格指南执行工具 |

### 测试框架

| 工具 | 文档 | 说明 |
|------|------|------|
| [pytest](https://docs.pytest.org/) | Testing Framework | Python 测试框架 |
| [unittest](https://docs.python.org/3/library/unittest.html) | Unit Testing | Python 内置单元测试框架 |
| [pytest-cov](https://pytest-cov.readthedocs.io/) | Coverage Plugin | 覆盖率统计插件 |
| [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) | AsyncIO Support | 异步测试支持 |
| [pytest-mock](https://pytest-mock.readthedocs.io/) | Mock Support | Mock 支持 |

### 性能分析工具

| 工具 | 文档 | 说明 |
|------|------|------|
| [cProfile](https://docs.python.org/3/library/profile.html#module-cProfile) | CPU Profiler | CPU 性能分析工具 |
| [memory_profiler](https://github.com/pythonprofilers/memory_profiler) | Memory Profiler | 内存性能分析工具 |
| [timeit](https://docs.python.org/3/library/timeit.html) | Timing | 代码执行时间测量工具 |
| [tracemalloc](https://docs.python.org/3/library/tracemalloc.html) | Memory Tracking | 内存分配追踪工具 |
| [py-spy](https://github.com/benfred/py-spy) | Sampling Profiler | 采样性能分析工具 |

### 调试工具

| 工具 | 文档 | 说明 |
|------|------|------|
| [pdb](https://docs.python.org/3/library/pdb.html) | Python Debugger | Python 内置调试器 |
| [logging](https://docs.python.org/3/library/logging.html) | Logging | 日志记录工具 |
| [traceback](https://docs.python.org/3/library/traceback.html) | Traceback | 异常追踪工具 |
| [structlog](https://www.structlog.org/) | Structured Logging | 结构化日志库 |

## 常用库

### 数据处理

| 库 | 文档 | 说明 |
|---|------|------|
| [NumPy](https://numpy.org/doc/) | Numerical Computing | 数值计算库 |
| [pandas](https://pandas.pydata.org/) | Data Analysis | 数据分析库 |
| [Polars](https://docs.pola-rs.com/) | DataFrame Library | 高性能数据框库 |

### Web 框架

| 库 | 文档 | 说明 |
|---|------|------|
| [FastAPI](https://fastapi.tiangolo.com/) | Modern Web Framework | 现代 Web 框架 |
| [Django](https://docs.djangoproject.com/) | Web Framework | Django Web 框架 |
| [Flask](https://flask.palletsprojects.com/) | Lightweight Web Framework | 轻量级 Web 框架 |

### 异步编程

| 库 | 文档 | 说明 |
|---|------|------|
| [asyncio](https://docs.python.org/3/library/asyncio.html) | Async I/O | Python 异步 I/O 库 |
| [aiohttp](https://docs.aiohttp.org/) | Async HTTP Client | 异步 HTTP 客户端 |
| [httpx](https://www.python-httpx.org/) | Async HTTP Client | 现代 HTTP 客户端 |

### 数据验证

| 库 | 文档 | 说明 |
|---|------|------|
| [pydantic](https://docs.pydantic.dev/) | Data Validation | 数据验证和设置管理 |
| [Marshmallow](https://marshmallow.readthedocs.io/) | Object Serialization | 对象序列化库 |
| [Cerberus](https://docs.python-cerberus.org/) | Data Validation | 轻量级数据验证库 |

## 最佳实践指南

### 设计模式

- [Design Patterns in Python](https://refactoring.guru/design-patterns/python) - 设计模式 Python 实现
- [Python Design Patterns](https://github.com/faif/python-patterns) - Python 设计模式集合

### 性能优化

- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed) - Python 性能优化技巧
- [Profiling](https://docs.python.org/3/library/profile.html) - Python 性能分析指南

### 安全最佳实践

- [OWASP Python Security](https://owasp.org/www-community/Source_code_analysis_tools) - OWASP Python 安全指南
- [Python Security Best Practices](https://realpython.com/python-security/) - Python 安全最佳实践

## 学习资源

### 书籍

- **Fluent Python** - Python 高级特性深入讲解
- **Effective Python** - Python 编程的 90 个有效建议
- **Clean Code in Python** - Python 代码整洁之道
- **High Performance Python** - Python 性能优化指南

### 在线课程

- [RealPython](https://realpython.com/) - Python 学习平台
- [DataCamp](https://www.datacamp.com/) - 数据科学和 Python 课程
- [Coursera Python](https://www.coursera.org/) - 大学级别 Python 课程

### 社区资源

- [Python Discourse](https://discuss.python.org/) - Python 官方讨论社区
- [Stack Overflow](https://stackoverflow.com/questions/tagged/python) - Python 问题解答
- [GitHub Python Repositories](https://github.com/search?q=language:Python) - 优秀的开源项目

## 版本信息

### Python 版本时间线

| 版本 | 发布日期 | 支持状态 |
|------|---------|--------|
| 3.8 | 2019-10-14 | 维护期（2024-10） |
| 3.9 | 2020-10-05 | 维护期（2025-10） |
| 3.10 | 2021-10-04 | 维护期（2026-10） |
| 3.11 | 2022-10-24 | 维护期（2027-10） |
| 3.12 | 2023-10-02 | 维护期（2028-10） |
| 3.13 | 2024-10-07 | 维护期（2029-10） |

更多版本信息见 [PEP 619](https://www.python.org/dev/peps/pep-0619/)

## 相关链接

### 包索引

- [PyPI](https://pypi.org/) - Python Package Index
- [Test PyPI](https://test.pypi.org/) - PyPI 测试环境

### 工具链

- [pip-tools](https://github.com/jazzband/pip-tools) - pip 依赖管理工具
- [poetry](https://python-poetry.org/) - 依赖管理和打包工具
- [conda](https://docs.conda.io/) - Anaconda 包管理器

### 其他资源

- [Python Module of the Week](https://pymotw.com/) - Python 模块每周介绍
- [Real Python Tutorials](https://realpython.com/) - Real Python 教程合集
- [Full Stack Python](https://www.fullstackpython.com/) - Web 开发完整指南

---

**最后更新**：2026-01-10
