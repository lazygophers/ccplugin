# SKEIN 集成测试环境 (docker-compose)

单容器跑**真实生产形态**：`skein serve` app（uvicorn + 入库 dist 前端），从宿主机打真 HTTP/WS/浏览器。

> 不走 `skein serve` CLI 入口 —— 它绑 `127.0.0.1` 随机端口（boardsource `_run_server`），容器外不可达；容器直接用 uvicorn factory `skeinlib.web.serve:_serve_app_factory` 绑 `0.0.0.0:8841`。

## 用法

```bash
make integration-test     # 一键: 起容器 → 装测试依赖 → pytest → 关容器
make integration-up       # 只起环境 (手动调试, 浏览器开 http://127.0.0.1:8841)
make integration-down     # 关环境 (清卷)
```

## 覆盖

| 文件 | 层 | 场景 |
|---|---|---|
| test_api_lifecycle.py | HTTP | task 全生命周期 (create→spec→design→subtask→confirm→check→finish)；confirm 硬门拒绝；design-save 路径穿越/404 守门；config hooks 拒写 (RCE 守门)；软删→回收站→清空；exec 白名单参数校验 |
| test_ws.py | WebSocket | 数据落盘 → watchfiles → `/__skein__/live` 推 task-changed（API 写 + design-save 两路） |
| test_ui_playwright.py | 浏览器 | 看板渲染；PRD 三段固定渲染（空 task 也亮卡）；PRD 编辑保存落盘；sid 点击复制 `tid sid` |

## 结构

- `Dockerfile` — python:3.12-slim + git，COPY scripts/ + assets/dist/（无 Node，不会触发前端重编译），预置 git 仓 + `skein init` 工作区
- `docker-compose.yml` — 端口 `127.0.0.1:8841`，匿名卷隔离每次运行，healthcheck 打 `/__skein__/id`
- `run.sh` — 起停编排 + 宿主 venv（pytest/httpx/websockets/playwright）
- `tests/` — pytest 套件；`conftest.py` 不管理容器生命周期，容器已在跑即可单独 `pytest`
