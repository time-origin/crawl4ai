# 使用 Docker 部署项目指南 (生产环境推荐)

本文档详细说明了如何使用 Docker 将本项目容器化，这是在生产环境中部署爬虫的最稳定、最可靠的方案。它能从根本上避免因开发与生产环境差异导致（如 `TargetClosedError`）的问题。

---

### 第1步：配置宿主机的 Clash 代理

为了让容器能通过宿主机的 VPN 访问网络，需要修改 Clash 的配置文件，允许来自容器的连接。

1.  打开您的 Clash 配置文件 (`config.yaml`)。
2.  进行以下**两处**修改：

    **a. 允许局域网连接:** 确保 `allow-lan` 的值为 `true`。
    ```yaml
    allow-lan: true
    ```

    **b. 监听所有地址:** 确保 `bind-address` 的值为 `*`。
    ```yaml
    bind-address: '*'
    ```

3.  **重启您的 Clash 客户端/脚本**，以使新配置生效。

---

### 第2步：构建 Docker 镜像

在项目根目录 (`crawl4ai/`) 下打开终端，运行以下命令。这个命令会使用我们项目中的 `Dockerfile-custom` 文件来创建一个名为 `crawl4ai-xcom` 的镜像。

```sh
docker build -t crawl4ai-xcom -f Dockerfile-custom .
```

**命令解释:**
*   `-t crawl4ai-xcom`: 为我们构建的镜像命名，方便后续使用。
*   `-f Dockerfile-custom`: **(关键)** 明确指定使用 `Dockerfile-custom` 这个自定义文件进行构建。
*   `.`: 代表将当前目录（项目根目录）作为构建上下文，这样 Docker 才能访问到项目中的所有文件。

---

### 第3步：运行 Docker 容器 (最终执行)

镜像构建成功后，您可以在任何安装了 Docker 的机器上，使用以下命令来运行您的爬虫。这条命令整合了网络连接、文件挂载和环境变量配置。

```sh
docker run --rm -it \
  --add-host=host.docker.internal:host-gateway \
  -v "/path/on/your/host/to/auth_state.json:/app/auth_state.json" \
  -e PROXY_SERVER="http://host.docker.internal:7890" \
  -e AUTH_JSON_PATH="/app/auth_state.json" \
  crawl4ai-xcom \
  python -m crawl4ai.crawlers.x_com.production_crawler --keyword "generative AI" --scan-scrolls 3
```

**命令参数详解:**

*   `--add-host=host.docker.internal:host-gateway`: **(Linux 系统关键)** 确保容器能通过 `host.docker.internal` 这个名字找到宿主机，以便连接代理。
*   `-v "/path/on/your/host/...:/app/auth_state.json"`: **(挂载文件)** 将您**宿主机**上的认证文件**映射**到**容器内**的 `/app/auth_state.json`。 **请务必将前面的路径替换为您 `auth_state.json` 文件在宿主机上的真实绝对路径。**
*   `-e PROXY_SERVER="..."`: 通过环境变量设置代理服务器地址。`7890` 是 Clash 默认的 HTTP 代理端口，如果您的配置不同，请在此处修改。
*   `-e AUTH_JSON_PATH="..."`: 通过环境变量告诉程序，认证文件在**容器内**的路径。
*   `crawl4ai-xcom`: 我们刚刚构建的镜像名称。
*   `python -m ...`: 您想在容器内执行的完整爬虫命令。
