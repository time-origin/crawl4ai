# crawl4ai/crawlers/reddit/models.py

from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class ExtractedComment:
    """
    一个用于存储单个已提取评论或回复的结构化数据的 dataclass。
    """
    id: str
    author: Optional[str]
    body: str
    score: int
    url: str
    replies: List['ExtractedComment'] = field(default_factory=list)

@dataclass
class ExtractedPost:
    """
    一个用于存储从Reddit帖子中提取的所有结构化数据的 dataclass，
    遵循T型模型，包含帖子本身及其顶级评论。
    """
    id: str
    title: str
    url: str
    score: int
    author: Optional[str]
    subreddit: str
    selftext: str
    comments: List[ExtractedComment] = field(default_factory=list)
