# opencode + IDA Headless MCP Runner

这个工程用于构建一个本地 opencode Web 容器，镜像基于 `smanx/opencode:latest`，并预装 opencode 与 `winmin/ida-headless-mcp` 运行环境。


## 目录说明

顶层目录：

- `image/`: 构建镜像时会 COPY 进容器的资产。
- `workspace/`: 唯一的运行时挂载目录，容器内路径是 `/workspace`。待分析二进制、输出报告、临时项目文件都放这里。
- `Dockerfile`: 从 `smanx/opencode:latest` 构建 opencode + IDA + MCP 镜像。
- `docker-compose.yml`: 可选的 Compose 启动配置，映射 `4096` 端口并挂载 `workspace/`。

`image/` 目录内部：

- `image/ida-pro-9.1/`: 放本机 IDA Pro 9.1 安装目录，构建时复制到容器 `/opt/ida-pro-9.1`。
- `image/ida-headless-mcp/`: vendored `winmin/ida-headless-mcp` 源码，构建时安装为 MCP 服务。
- `image/idapro-user/`: 放 IDA 用户配置，主要是 `ida.reg`，构建时复制到容器 `/root/.idapro`。
- `image/opencode/`: opencode 默认 MCP 配置和容器入口脚本。
- `image/bin/`: 容器里的 MCP 启动包装脚本。

## 准备 IDA 文件

在宿主机上把 IDA Pro 9.1 目录同步到工程内：

```bash
cd /home/pwn20tty/Desktop/opencode_ida_mcp_runner
rsync -a --delete /home/pwn20tty/ida-pro-9.1/ image/ida-pro-9.1/
```

把 IDA 用户配置复制进来：

```bash
mkdir -p image/idapro-user
cp /home/pwn20tty/.idapro/ida.reg image/idapro-user/ida.reg
```

如果没有 `ida.reg`，容器可能能构建，但真正调用 `idalib_open` 时可能失败，常见错误是：

```text
License not yet accepted, cannot run in batch mode
```

## 状态说明

容器不会预置 API key，也不会设置 `OPENCODE_SERVER_PASSWORD`。用户打开 Web UI 后，在 opencode 页面里自行配置 provider/auth。

每次容器启动时都会清空 opencode 的本地状态目录，并重新写入默认 MCP 配置。因此历史对话、provider/auth 等状态不会跨启动保留。唯一持久化的目录是 `workspace/`。

浏览器如果还显示旧页面，可以清理 `http://192.168.227.143:4096` 的站点数据，或用无痕窗口打开。

## 使用方式

可以二选一：

- Docker Compose 管理：命令短，适合日常使用。
- Docker CLI 管理：完全不用 Compose，所有参数都写在命令行里。

两种方式都默认使用同一个镜像名和容器名：

```text
image: opencode-ida-mcp:latest
container: opencode-ida-mcp
```

不要同时启动两套方式，否则容器名和 `4096` 端口会冲突。切换方式前，先停止当前容器。

## Docker Compose 管理

构建镜像：

```bash
cd /home/pwn20tty/Desktop/opencode_ida_mcp_runner
sudo docker compose build
```

启动：

```bash
sudo docker compose up -d
```

访问：

```text
http://192.168.227.143:4096
```

停止并删除容器，保留镜像和 `workspace/`：

```bash
sudo docker compose down
```

重启当前服务：

```bash
sudo docker compose restart
```

重新构建并强制重建容器：

```bash
sudo docker compose up -d --build --force-recreate
```

查看状态：

```bash
sudo docker compose ps
```

查看日志：

```bash
sudo docker compose logs -f
```

进入容器 shell：

```bash
sudo docker exec -it opencode-ida-mcp bash
```

删除镜像：

```bash
sudo docker compose down
sudo docker image rm opencode-ida-mcp:latest
```

## Docker CLI 管理

构建镜像：

```bash
cd /home/pwn20tty/Desktop/opencode_ida_mcp_runner
sudo docker build -t opencode-ida-mcp:latest .
```

启动容器：

```bash
sudo docker run -d   --name opencode-ida-mcp   --restart unless-stopped   -p 4096:4096   -v "$PWD/workspace:/workspace"   opencode-ida-mcp:latest
```

访问：

```text
http://192.168.227.143:4096
```

停止容器，但不删除容器：

```bash
sudo docker stop opencode-ida-mcp
```

重新启动已停止的容器：

```bash
sudo docker start opencode-ida-mcp
```

重启当前容器：

```bash
sudo docker restart opencode-ida-mcp
```

停止并删除容器：

```bash
sudo docker rm -f opencode-ida-mcp
```

重新构建并重建容器：

```bash
cd /home/pwn20tty/Desktop/opencode_ida_mcp_runner
sudo docker rm -f opencode-ida-mcp 2>/dev/null || true
sudo docker build -t opencode-ida-mcp:latest .
sudo docker run -d   --name opencode-ida-mcp   --restart unless-stopped   -p 4096:4096   -v "$PWD/workspace:/workspace"   opencode-ida-mcp:latest
```

查看状态：

```bash
sudo docker ps --filter name=opencode-ida-mcp
```

查看日志：

```bash
sudo docker logs -f opencode-ida-mcp
```

进入容器 shell：

```bash
sudo docker exec -it opencode-ida-mcp bash
```

删除镜像：

```bash
sudo docker rm -f opencode-ida-mcp
sudo docker image rm opencode-ida-mcp:latest
```

删除所有 Docker 容器：

```bash
sudo docker ps -aq | xargs -r sudo docker rm -f
```

## 配置说明

Compose 方式的端口映射在 `docker-compose.yml` 里：

```yaml
ports:
  - "4096:4096"
```

Docker CLI 方式的端口映射在 `docker run` 命令里：

```bash
-p 4096:4096
```

如果宿主机想换成 `8080` 端口：

```yaml
# docker-compose.yml
ports:
  - "8080:4096"
```

```bash
# docker CLI
-p 8080:4096
```

右边的 `4096` 是容器内 opencode Web 端口，通常不要改；左边是宿主机访问端口。

`workspace/` 挂载：

```yaml
# docker-compose.yml
volumes:
  - ./workspace:/workspace
```

```bash
# docker CLI
-v "$PWD/workspace:/workspace"
```

opencode MCP 配置在：

```text
image/opencode/opencode.json
```

IDA MCP 启动包装脚本在：

```text
image/bin/idalib-pool-opencode
```

默认最大 IDA 实例数是 `2`。如果只想临时改运行参数，可以在 Docker CLI 启动时加环境变量：

```bash
-e IDA_MCP_MAX_INSTANCES=4
```

例如：

```bash
sudo docker run -d   --name opencode-ida-mcp   --restart unless-stopped   -p 4096:4096   -v "$PWD/workspace:/workspace"   -e IDA_MCP_MAX_INSTANCES=4   opencode-ida-mcp:latest
```

Compose 方式也可以在 `docker-compose.yml` 里加：

```yaml
environment:
  IDA_MCP_MAX_INSTANCES: 4
```

## 使用样本

把样本放到宿主机的 `workspace/` 里，然后在 opencode Web 里用容器路径访问。例如宿主机文件是：

```text
/home/pwn20tty/Desktop/opencode_ida_mcp_runner/workspace/binaries/exp
```

在 opencode 里就使用：

```text
Use ida_pro_mcp. Open /workspace/binaries/exp with idalib_open, run survey_binary, then decompile the main logic and write /workspace/report.md.
```

## 测试 MCP

先确认 MCP 连接状态：

```bash
sudo docker exec opencode-ida-mcp opencode mcp list
```

正常应看到：

```text
ida_pro_mcp connected
```

进一步测试 IDA 是否能实际打开二进制：

```bash
sudo docker run --rm --entrypoint bash opencode-ida-mcp:latest -lc '
set -euo pipefail
cp /bin/ls /tmp/ls-smoke
opencode mcp list
/opt/ida-headless-mcp/.venv/bin/python - <<"PY"
import json, subprocess, time
p = subprocess.Popen(["/usr/local/bin/idalib-pool-opencode"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
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
            raise RuntimeError(f"MCP server exited: {p.returncode}")
        time.sleep(0.05)
try:
    send({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1"}}})
    print(recv()["result"]["serverInfo"])
    send({"jsonrpc":"2.0","method":"notifications/initialized","params":{}})
    send({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
    print("tool_count", len(recv()["result"]["tools"]))
    send({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"idalib_open","arguments":{"input_path":"/tmp/ls-smoke","run_auto_analysis":False,"session_id":"smoke"}}})
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

成功时会看到 `tool_count` 和 `Session created: smoke`。
