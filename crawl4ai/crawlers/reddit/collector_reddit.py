# crawl4ai/crawlers/reddit/collector_reddit.py

import asyncio
import httpx
import json
import argparse
import re
from datetime import datetime
from uuid import uuid4
from typing import List, Dict, Any, Optional

# --- [重构] 从中央中间件导入Kafka逻辑 ---
# from crawl4ai.middlewares.kafka.producer import KafkaMiddleware

# 从当前目录导入配置
from . import config

# [FIX] 使用一个看起来像真实浏览器的User-Agent，以更好地避免403错误
CUSTOM_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# --- 数据清洗 ---
def clean_text(text: str) -> str:
    if not text: return ""
    text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+', '', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'(\*\*|__)(.*?)(\1)', r'\2', text)
    text = re.sub(r'(\*|_)(.*?)(\1)', r'\2', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_post_data(post_data: dict) -> dict:
    return {
        "id": post_data.get("id"),
        "subreddit": post_data.get("subreddit"),
        "title": clean_text(post_data.get("title")),
        "selftext": clean_text(post_data.get("selftext")),
        "author": post_data.get("author"),
        "created_utc": post_data.get("created_utc"),
        "url": post_data.get("url"),
        "upvotes": post_data.get("ups"),
        "comment_count": post_data.get("num_comments"),
        "flair": post_data.get("link_flair_text"),
        "crawled_at": datetime.utcnow().isoformat()
    }

def clean_comment_data(comment_data: dict) -> dict:
    """清洗单条回复的数据，并为其添加一个空的replies列表。"""
    return {
        "id": comment_data.get("id"),
        "author": comment_data.get("author"),
        "body": clean_text(comment_data.get("body")),
        "upvotes": comment_data.get("ups"),
        "created_utc": comment_data.get("created_utc"),
        "replies": []  # 为下一层递归预留位置
    }

# --- [NEW] 递归处理回复 ---
def process_and_clean_comments(raw_comment_list: list, max_depth: int, current_depth: int = 1) -> list:
    """递归地清洗评论及其子评论，直到达到最大深度。"""
    if current_depth > max_depth:
        return []

    cleaned_comments = []
    for item in raw_comment_list:
        # 只处理实际的评论（kind: 't1'），忽略 "more" 等对象
        if item.get('kind') != 't1':
            continue

        comment_data = item.get('data')
        if not comment_data:
            continue

        cleaned_comment = clean_comment_data(comment_data)
        
        # 检查是否存在下一层回复
        replies_obj = comment_data.get('replies')
        if replies_obj and isinstance(replies_obj, dict):
            child_comments = replies_obj.get('data', {}).get('children', [])
            # 递归调用
            cleaned_comment['replies'] = process_and_clean_comments(child_comments, max_depth, current_depth + 1)
        
        cleaned_comments.append(cleaned_comment)
        
    return cleaned_comments

# --- Reddit API 请求 ---
async def get_reddit_posts(client: httpx.AsyncClient, subreddit: str, limit: int) -> list:
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {'User-Agent': CUSTOM_USER_AGENT}
    try:
        response = await client.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        return [post['data'] for post in response.json()['data']['children']]
    except (httpx.RequestError, json.JSONDecodeError) as e:
        print(f"从 r/{subreddit} 抓取帖子时发生错误: {e}")
        return []

async def search_reddit_posts(client: httpx.AsyncClient, keyword: str, subreddit: Optional[str], limit: int) -> list:
    if subreddit:
        url = f"https://www.reddit.com/r/{subreddit}/search.json?q={keyword}&limit={limit}&sort=relevance&t=all"
    else:
        url = f"https://www.reddit.com/search.json?q={keyword}&limit={limit}&sort=relevance&t=all"
    
    print(f"  [API] 正在请求: {url}")
    headers = {'User-Agent': CUSTOM_USER_AGENT}
    try:
        response = await client.get(url, headers=headers, timeout=30.0)
        response.raise_for_status()
        return [post['data'] for post in response.json()['data']['children']]
    except (httpx.RequestError, json.JSONDecodeError) as e:
        scope = f"r/{subreddit}" if subreddit else "全局"
        print(f"在 {scope} 搜索 '{keyword}' 时发生错误: {e}")
        return []

async def get_post_comments(client: httpx.AsyncClient, subreddit: str, post_id: str, limit: int) -> list:
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json?limit={limit}"
    headers = {'User-Agent': CUSTOM_USER_AGENT}
    try:
        response = await client.get(url, headers=headers, timeout=45.0)
        response.raise_for_status()
        # API返回一个列表，[0]是帖子信息，[1]是评论信息
        return response.json()[1]['data']['children']
    except (httpx.RequestError, json.JSONDecodeError, IndexError) as e:
        print(f"为帖子 {post_id} 抓取回复时发生错误: {e}")
        return []

# --- 主程序 ---
async def main(args):
    print("--- Reddit 生产环境爬虫启动 (本地测试模式) ---")
    print(f"接收到启动参数: {args}")
    original_task_id = args.original_task_id or str(uuid4())
    print(f"任务ID: {original_task_id}")

    subreddits = args.subreddits or config.SUBREDDITS_TO_CRAWL
    post_limit = args.limit or config.POST_LIMIT_PER_SUBREDDIT
    comment_limit = args.comment_limit
    comment_depth = args.comment_depth
    keyword = args.keyword

    if not keyword and not subreddits:
        print("❌ 错误: 必须提供 --keyword 或 --subreddits 参数之一。")
        return

    try:
        async with httpx.AsyncClient() as client:
            all_raw_posts = []
            if keyword:
                print(f"\n--- 正在以关键词 '{keyword}' 执行搜索... ---")
                if subreddits:
                    for sub in subreddits:
                        print(f"--- 在 r/{sub} 中搜索... ---")
                        posts = await search_reddit_posts(client, keyword, sub, post_limit)
                        all_raw_posts.extend(posts)
                else:
                    print("--- 执行全局 Reddit 搜索... ---")
                    posts = await search_reddit_posts(client, keyword, None, post_limit)
                    all_raw_posts.extend(posts)
            else:
                print(f"--- 正在抓取以下板块的热门帖子: {', '.join(subreddits)} ---")
                for sub in subreddits:
                    posts = await get_reddit_posts(client, sub, post_limit)
                    all_raw_posts.extend(posts)

            if not all_raw_posts:
                print("\n--- 未找到任何相关帖子，任务结束。 ---")
                return

            print(f"\n--- 共找到 {len(all_raw_posts)} 条原始帖子。现在开始处理并抓取回复... ---")
            all_processed_posts = []
            for i, post_data in enumerate(all_raw_posts, 1):
                post_id = post_data.get('id', 'N/A')
                subreddit_of_post = post_data.get('subreddit')
                
                if not subreddit_of_post:
                    print(f"  处理进度: {i}/{len(all_raw_posts)} - 跳过无效帖子 (缺少subreddit信息)")
                    continue

                print(f"  处理进度: {i}/{len(all_raw_posts)} - 帖子ID: {post_id} (来自 r/{subreddit_of_post})")
                
                cleaned_post = clean_post_data(post_data)
                
                if comment_limit > 0 and comment_depth > 0:
                    print(f"    正在为帖子 {post_id} 抓取最多 {comment_limit} 条顶级回复 (深度: {comment_depth})...")
                    raw_comments = await get_post_comments(client, subreddit_of_post, post_id, comment_limit)
                    cleaned_post['replies'] = process_and_clean_comments(raw_comments, comment_depth)
                    print(f"    成功处理了顶级回复及其子回复。")
                else:
                    cleaned_post['replies'] = []

                all_processed_posts.append(cleaned_post)

            print("\n--- 所有数据处理完成，以下是抓取结果的预览 ---")
            print(json.dumps(all_processed_posts, indent=2, ensure_ascii=False))
            print("-------------------------------------------------")
        
        print("\n--- 所有板块抓取和处理任务完成。 ---")

    except Exception as e:
        print(f"在主程序中发生未预料的错误: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从Reddit抓取或搜索数据。")
    
    task_group = parser.add_argument_group('Task Identification')
    task_group.add_argument("--original-task-id", type=str, help="来自调用服务的原始任务ID。")

    scrape_group = parser.add_argument_group('Scraping Options')
    scrape_group.add_argument("--keyword", type=str, help="要搜索的关键词。如果提供此参数，将执行搜索而不是抓取热门帖子。")
    scrape_group.add_argument("--subreddits", type=str, nargs='+', help="要抓取或在其中搜索的Reddit板块列表。")
    scrape_group.add_argument("--limit", type=int, help="要抓取或搜索的帖子数量。")
    scrape_group.add_argument("--comment-limit", type=int, default=20, help="每个帖子要抓取的顶级回复数量。(默认: 20)")
    scrape_group.add_argument("--comment-depth", type=int, default=2, help="回复抓取的层级深度。1表示只抓取顶级回复。(默认: 2)")

    parsed_args = parser.parse_args()
    asyncio.run(main(parsed_args))
