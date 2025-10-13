# X.com 爬虫 Docker 启动命令指南

本文档旨在提供在 Docker 容器中运行 X.com 爬虫的详细命令和说明。

---

## 1. 前提条件

1.  **Docker 已安装**: 确保您的系统中已经安装并运行了 Docker。
2.  **Docker 镜像**: 我们的官方镜像地址是 `registry.cn-shanghai.aliyuncs.com/dazzrepo/custom-crawl4ai:latest`。
    ```sh
    # 拉取最新的镜像
    docker pull registry.cn-shanghai.aliyuncs.com/dazzrepo/custom-crawl4ai:latest
    ```
3.  **配置文件 (`.env`)**: 对于本地手动执行，建议在宿主机目录中创建一个 `.env` 文件来管理配置。

---

## 2. 基础用法：使用 .env 文件

此方法适合在本地开发或手动执行任务时使用。

### 命令结构

```sh
docker run --rm --env-file ./.env registry.cn-shanghai.aliyuncs.com/dazzrepo/custom-crawl4ai:latest python -m crawl4ai.crawlers.x_com.production_crawler [OPTIONS]
```

*   `--env-file ./.env`: 此参数会从**执行 `docker run` 命令的当前目录**（在宿主机上）读取 `.env` 文件，并将其中的所有变量作为环境变量注入到容器中。

> **重要提示**: 使用此方法时，所有 `docker run` 命令都应在**包含 `.env` 文件的目录**下执行。

---

## 3. 高级用法：通过命令行传递环境变量

在自动化场景下，最佳实践是直接通过 `-e` 或 `--env` 参数在命令行中传递所有环境变量。

### 完整命令示例 (Complete Command Example)

以下是一个综合了所有配置选项的完整命令示例。它执行一个复杂的抓取任务，并将结果推送到 Kafka。

```sh
# 综合示例：执行一个包含所有参数的复杂抓取任务
docker run --rm \
  # --- 卷挂载 ---
  -v ./output_data:/app/crawl4ai/crawlers/x_com/out/scraped \
  -v ./auth_state.json:/app/auth_state.json \
  \
  # --- 环境变量配置 ---
  # (重要) 提供访问X.com所需的HTTP或SOCKS5代理
  -e PROXY_SERVER="http://<YOUR_PROXY_IP>:<PORT>" \
  -e X_USERNAME="your_x_username" \
  -e X_PASSWORD="your_x_password" \
  -e KAFKA_BROKER_URL="kafka.example.com:9092" \
  -e KAFKA_TOPIC="x_com_scraped_data" \
  \
  # --- Docker 镜像 ---
  registry.cn-shanghai.aliyuncs.com/dazzrepo/custom-crawl4ai:latest \
  \
  # --- 爬虫脚本与参数 ---
  python -m crawl4ai.crawlers.x_com.production_crawler \
    --keyword "Generative AI" \
    --scan-scrolls 10 \
    --max-replies 20 \
    --output-method kafka \
    --output-prefix "gen_ai_run_01"
```

> #### 如何确定 `<YOUR_PROXY_IP>`?
> *   **对于 Docker Desktop (Windows/Mac)**: 直接使用特殊地址 `host.docker.internal`。示例: `-e PROXY_SERVER="http://host.docker.internal:7890"`
> *   **对于在 WSL2 中运行的 Docker**: 在 **WSL 终端**中运行 `cat /etc/resolv.conf | grep nameserver | awk '{print $2}'` 来获取宿主机 IP。示例: `-e PROXY_SERVER="http://172.31.80.1:7890"`
> *   **对于 Linux**: 通常是您主机的局域网 IP 地址 (例如 `192.168.1.100`)。
> 
> **同时，请务必确保您宿主机上的代理软件已开启“允许来自局域网的连接” (Allow connections from LAN) 选项。**

---

### 单行命令示例 (Single-Line Command Example)

以下是一个不包含卷挂载、所有参数都在一行内的完整命令，可以直接复制使用。请根据上述指南替换 `<YOUR_PROXY_IP>` 和端口。

```sh
docker run --rm -e PROXY_SERVER="http://<YOUR_PROXY_IP>:<PORT>" -e X_USERNAME="jason0447587146" -e X_PASSWORD="Abc12345678@" -e KAFKA_BROKER_URL="192.168.0.200:9092" -e KAFKA_TOPIC="x_com_scraped_data" registry.cn-shanghai.aliyuncs.com/dazzrepo/custom-crawl4ai:latest python -m crawl4ai.crawlers.x_com.production_crawler --keyword "Generative AI" --scan-scrolls 3 --max-replies 10 --output-method kafka

# --dns="8.8.8.8" 强制使用 Google DNS 来“问路”
# -e PROXY_SERVER="http://host.docker.internal:7890" 明确指定 Clash 代理来“开车”
docker run --rm --dns="8.8.8.8" -e PROXY_SERVER="http://host.docker.internal:7890" -e X_USERNAME="jason0447587146" -e X_PASSWORD="Abc12345678@" -e KAFKA_BROKER_URL="192.168.0.200:9092" -e KAFKA_TOPIC="x_com_scraped_data" registry.cn-shanghai.aliyuncs.com/dazzrepo/custom-crawl4ai:latest python -m crawl4ai.crawlers.x_com.production_crawler --keyword "Generative AI" --scan-scrolls 3 --max-replies 10 --output-method kafka

docker run --rm --dns="8.8.8.8" -e PROXY_SERVER="http://host.docker.internal:7890" -e X_USERNAME="jason0447587146" -e X_PASSWORD="Abc12345678@" registry.cn-shanghai.aliyuncs.com/dazzrepo/custom-crawl4ai:latest python -m crawl4ai.crawlers.x_com.production_crawler --login

docker run --rm --dns="8.8.8.8" -e PROXY_SERVER="http://host.docker.internal:7890" -e X_USERNAME="jason0447587146" -e X_PASSWORD="Abc12345678@" custom-crawl4ai:latest python -m crawl4ai.crawlers.x_com.production_crawler --login

```
```sh 
# 删除无用的镜像
docker rmi $(docker images | grep '<none>' | awk '{print $3}')
```
