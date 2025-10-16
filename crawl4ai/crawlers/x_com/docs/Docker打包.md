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

### 第2步：准备外部配置文件

将您的 `.env` 文件和 `auth_state.json` 文件都放置在宿主机的一个固定目录下，例如您指定的：
`/home/gyq/workspace/game_data/resources/xcom_auth/`

---

### 第3步：构建 Docker 镜像

在项目根目录 (`crawl4ai/`) 下打开终端，运行以下命令。这个命令会使用我们项目中的 `Dockerfile-custom` 文件来创建一个名为 `crawl4ai-xcom` 的镜像。

```sh
docker build -t crawl4ai-xcom -f Dockerfile-custom .
```

---

### 第4步：运行容器

我们提供两种方式来运行容器：直接使用 `docker run` 命令，或者使用 `docker-compose`（更推荐）。

#### 方式一：使用 `docker run` 命令

此方式直接、灵活，适合快速测试或在不方便创建 `docker-compose.yml` 文件的环境中使用。

```sh
docker run --rm -it \
  --add-host=host.docker.internal:host-gateway \
  -v "/home/gyq/workspace/game_data/resources/xcom_auth/.env:/app/.env" \
  -v "/home/gyq/workspace/game_data/resources/xcom_auth/auth_state.json:/app/auth_state.json" \
  -e PROXY_SERVER="http://host.docker.internal:7890" \
  -e AUTH_JSON_PATH="/app/auth_state.json" \
  crawl4ai-xcom \
  python -m crawl4ai.crawlers.x_com.production_crawler \
    --keyword "generative AI" \
    --scan-scrolls 3 \
    --max-replies 10 \
    --reply-scrolls 8 \
    --output-method kafka \
    --kafka-key-prefix "x.com"
```

#### 方式二：使用 `docker-compose` (更推荐)

此方式将所有复杂的配置都固化在 `docker-compose-custom.yml` 文件中，使得启动命令极其简单，是规范化部署的最佳实践。

**1. 检查 `docker-compose-custom.yml` 文件**

确保项目根目录下的 `docker-compose-custom.yml` 文件内容正确无误（我们已在上一步创建）。

**2. 启动服务**

在项目根目录 (`crawl4ai/`) 下打开终端，运行以下命令：

```sh
docker-compose -f docker-compose-custom.yml up
```

**命令解释:**
*   `-f docker-compose-custom.yml`: 明确指定使用我们自定义的 compose 文件。
*   `up`: 创建并启动在 compose 文件中定义的服务。添加 `--build` 参数可以在启动前强制重新构建镜像，例如 `docker-compose ... up --build`。

Docker Compose 会自动读取文件中的所有配置（镜像名、网络、挂载、环境变量、要执行的命令等），然后为您启动容器。这使得您的每次运行都变得简单、一致且不易出错。
