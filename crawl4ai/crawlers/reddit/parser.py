# crawl4ai/crawlers/reddit/parser.py

from .models import ExtractedPost, ExtractedComment
from .config import CRAWLER_CONFIG, KEYWORD_FILTERS

def parse_subreddit_feed(json_data: dict) -> list[dict]:
    """
    解析来自Subreddit Feed的JSON数据(例如 /r/politics/rising.json)，
    并返回一个经过筛选的潜在帖子列表。

    参数:
        json_data (dict): 从Subreddit Feed解析得到的JSON数据。

    返回:
        list[dict]: 一个符合条件的帖子数据字典列表。
    """
    potential_posts = []
    if not isinstance(json_data, dict) or 'data' not in json_data or 'children' not in json_data['data']:
        return []

    trigger_words = {word.lower() for word in KEYWORD_FILTERS["trigger_words"]}
    blacklist_words = {word.lower() for word in KEYWORD_FILTERS["blacklist_words"]}

    for post in json_data['data']['children']:
        post_data = post.get('data', {})
        title = post_data.get('title', '').lower()
        
        has_trigger = any(word in title for word in trigger_words)
        has_blacklist = any(word in title for word in blacklist_words)

        if has_trigger and not has_blacklist:
            potential_posts.append(post_data)
    
    return potential_posts


def parse_post_details(json_data: list) -> ExtractedPost | None:
    """
    解析来自单个帖子详情页的JSON数据(例如 /r/subreddit/comments/post_id.json)，
    并使用T型抓取法将数据提取到一个ExtractedPost对象中。

    参数:
        json_data (list): 从帖子详情页解析得到的JSON数据。它是一个列表，
                          索引0包含帖子数据，索引1包含评论数据。

    返回:
        ExtractedPost | None: 一个ExtractedPost对象，如果解析失败则返回None。
    """
    if not isinstance(json_data, list) or len(json_data) < 2:
        return None

    try:
        post_data_raw = json_data[0]['data']['children'][0]['data']
        
        post_obj = ExtractedPost(
            id=post_data_raw.get('id'),
            title=post_data_raw.get('title'),
            url=post_data_raw.get('permalink'),
            score=post_data_raw.get('score'),
            author=post_data_raw.get('author'),
            subreddit=post_data_raw.get('subreddit'),
            selftext=post_data_raw.get('selftext')
        )

        # --- T型评论提取 ---
        comments_raw = json_data[1]['data']['children']
        max_comments = CRAWLER_CONFIG.get("max_comments_to_fetch", 3)
        max_replies = CRAWLER_CONFIG.get("max_replies_to_fetch", 1)
        
        comments_fetched = 0
        for comment_item in comments_raw:
            if comments_fetched >= max_comments:
                break
            
            # 't1' 是Reddit API中表示评论的类型
            if comment_item.get('kind') != 't1':
                continue

            comment_data_raw = comment_item['data']
            comment_obj = ExtractedComment(
                id=comment_data_raw.get('id'),
                author=comment_data_raw.get('author'),
                body=comment_data_raw.get('body'),
                score=comment_data_raw.get('score'),
                url=comment_data_raw.get('permalink')
            )

            # 提取回复
            if 'replies' in comment_data_raw and isinstance(comment_data_raw['replies'], dict):
                replies_raw = comment_data_raw['replies']['data']['children']
                replies_fetched = 0
                for reply_item in replies_raw:
                    if replies_fetched >= max_replies:
                        break
                    if reply_item.get('kind') != 't1':
                        continue
                    
                    reply_data_raw = reply_item['data']
                    reply_obj = ExtractedComment(
                        id=reply_data_raw.get('id'),
                        author=reply_data_raw.get('author'),
                        body=reply_data_raw.get('body'),
                        score=reply_data_raw.get('score'),
                        url=reply_data_raw.get('permalink')
                    )
                    comment_obj.replies.append(reply_obj)
                    replies_fetched += 1

            post_obj.comments.append(comment_obj)
            comments_fetched += 1
            
        return post_obj

    except (IndexError, KeyError, TypeError) as e:
        print(f"错误: 因JSON结构不符合预期，解析帖子详情失败。详情: {e}")
        return None
