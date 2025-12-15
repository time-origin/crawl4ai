# crawl4ai/crawlers/reddit/main.py

import json
import time
from dataclasses import asdict

# 导入配置模块和函数
from . import config
from .utils import get_reddit_json
from .parser import parse_subreddit_feed, parse_post_details

def run_crawler_once():
    """
    执行一次完整的Reddit爬虫运行流程（使用.json接口方法）。
    
    它会使用在程序启动时加载的配置（默认配置或通过命令行参数传入的配置）。
    """
    print("="*50)
    print(f"爬虫运行开始于 {time.ctime()} (使用 .json 方法)")
    print("="*50)
    
    all_extracted_data = []
    
    # 1. 从所有目标Subreddit中发现有潜力的帖子
    print("--- 阶段 1: 监控Subreddit Feeds ---")
    potential_posts_raw = []
    for subreddit in config.TARGET_SUBREDDITS:
        print(f"正在检查 /r/{subreddit}/rising.json...")
        feed_url = f"https://www.reddit.com/r/{subreddit}/rising.json"
        feed_json = get_reddit_json(feed_url)
        if feed_json:
            posts = parse_subreddit_feed(feed_json)
            if posts:
                print(f"  [+] 在 /r/{subreddit} 中发现 {len(posts)} 个潜力帖子")
                potential_posts_raw.extend(posts)
        time.sleep(1) # 尊重Reddit服务器，增加一个小延迟

    if not potential_posts_raw:
        print("\n本次运行未发现符合条件的帖子。")
        return

    # 2. 为每个潜力帖子提取详细信息
    print(f"\n--- 阶段 2: 为 {len(potential_posts_raw)} 个帖子提取详情 ---")
    for i, post_raw in enumerate(potential_posts_raw):
        permalink = post_raw.get('permalink')
        if not permalink:
            continue
            
        post_url = f"https://www.reddit.com{permalink}"
        print(f"正在提取帖子 {i+1}/{len(potential_posts_raw)}: {post_raw.get('title')[:50]}...")
        
        detail_json = get_reddit_json(post_url)
        if detail_json:
            extracted_post = parse_post_details(detail_json)
            if extracted_post:
                all_extracted_data.append(extracted_post)
        time.sleep(1) # 在请求详情页之间也增加小延迟

    # 3. 处理并打印最终结果
    if all_extracted_data:
        print("\n\n" + "="*50)
        print("爬虫运行完成: 成功提取了以下帖子数据:")
        print("="*50)
        
        # 使用 asdict 将 dataclass 转换为字典，以便进行JSON序列化
        output_json = json.dumps(
            [asdict(post) for post in all_extracted_data], 
            indent=2,
            ensure_ascii=False # 确保中文字符能正确显示
        )
        print(output_json)
    else:
        print("\n\n" + "="*50)
        print("爬虫运行完成: 未能从潜力帖子中提取到任何数据。")
        print("="*50)

def main():
    """
    Reddit爬虫应用的主入口。
    
    首先，它会从命令行参数初始化配置，
    然后运行一次爬虫的主要逻辑。
    """
    config.initialize_config_from_args()
    run_crawler_once()

if __name__ == "__main__":
    main()
