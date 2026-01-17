# Docker 测试文件 - 包含多阶段构建、优化、安全

# 阶段 1: 构建阶段
FROM ubuntu:22.04 AS builder

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV CMAKE_VERSION=3.25.1
ENV PYTHON_VERSION=3.11

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake=${CMAKE_VERSION}* \
    git \
    wget \
    curl \
    libssl-dev \
    libpthread-stubs0-dev \
    python3=${PYTHON_VERSION}* \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /build

# 复制依赖文件
COPY requirements.txt .
COPY pyproject.toml .

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir uv
RUN uv sync

# 复制源代码
COPY src/ ./src/
COPY include/ ./include/
COPY tests/ ./tests/
COPY CMakeLists.txt .

# 构建应用
RUN mkdir build && cd build && \
    cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_TESTS=ON && \
    make -j$(nproc)

# 运行测试
RUN cd build && ctest --output-on-failure

# 阶段 2: 运行阶段
FROM ubuntu:22.04

# 设置标签
LABEL maintainer="your-email@example.com"
LABEL version="1.0.0"
LABEL description="Semantic Search Application"

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    libssl3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制二进制文件
COPY --from=builder /build/build/bin/semantic_search /app/semantic_search
COPY --from=builder /build/build/lib/ /app/lib/

# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/config && \
    chown -R appuser:appuser /app

# 复制配置文件
COPY config/ /app/config/

# 设置环境变量
ENV PATH="/app:$PATH"
ENV LD_LIBRARY_PATH="/app/lib:$LD_LIBRARY_PATH"
ENV PYTHONUNBUFFERED=1

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD semantic_search --health || exit 1

# 入口点
ENTRYPOINT ["/app/semantic_search"]

# 默认参数
CMD ["--config", "/app/config/config.json", "--port", "8080"]
