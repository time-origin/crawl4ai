# crawl4ai/crawlers/reddit/config.py

import argparse
import json

# --- 默认配置 ---
# 如果未通过命令行参数提供，则使用以下默认值。

# 1. 爬虫行为配置
# 伪装成一个真实的浏览器User-Agent至关重要，以避免被屏蔽。
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

CRAWLER_CONFIG = {
    "monitoring_interval_minutes": 15,  # 监控间隔分钟数 (暂未使用)
    "request_timeout_seconds": 10,      # 网络请求超时时间（秒）
    "max_posts_to_check_per_run": 50,   # 每次运行时在rising流中检查的最大帖子数
    "max_comments_to_fetch": 3,         # T型抓取中，要抓取的顶级评论数
    "max_replies_to_fetch": 1,          # T型抓取中，要抓取的子级回复数
}

# 2. 目标Subreddit监控列表
TARGET_SUBREDDITS = [
    "nottheonion", "LeopardsAteMyFace", "PoliticalHumor", "facepalm", "SelfAwarewolves",
    "OSINT", "intelligence", "NonCredibleDefense", "conspiracy", "ConflictNews",
    "worldnews", "anime_titties", "politics", "OutOfTheLoop", "PublicFreakout",
    "ukpolitics", "korea", "europe", "China_irl", "Taiwan",
    "WhitePeopleTwitter", "BlackPeopleTwitter", "TikTokCringe",
]

# 3. 用于过滤帖子标题的关键词列表
KEYWORD_FILTERS = {
    # 触发词：包含这些词的帖子将被视为必抓目标
    "trigger_words": [
        "Leak", "Scandal", "Resign", "Mistake", "Sorry", 
        "Apology", "Hot mic", "Caught", "Audio", "Video"
    ],
    # 黑名单词：包含这些词的帖子将被忽略
    "blacklist_words": [
        "Trump",  # 示例：避免某个特定人物的内容刷屏
        "Opinion",
        "Megathread",
    ]
}

def initialize_config_from_args():
    """
    解析命令行参数并更新配置变量。
    
    该函数允许通过传递JSON格式的字符串作为命令行参数来覆盖默认配置，
    从而实现由主服务进行动态控制。
    """
    global CRAWLER_CONFIG, TARGET_SUBREDDITS, KEYWORD_FILTERS

    parser = argparse.ArgumentParser(description="由命令行参数控制的Reddit爬虫。")
    
    parser.add_argument(
        '--crawler-config', 
        type=str, 
        help='一个用于覆盖 CRAWLER_CONFIG 对象的JSON字符串。'
    )
    parser.add_argument(
        '--target-subreddits', 
        type=str, 
        help='一个用于覆盖 TARGET_SUBREDDITS 列表的JSON字符串（数组）。'
    )
    parser.add_argument(
        '--keyword-filters', 
        type=str, 
        help='一个用于覆盖 KEYWORD_FILTERS 对象的JSON字符串。'
    )

    # argparse在处理模块化运行时，需要忽略未知参数
    args, unknown = parser.parse_known_args()

    try:
        if args.crawler_config:
            CRAWLER_CONFIG = json.loads(args.crawler_config)
            print("信息: CRAWLER_CONFIG 已被命令行参数覆盖。")

        if args.target_subreddits:
            TARGET_SUBREDDITS = json.loads(args.target_subreddits)
            print("信息: TARGET_SUBREDDITS 已被命令行参数覆盖。")

        if args.keyword_filters:
            KEYWORD_FILTERS = json.loads(args.keyword_filters)
            print("信息: KEYWORD_FILTERS 已被命令行参数覆盖。")
            
    except json.JSONDecodeError as e:
        print(f"致命错误: 解析命令行参数中的JSON失败。错误: {e}")
        # 如果JSON格式错误，则优雅退出。
        exit(1)

    print("\n--- 最终配置 ---")
    print(f"CRAWLER_CONFIG: {json.dumps(CRAWLER_CONFIG, ensure_ascii=False)}")
    print(f"TARGET_SUBREDDITS: {json.dumps(TARGET_SUBREDDITS, ensure_ascii=False)}")
    print(f"KEYWORD_FILTERS: {json.dumps(KEYWORD_FILTERS, ensure_ascii=False)}")
    print("---------------------------\n")
