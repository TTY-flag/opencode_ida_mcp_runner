FROM smanx/opencode:latest

ARG UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG IDA_DIR=/opt/ida-pro-9.1
ARG IDA_MCP_HOME=/opt/ida-headless-mcp

ENV DEBIAN_FRONTEND=noninteractive     IDADIR=${IDA_DIR}     IDA_MCP_HOME=${IDA_MCP_HOME}     QT_QPA_PLATFORM=offscreen     OPENCODE_HOSTNAME=0.0.0.0     OPENCODE_HOST=0.0.0.0     OPENCODE_PORT=4096

RUN apt-get update     && apt-get install -y --no-install-recommends         ca-certificates         curl         git         libdbus-1-3         libfontconfig1         libfreetype6         libgl1         libglib2.0-0         libsm6         libx11-6         libxext6         libxrender1         libxkbcommon-x11-0         libxcb1         libxcb-xinerama0         xz-utils     && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh -o /tmp/uv-install.sh     && UV_INSTALL_DIR=/usr/local/bin sh /tmp/uv-install.sh     && rm -f /tmp/uv-install.sh     && uv python install 3.11

COPY image/ida-headless-mcp/ ${IDA_MCP_HOME}/
COPY image/ida-pro-9.1/ ${IDA_DIR}/
COPY image/idapro-user/ /opt/idapro-user/
COPY image/opencode/opencode.json /opt/opencode-ida/opencode.json
COPY image/opencode/entrypoint.sh /usr/local/bin/opencode-ida-entrypoint
COPY image/bin/idalib-pool-opencode /usr/local/bin/idalib-pool-opencode

RUN chmod +x /usr/local/bin/opencode-ida-entrypoint /usr/local/bin/idalib-pool-opencode     && if [ ! -f ${IDA_DIR}/ida ] || [ ! -f ${IDA_DIR}/libidalib.so ]; then echo "Missing IDA Pro files. Put IDA Pro 9.1 into image/ida-pro-9.1 before building." >&2; exit 1; fi     && if [ ! -f /opt/idapro-user/ida.reg ]; then echo "Warning: image/idapro-user/ida.reg is missing; IDA may fail in headless mode until the license/user config is accepted." >&2; fi     && mkdir -p /root/.idapro /root/.config/opencode /workspace     && if [ -d /opt/idapro-user ]; then cp -a /opt/idapro-user/. /root/.idapro/; fi     && cd ${IDA_MCP_HOME}     && uv venv --python 3.11 .venv     && UV_INDEX_URL=${UV_INDEX_URL} uv pip install -e .     && ${IDA_MCP_HOME}/.venv/bin/python ${IDA_DIR}/idalib/python/py-activate-idalib.py -d ${IDA_DIR}     && cp /opt/opencode-ida/opencode.json /root/.config/opencode/opencode.json     && chmod -R a+rX ${IDA_DIR} ${IDA_MCP_HOME} /opt/opencode-ida /root/.idapro

WORKDIR /workspace
EXPOSE 4096
ENTRYPOINT ["/usr/local/bin/opencode-ida-entrypoint"]
