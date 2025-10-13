命令行参数：
* --keyword (必需): 您要搜索的关键词。
* --scan-scrolls (可选): 在搜索结果页滚动的次数，默认为 1。
* --max-replies (可选): 每个推文最多抓取多少条回复，默认为 3。
* --reply-scrolls (可选): 为了抓取回复，最多滚动多少次页面，默认为 5。
* --output-prefix (可选): 输出的 JSON 文件名前缀，默认为 x_com_scrape。

* 搜索关键字 "Nvidia" (--keyword "Nvidia")
* 在搜索结果页滚动 3 次 (--scan-scrolls 3)
* 抓取每条推文的回复 (--fetch-replies)
* 每条推文最多抓取 5 条回复 (--max-replies 5)
* 为了找这5条回复，最多滚动 10 次 (--reply-scrolls 10)
* 输出的文件名前缀为 nvidia_scrape (--output-prefix nvidia_scrape)

运行命令：
首次登录（生成认证文件）
python -m crawl4ai.crawlers.x_com.production_crawler --login
根目录下执行：
python -m crawl4ai.crawlers.x_com.production_crawler --keyword "OpenAI"
所有参数：
python -m crawl4ai.crawlers.x_com.production_crawler --keyword "generative AI" --scan-scrolls 3 --max-replies 10 --reply-scrolls 8 --output-method kafka --kafka-key-prefix "x.com"

