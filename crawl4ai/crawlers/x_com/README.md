命令行参数：
* --keyword (必需): 您要搜索的关键词。
* --scan-scrolls (可选): 在搜索结果页滚动的次数，默认为 1。
* --fetch-replies (可选): 一个开关，一旦使用，就代表您想要抓取回复。
* --max-replies (可选): 每个推文最多抓取多少条回复，默认为 3。
* --reply-scrolls (可选): 为了抓取回复，最多滚动多少次页面，默认为 5。
* --output-prefix (可选): 输出的 JSON 文件名前缀，默认为 x_com_scrape。

| 参数 (您提供) | 默认值 (您提供) | 代码中的对应 (tweet_detail_scene.py) | 是否一致 | 备注 | | :--- | :--- | :--- | :--- | :--- | 
| --keyword | (必需) | 不适用 | - | 这个参数用于搜索，不属于单个推文详情页的抓取逻辑。 | 
| --scan-scrolls | 1 | 不适用 | - | 这个参数同样用于搜索结果页的滚动，不在此文件中。 | 
| --fetch-replies | (开关) | kwargs.get("include_replies", False) | ✅ 一致 | 代码通过 include_replies 这个布尔值来决定是否执行抓取回复的逻辑。 | 
| --max-replies | 3 | kwargs.get("max_replies") | ✅ 一致 | 代码通过 max_replies 控制抓取回复的最大数量。 | 
| --reply-scrolls | 5 | kwargs.get("reply_scroll_count", 5) | ✅ 完全一致 | 代码中明确使用了 reply_scroll_count，并且默认值也是 5。 | 
| --output-prefix | x_com_scrape | 不适用 | - | 这个参数用于定义最终输出文件的名称，通常在调用所有场景的主程序中处理，不属于单个场景的逻辑。 |


运行命令：
根目录下执行：
python -m crawl4ai.crawlers.x_com.production_crawler --keyword "OpenAI" --fetch-replies