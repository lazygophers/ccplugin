# SKEIN 集成测试镜像 — 单容器跑真实生产形态: skein serve app (uvicorn + 入库 dist 前端)。
# 不走 `skein serve` CLI 入口: 它绑 127.0.0.1 随机端口 (boardsource._run_server), 容器外不可达;
# 直接 uvicorn factory (skeinlib/web/serve.py:_serve_app_factory) 绑 0.0.0.0:8841。
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
# pypi 直连超时, 走清华镜像 (容器内网络受限环境的常态)
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 只带运行所需: CLI 脚本 + 前端构建产物 (无 Node, 不会触发自动重编译)
COPY scripts/ /app/scripts/
COPY assets/dist/ /app/assets/dist/

ENV PYTHONPATH=/app/scripts \
    SKEIN_NO_AUTOBUILD=1

# 预置空工作区: git 仓 (confirm 建 worktree / finish 合并要用) + .skein 初始化
RUN mkdir /workspace && cd /workspace \
    && git init -q \
    && git config user.email itest@skein.local \
    && git config user.name itest \
    && git commit -q --allow-empty -m init \
    && python /app/scripts/skein.py init

WORKDIR /workspace
EXPOSE 8841
CMD ["python", "-m", "uvicorn", "skeinlib.web.serve:_serve_app_factory", \
     "--factory", "--host", "0.0.0.0", "--port", "8841", "--log-level", "warning"]
