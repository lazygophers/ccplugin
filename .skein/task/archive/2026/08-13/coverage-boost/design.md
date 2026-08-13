# 测试覆盖率提升到95% — 详细设计

## 现状
- 732 tests, 100% pass
- 总覆盖率 73% (1689 miss / 6235 stmts) → 目标 95% (≤312 miss)
- 子进程 coverage 已修复（路径归一 + omit copy 路径）

## 分组策略 (4 个并行 subtask)

### cov-web (serve 304 + views 208 + boardsource 131 = 643 miss)
- 已有: test_cov_web_serve.py, test_serve_routes.py, test_board.py
- 补法: 进程内 TestClient + _FakeBoard 打未覆盖路由；views 函数直接调用
- 关键未覆盖: serve.py lifespan/watch_loop/前端重建/reindex 路径；views.py 渲染函数；boardsource.py git 操作

### cov-core (scheduling 107 + doctor 83 + lifecycle 52 + workspace 24 + artifacts 18 + query 12 + admin 9 = 305 miss)
- 已有: test_cov_core_sched.py, test_cov_doctor.py
- 补法: 进程内 import mixin，mock subprocess/git

### cov-spec (maintain 74 + write 65 + analyze 17 + map 15 + index 15 + model 13 = 199 miss)
- 已有: test_cov_spec.py, test_spec.py
- 补法: 进程内 import WriteMixin/MaintainMixin；CLI subprocess 补命令

### cov-misc (hooks + utils + task + cli = 542 miss)
- 已有: test_cov_utils_hooks.py
- 补法: hooks 进程内函数调用；exec_policy 全白名单分支；task 模块各方法

## 测试接缝 (seam)
三条接缝覆盖全部新增测试:
1. **进程内 TestClient + mock board** (web 模块): FastAPI TestClient 不开 socket，_FakeBoard 提供 duck-type DataSource；monkeypatch serve.subprocess.run 拦子进程
2. **进程内 import mixin/函数直接调用** (core/spec/task/utils/hooks): 直接 import skeinlib 模块，构造对象或调纯函数，monkeypatch 依赖
3. **CLI subprocess** (spec/cli, cli/main): 已有 run_skein/run_spec wrapper，补未跑的命令分支
