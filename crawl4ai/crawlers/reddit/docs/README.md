# Reddit 爬虫模块使用指南

## 1. 概述

本模块是一个为 `Ratio'd` 游戏定制的 Reddit 数据采集工具。它遵循一种智能策略，旨在准实时地发现并抓取与政治相关的、具有“梗”潜力的热点事件。

其核心工作流程分为两步：
1.  **横向监控**：通过轻量级的 `.json` 接口高频扫描多个目标板块（Subreddits）的 `rising` 队列，根据关键词快速筛选出有潜力的帖子。
2.  **纵向深挖**：一旦发现潜力帖子，立即访问该帖子详情页的 `.json` 接口，进行深度“T型抓取”，提取帖子本身以及最热门的几条评论（“神回复”）。

本爬虫**不使用**任何官方API Key，完全模拟匿名用户的网页请求。

## 2. 文件结构

为了便于维护，项目被拆分为以下几个核心模块：

```
reddit/
├── __init__.py
├── config.py           # 存放默认配置和参数解析逻辑
├── utils.py            # 存放通用的网络请求函数
├── parser.py           # 负责解析.json数据，提取帖子和评论
├── models.py           # 定义了爬取结果的数据模型
├── main.py             # 主入口，编排和调度爬虫流程
└── docs/
    └── README.md       # (本使用指南)
```

-   `config.py`: 存放默认配置。**（重要：所有配置都可通过命令行参数覆盖）**
-   `utils.py`: 管理网络请求和伪装。
-   `parser.py`: 负责解析数据。
-   `models.py`: 定义了输出数据的结构。
-   `main.py`: 运行整个爬虫的入口点。

## 3. 安装与配置

### 3.1 安装依赖

本模块主要依赖 `requests` 库。请通过 pip 安装：
```shell
pip install requests
```

### 3.2 基础配置

打开 `crawl4ai/crawlers/reddit/config.py` 文件。该文件包含了爬虫的所有默认配置，如默认的目标板块、关键词等。在本地开发或测试时，您可以直接修改这些默认值。

对于自动化部署和由主服务调度，请参考第5节“动态参数化运行”。

## 4. 如何运行

配置完成后，您可以从项目的根目录 (`crawl4ai` 的上一级目录) 运行主程序。

### 4.1 使用默认配置运行

如果只是想使用 `config.py` 中定义的默认配置进行一次测试运行，执行以下命令：

```shell
python -m crawl4ai.crawlers.reddit.main
```

### 4.2 动态参数化运行 (核心)

请参考下一节的说明。

**注意**: 直接在 `reddit` 目录下运行 `python main.py` 会因相对导入问题而失败。请务必在项目根目录使用 `-m` 模块化运行方式。

## 5. 动态参数化运行 (自动化与调度)

为了便于主服务进行自动化调度和控制，本爬虫的所有核心配置都可以通过命令行参数动态传入。参数的值必须是**合法的JSON格式字符串**。

### 5.1 可用参数

-   `--crawler-config 'JSON_STRING'`
    -   **作用**: 覆盖 `CRAWLER_CONFIG` 对象，控制爬虫的具体行为。
    -   **示例**: `'{"request_timeout_seconds": 15, "max_comments_to_fetch": 5}'`

-   `--target-subreddits 'JSON_STRING'`
    -   **作用**: 覆盖 `TARGET_SUBREDDITS` 列表，动态指定要监控的板块。
    -   **示例**: `'["worldnews", "gaming", "technology"]'`

-   `--keyword-filters 'JSON_STRING'`
    -   **作用**: 覆盖 `KEYWORD_FILTERS` 对象，动态修改关键词。
    -   **示例**: `'{"trigger_words": ["Breaking"], "blacklist_words": ["Rumor"]}'`

### 5.2 完整示例

假设主服务需要临时将爬取目标调整为仅监控 `r/worldnews`，并只关心包含 "Leak" 或 "Scandal" 的帖子，可以构造并执行以下命令：

```shell
python -m crawl4ai.crawlers.reddit.main \
--target-subreddits '["worldnews"]' \
--keyword-filters '{"trigger_words": ["Leak", "Scandal"], "blacklist_words": []}'
```

程序在启动时会打印出最终生效的配置，方便您确认参数是否被成功覆盖。

## 6. 输出格式

爬虫运行成功后，会将抓取到的结构化数据以 JSON 格式打印到标准输出（stdout）。每个被成功抓取的帖子都对应一个 JSON 对象，其结构由 `models.py` 中的 `ExtractedPost` 和 `ExtractedComment` 定义。
```json
[
  {
    "id": "post_id",
    "title": "Post Title",
    "url": "/r/subreddit/comments/post_id/post_title/",
    "score": 1234,
    "author": "post_author",
    "subreddit": "subreddit_name",
    "selftext": "...",
    "comments": [
      {
        "id": "comment_id",
        "author": "comment_author",
        "body": "This is a top-level comment.",
        "score": 567,
        "url": "...",
        "replies": [
          {
            "id": "reply_id",
            "author": "reply_author",
            "body": "This is a reply to the top-level comment.",
            "score": 89,
            "url": "...",
            "replies": []
          }
        ]
      }
    ]
  }
]
```
