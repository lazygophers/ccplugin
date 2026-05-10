# cortex 测试套件

> stdlib-only (Python `unittest` + 纯 bash 自带断言库) 的本地单测/集成测试。

## 运行

```bash
# 全部测试 (python + bash)
bash plugins/tools/cortex/tests/run.sh

# 只跑 python
bash plugins/tools/cortex/tests/run.sh python

# 只跑 bash
bash plugins/tools/cortex/tests/run.sh bash

# 加 coverage 报告 (需先 pip install coverage)
bash plugins/tools/cortex/tests/run.sh --coverage
```

退出码: 0 全过, 1 有任一失败。

## 目录

```
tests/
├── run.sh                 # 入口 (python + bash 串跑)
├── README.md              # 本文件
├── python/
│   ├── _helpers.py        # vault fixture / 路径加载
│   ├── test_cortex_locale.py    # 28 cases
│   ├── test_save_session.py     # 25 cases (含 CLI 集成)
│   ├── test_backlink_sync.py    # 18 cases
│   ├── test_lint_run.py         # 19 cases (15 lint rules + autofix)
│   └── test_refactor.py         # 20 cases (rename/merge/split/fold/migrate_locale + _common)
└── bash/
    ├── _assert.sh         # bash 断言库
    ├── test_resolve_vault.sh    # 6 cases
    ├── test_session_start.sh    # 4 cases
    ├── test_stop_hooks.sh       # 7 cases (stop + post_compact)
    ├── test_install_cron.sh     # 5 cases
    └── test_cron_run.sh         # 10 cases (run.sh + lint/fold/dashboard 子脚本)
```

## 设计原则

- **stdlib only**: python 不引第三方; bash 不依赖 bats/shunit
- **沙箱化**: 全部用 `tempfile.TemporaryDirectory` / `mktemp -d`, 不污染用户 vault
- **可重复**: 不依赖系统时间、网络、用户 home
- **fake CLI**: cron 测试通过 `PATH` 注入 fake `claude` / `timeout`

## 已知限制

- 部分 bash 测试用 `env -i` 隔离环境变量, 防 macOS 默认 vault `~/persons/knowledge/obsidian` 干扰。
- `flock` 在 macOS 默认缺失, run.sh 走 PID 锁分支; 测试覆盖该分支。
- `timeout` 在 macOS 默认缺失, cron 测试注入 fake `timeout` (等价 passthrough)。
- 集成测试调用 `python3 script.py` 子进程, 不参与 coverage (除非用 `coverage run`)。
