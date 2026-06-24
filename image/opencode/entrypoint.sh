#!/usr/bin/env bash
set -euo pipefail

export IDADIR="${IDADIR:-/opt/ida-pro-9.1}"
export IDA_MCP_HOME="${IDA_MCP_HOME:-/opt/ida-headless-mcp}"
export LD_LIBRARY_PATH="$IDADIR:$IDADIR/plugins:${LD_LIBRARY_PATH:-}"
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"

rm -rf /root/.config/opencode /root/.local/share/opencode /root/.cache/opencode
mkdir -p /root/.config/opencode /root/.local/share/opencode /workspace
cp /opt/opencode-ida/opencode.json /root/.config/opencode/opencode.json

if ! command -v xdg-open >/dev/null 2>&1; then
  cat >/usr/local/bin/xdg-open <<'EOF_XDG_OPEN'
#!/usr/bin/env sh
exit 0
EOF_XDG_OPEN
  chmod +x /usr/local/bin/xdg-open
fi

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

hostname="${OPENCODE_HOSTNAME:-${OPENCODE_HOST:-0.0.0.0}}"
port="${OPENCODE_PORT:-4096}"

args=("web")
if [ -n "$port" ]; then
  args+=("--port" "$port")
fi
if [ -n "$hostname" ]; then
  args+=("--hostname" "$hostname")
fi

case "${OPENCODE_MDNS:-false}" in
  1|true|TRUE|yes|YES|on|ON) args+=("--mdns") ;;
esac
if [ -n "${OPENCODE_MDNS_DOMAIN:-}" ]; then
  args+=("--mdns-domain" "${OPENCODE_MDNS_DOMAIN}")
fi
if [ -n "${OPENCODE_LOG_LEVEL:-}" ]; then
  args+=("--log-level" "${OPENCODE_LOG_LEVEL}")
fi
case "${OPENCODE_PRINT_LOGS:-true}" in
  1|true|TRUE|yes|YES|on|ON) args+=("--print-logs") ;;
esac
if [ -n "${OPENCODE_CORS:-}" ]; then
  cors_list="${OPENCODE_CORS//,/ }"
  for origin in $cors_list; do
    [ -n "$origin" ] || continue
    args+=("--cors" "$origin")
  done
fi

cat <<EOF
[opencode-ida] Web UI: http://0.0.0.0:${port}
[opencode-ida] Workspace: /workspace
[opencode-ida] State reset on every container start
[opencode-ida] Put binaries under /workspace and open them with /workspace/<path>
[opencode-ida] MCP tool namespace: ida_pro_mcp
EOF

exec opencode "${args[@]}"
