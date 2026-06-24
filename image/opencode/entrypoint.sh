#!/usr/bin/env bash
set -euo pipefail

# 初始化 IDA、MCP 和 Qt 运行环境。
export IDADIR="${IDADIR:-/opt/ida-pro-9.1}"
export IDA_MCP_HOME="${IDA_MCP_HOME:-/opt/ida-headless-mcp}"
export LD_LIBRARY_PATH="$IDADIR:$IDADIR/plugins:${LD_LIBRARY_PATH:-}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"

# 每次启动都重置 opencode 状态，并写入仓库内置 MCP 配置。
rm -rf /root/.config/opencode /root/.local/share/opencode /root/.cache/opencode
mkdir -p /root/.config/opencode /root/.local/share/opencode /workspace
cp /opt/opencode-ida/opencode.json /root/.config/opencode/opencode.json

# 容器没有桌面环境时补一个空 xdg-open，避免 opencode 尝试打开浏览器失败。
if ! command -v xdg-open >/dev/null 2>&1; then
  cat >/usr/local/bin/xdg-open <<'EOF_XDG_OPEN'
#!/usr/bin/env sh
exit 0
EOF_XDG_OPEN
  chmod +x /usr/local/bin/xdg-open
fi

# 启动 opencode Web 服务。
hostname="${OPENCODE_HOSTNAME:-${OPENCODE_HOST:-0.0.0.0}}"
port="${OPENCODE_PORT:-4096}"

cat <<EOF
[opencode-ida] Web UI: http://${hostname}:${port}
[opencode-ida] Workspace: /workspace
[opencode-ida] MCP tool namespace: ida_pro_mcp
EOF

exec opencode web --port "$port" --hostname "$hostname" --print-logs