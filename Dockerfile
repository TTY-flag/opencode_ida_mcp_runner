# 使用预置 opencode 的基础镜像。
FROM smanx/opencode:latest

# 配置构建参数和容器内关键目录。
ARG UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG IDA_DIR=/opt/ida-pro-9.1
ARG IDA_MCP_HOME=/opt/ida-headless-mcp

# 设置 IDA、MCP、opencode Web 和 headless Qt 的默认运行环境。
ENV DEBIAN_FRONTEND=noninteractive \
    IDADIR=${IDA_DIR} \
    IDA_MCP_HOME=${IDA_MCP_HOME} \
    IDA_MCP_MAX_INSTANCES=5 \
    QT_QPA_PLATFORM=offscreen \
    OPENCODE_HOSTNAME=0.0.0.0 \
    OPENCODE_PORT=4096

# 安装 IDA/headless Qt 运行所需的系统依赖。
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        libdbus-1-3 \
        libfontconfig1 \
        libfreetype6 \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libxkbcommon-x11-0 \
        libxcb1 \
        libxcb-xinerama0 \
        xz-utils \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv 和 Python 3.11，用于创建 ida-headless-mcp 虚拟环境。
RUN curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh \
    && UV_INSTALL_DIR=/usr/local/bin sh /tmp/uv-install.sh \
    && rm -f /tmp/uv-install.sh \
    && uv python install 3.11

# 复制 IDA、MCP、opencode 配置和启动脚本到镜像内。
COPY image/ida-headless-mcp/ ${IDA_MCP_HOME}/
COPY image/ida-pro-9.1/ ${IDA_DIR}/
COPY image/idapro-user/ /opt/idapro-user/
COPY image/opencode/opencode.json /opt/opencode-ida/opencode.json
COPY --chmod=0755 image/opencode/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY --chmod=0755 image/bin/idalib-pool-opencode /usr/local/bin/idalib-pool-opencode

# 校验 IDA 文件，安装 MCP 包，并激活 idalib。
RUN if [ ! -f "${IDA_DIR}/ida" ] || [ ! -f "${IDA_DIR}/libidalib.so" ]; then \
        echo "Missing IDA Pro files under ${IDA_DIR}." >&2; \
        exit 1; \
    fi \
    && mkdir -p /root/.idapro /workspace \
    && cp -a /opt/idapro-user/. /root/.idapro/ \
    && cd ${IDA_MCP_HOME} \
    && uv venv --python 3.11 .venv \
    && UV_INDEX_URL=${UV_INDEX_URL} uv pip install -e . \
    && ${IDA_MCP_HOME}/.venv/bin/python ${IDA_DIR}/idalib/python/py-activate-idalib.py -d ${IDA_DIR} \
    && chmod -R a+rX ${IDA_DIR} ${IDA_MCP_HOME} /opt/opencode-ida /root/.idapro

# 默认在持久化工作目录中启动 opencode Web。
WORKDIR /workspace
EXPOSE 4096
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
