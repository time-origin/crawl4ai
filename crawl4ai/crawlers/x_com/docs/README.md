# X.com 生产环境爬虫

## 运行命令

### 首次登录（生成认证文件）
该命令会打开一个浏览器窗口，请手动登录 X.com。成功登录后，会在 `crawl4ai/crawlers/x_com/` 目录下生成 `auth_state.json` 文件用于后续的免登录抓取。
```bash
python -m crawl4ai.crawlers.x_com.production_crawler --login
```

### 执行抓取任务
在项目根目录下执行以下命令。
**基本用法 (输出到文件):**
```bash
python -m crawl4ai.crawlers.x_com.production_crawler --original-task-id 101 --keyword "OpenAI"
```

**所有参数示例 (输出到 Kafka):**
```bash
python -m crawl4ai.crawlers.x_com.production_crawler --original-task-id 123 --keyword "generative AI" --scan-scrolls 3 --max-replies 10 --reply-scrolls 8 --output-method kafka --kafka-key-prefix "x.com"
```

---

## 命令行参数详解

### 任务与认证
*   `--login`:
    *   **说明**: 独立标志，用于生成认证文件，执行此操作时会忽略其他所有参数。
    *   **必需**: 否

*   `--original-task-id`:
    *   **说明**: 来自调用服务的原始任务ID，用于追踪和控制任务。
    *   **必需**: 是 (执行抓取时)
    *   **类型**: `int`

### 抓取内容
*   `--keyword`:
    *   **说明**: 您要搜索的关键词。
    *   **必需**: 是 (执行抓取时)
    *   **类型**: `str`

*   `--scan-scrolls`:
    *   **说明**: 在搜索结果页（推文列表）向下滑动的次数，以加载更多内容。
    *   **必需**: 否
    *   **默认值**: `1`
    *   **类型**: `int`

*   `--max-replies`:
    *   **说明**: 对于抓取到的每一条推文，最多抓取其下多少条回复。设置为 `0` 表示不抓取回复。
    *   **必需**: 否
    *   **默认值**: `0`
    *   **类型**: `int`

*   `--reply-scrolls`:
    *   **说明**: 在单条推文的详情页中，为了寻找回复而向下滑动的次数。
    *   **必需**: 否
    *   **默认值**: `5`
    *   **类型**: `int`

### 输出配置
*   `--output-method`:
    *   **说明**: 数据输出方式。`file` 表示保存为本地 JSON 文件，`kafka` 表示发送到 Kafka 消息队列。
    *   **必需**: 否
    *   **可选值**: `file`, `kafka`
    *   **默认值**: `file`

*   `--output-prefix`:
    *   **说明**: 当 `output-method` 为 `file` 时，输出目录的前缀。
    *   **必需**: 否
    *   **默认值**: `x_com_scrape`
    *   **类型**: `str`

*   `--kafka-key-prefix`:
    *   **说明**: 当 `output-method` 为 `kafka` 时，发送到 Kafka 的消息键 (key) 的前缀。
    *   **必需**: 否
    *   **默认值**: `x.com`
    *   **类型**: `str`
