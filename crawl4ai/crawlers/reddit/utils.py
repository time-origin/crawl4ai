# crawl4ai/crawlers/reddit/utils.py

import requests
import time
from .config import USER_AGENT, CRAWLER_CONFIG

def get_reddit_json(url: str) -> dict | list | None:
    """
    从给定的Reddit URL获取并返回JSON数据。

    该函数负责处理在URL后附加'.json'、设置必需的User-Agent请求头，
    以及管理基本的请求错误和速率限制。

    参数:
        url (str): 要获取的Reddit URL。

    返回:
        dict | list | None: 如果请求成功，则返回解析后的JSON数据，否则返回None。
    """
    # 确保URL以.json结尾
    if not url.endswith('.json'):
        url = url.rstrip('/') + '.json'

    headers = {
        'User-Agent': USER_AGENT
    }

    try:
        response = requests.get(
            url, 
            headers=headers, 
            timeout=CRAWLER_CONFIG.get("request_timeout_seconds", 10)
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # 被速率限制
            print("警告: 请求过于频繁 (429)，休眠60秒...")
            time.sleep(60)
            return None
        else:
            print(f"警告: 获取 {url} 失败。状态码: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"错误: 请求 {url} 失败。详情: {e}")
        return None
