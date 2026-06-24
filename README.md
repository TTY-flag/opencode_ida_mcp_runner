# opencode + IDA Headless MCP Runner

这个仓库用于构建一个本地 opencode Web 容器。镜像基于 `smanx/opencode:latest`，并预装 IDA Pro 9.1、`ida-headless-mcp` 以及默认的 opencode MCP 配置。

## 快速启动

以下命令都在仓库根目录执行。

```bash
docker compose up -d --build
```

查看容器状态：

```bash
docker compose ps
```

正常情况下会看到 `opencode-ida-mcp` 处于 `Up` 状态，并映射 `4096` 端口。

浏览器访问：

```text
http://127.0.0.1:4096/L3dvcmtzcGFjZQ/session
```

其中 `L3dvcmtzcGFjZQ` 是 `/workspace` 的编码路径。默认会进入容器内 `/workspace` 对应的 opencode session。如果你把宿主机端口改成了 `8080`，访问地址相应改成：

```text
http://127.0.0.1:8080/L3dvcmtzcGFjZQ/session
```

如果 Docker 在你的系统上需要额外权限，按本机环境处理即可。

## 目录结构

```text
.
├── Dockerfile
├── docker-compose.yml
├── image/
│   ├── bin/
│   ├── ida-headless-mcp/
│   ├── ida-pro-9.1/
│   ├── idapro-user/
│   └── opencode/
└── workspace/
```

关键目录说明：

- `image/`: 构建镜像时复制进容器的资源。
- `image/ida-pro-9.1/`: IDA Pro 9.1 安装目录，构建后位于容器 `/opt/ida-pro-9.1`。
- `image/ida-headless-mcp/`: vendored `ida-headless-mcp` 源码，构建时安装到容器 `/opt/ida-headless-mcp`。
- `image/idapro-user/`: IDA 用户配置目录，主要是 `ida.reg`，构建时复制到容器 `/root/.idapro`。
- `image/opencode/opencode.json`: opencode MCP 默认配置。
- `image/opencode/entrypoint.sh`: 容器入口脚本。
- `image/bin/idalib-pool-opencode`: IDA MCP 启动包装脚本。
- `workspace/`: 唯一持久化的运行目录，容器内路径是 `/workspace`。

分析样本、输出报告、临时项目文件都建议放在 `workspace/` 下。IDA 在 `workspace/` 里生成的 `.id0`、`.id1`、`.id2`、`.nam`、`.til` 等缓存文件已经由 `.gitignore` 忽略。

## 运行方式

推荐使用 Docker Compose。

构建并启动：

```bash
docker compose up -d --build
```

停止并删除容器，保留镜像和 `workspace/`：

```bash
docker compose down
```

重启当前服务：

```bash
docker compose restart
```

重新构建并强制重建容器：

```bash
docker compose up -d --build --force-recreate
```

查看日志：

```bash
docker compose logs -f
```

进入容器 shell：

```bash
docker exec -it opencode-ida-mcp bash
```

删除镜像：

```bash
docker compose down
docker image rm opencode-ida-mcp:latest
```

## Docker CLI 备用方式

不使用 Compose 时，可以手动构建并运行：

```bash
docker build -t opencode-ida-mcp:latest .
docker run -d \
  --name opencode-ida-mcp \
  --restart unless-stopped \
  -p 4096:4096 \
  -v "$PWD/workspace:/workspace" \
  opencode-ida-mcp:latest
```

停止并删除容器：

```bash
docker rm -f opencode-ida-mcp
```

查看状态：

```bash
docker ps --filter name=opencode-ida-mcp
```

查看日志：

```bash
docker logs -f opencode-ida-mcp
```

## 配置说明

默认镜像名和容器名：

```text
image: opencode-ida-mcp:latest
container: opencode-ida-mcp
```

默认端口映射在 `docker-compose.yml` 中配置：

```yaml
ports:
  - "4096:4096"
```

右侧 `4096` 是容器内 opencode Web 端口，通常不需要修改；左侧 `4096` 是宿主机访问端口。如果宿主机端口冲突，可以改左侧端口，例如：

```yaml
ports:
  - "8080:4096"
```

`workspace/` 挂载配置：

```yaml
volumes:
  - ./workspace:/workspace
```

默认最大 IDA 实例数是 `5`，由镜像环境变量和 MCP 包装脚本共同兜底：

```text
IDA_MCP_MAX_INSTANCES=5
```

临时改实例数可以在 Compose 中加环境变量：

```yaml
environment:
  IDA_MCP_MAX_INSTANCES: 4
```

Docker CLI 方式可以加：

```bash
-e IDA_MCP_MAX_INSTANCES=4
```

opencode MCP 配置位置：

```text
image/opencode/opencode.json
```

MCP 启动包装脚本位置：

```text
image/bin/idalib-pool-opencode
```

## 使用样本

把待分析二进制放到宿主机 `workspace/` 下。例如：

```text
workspace/binaries/exp
```

在 opencode Web 里使用容器路径访问它：

```text
/workspace/binaries/exp
```

示例提示词：

```text
Use ida_pro_mcp. Open /workspace/binaries/exp with idalib_open, run survey_binary, then decompile the main logic and write /workspace/report.md.
```

## 验证 MCP

确认 opencode 能看到 MCP 服务：

```bash
docker exec opencode-ida-mcp opencode mcp list
```

正常输出应包含：

```text
ida_pro_mcp connected
```

进一步验证 IDA 是否能实际打开二进制：

```bash
docker exec opencode-ida-mcp bash -lc '
set -euo pipefail
cp /bin/ls /tmp/ls-smoke
/opt/ida-headless-mcp/.venv/bin/python - <<"PY"
import json, subprocess, time

p = subprocess.Popen(
    ["/usr/local/bin/idalib-pool-opencode"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)

def send(obj):
    p.stdin.write(json.dumps(obj, separators=(",", ":")) + "\n")
    p.stdin.flush()

def recv(timeout=180):
    start = time.time()
    while True:
        if time.time() - start > timeout:
            raise TimeoutError("timeout waiting for MCP response")
        line = p.stdout.readline()
        if line:
            return json.loads(line)
        if p.poll() is not None:
            raise RuntimeError(f"MCP server exited: {p.returncode}: {p.stderr.read()}")
        time.sleep(0.05)

try:
    send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "smoke", "version": "1"},
        },
    })
    print("server", recv()["result"]["serverInfo"])
    send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    print("tool_count", len(recv()["result"]["tools"]))
    send({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "idalib_open",
            "arguments": {
                "input_path": "/tmp/ls-smoke",
                "run_auto_analysis": False,
                "session_id": "smoke",
            },
        },
    })
    print(json.dumps(recv(timeout=180).get("result", {}), ensure_ascii=False)[:1200])
finally:
    p.terminate()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
PY
'
```

成功时会看到 `tool_count` 以及 `Session created: smoke`。
