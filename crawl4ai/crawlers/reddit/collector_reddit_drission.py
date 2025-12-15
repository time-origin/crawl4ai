# -*- coding: utf-8 -*-
"""
@Project: crawl4ai
@File   : collector_reddit_drission.py
@Author : Assistant

概要:
    本文件实现了使用 DrissionPage 库深度抓取 Reddit 帖子的功能。
    它能够模拟浏览器行为，获取包括动态加载评论在内的全量数据，
    并经过优化以支持在无头服务器（如 Linux）上高效运行。

核心依赖:
    - DrissionPage: 请通过 'pip install DrissionPage' 安装。
    - 环境: 需要预装 Chromium 内核的浏览器 (如 Google Chrome)。
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time
from typing import List, Dict
import os

def scrape_reddit_post_with_drission(url: str) -> List[Dict[str, str]]:
    """
    使用 DrissionPage 深度抓取 Reddit 帖子的所有评论。

    该方法通过模拟浏览器行为，可以展开并抓取通过 .json 接口无法获取的
    “More Comments”内容。它经过优化，可在无图形界面的 Linux 服务器上运行。

    核心策略:
    1. 无头模式: 兼容 Linux 服务器，无须图形界面。
    2. 无图模式: 提升加载速度。
    3. 模拟滚动: 触发动态加载。
    4. 智能点击: 展开被折叠的评论。
    5. 高效解析: 直接读取新版 Reddit 前端组件的属性。

    Args:
        url: 目标 Reddit 帖子的 URL。

    Returns:
        一个包含所有评论信息的字典列表，每个字典包含 author, score, id, 和 text。
    """
    co = ChromiumOptions()

    # --- 1. 初始化浏览器配置 ---
    # 禁用图片加载，大幅提升页面加载速度
    co.set_load_mode('none')

    # 启用无头模式，这是在 Linux 服务器上运行的必要条件。
    # 为了方便本地调试，可以设置环境变量 `HEADLESS=false` 来显示浏览器界面。
    if os.environ.get('HEADLESS', 'true').lower() == 'true':
        print("信息: 以无头模式 (Headless) 运行...")
        co.headless()

    # 添加在 Linux 无头模式下稳定运行所需的关键参数
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')

    page = ChromiumPage(co)
    print(f"信息: 正在访问: {url}")
    page.get(url)

    # 等待页面初步加载完成
    page.wait.load_start()
    time.sleep(2)

    # --- 2. 循环展开所有评论 ---
    max_scrolls = 10  # 设置一个最大滚动次数，防止无限循环
    print("信息: 开始展开评论...")
    for i in range(max_scrolls):
        page.scroll.to_bottom()
        print(f"  -> 正在滚动页面 ({i + 1}/{max_scrolls})...")
        time.sleep(1.5)  # 等待滚动后网络请求和页面渲染

        # 查找并点击所有“加载更多评论”的按钮
        # DrissionPage 可直接穿透 Shadow DOM 查找元素，选择器兼容新旧版UI
        more_buttons = page.eles('text:View more comments') or page.eles('text:More comments')

        if not more_buttons:
            print("  -> 未找到“加载更多”按钮，可能已全部展开。")
            break

        clicked_count = 0
        for btn in more_buttons:
            # 确保按钮在页面上可见且可点击
            if btn.states.is_displayed:
                btn.click(by_js=True)  # 使用 JS 点击，速度快且成功率高
                clicked_count += 1
                time.sleep(0.5)  # 每次点击后短暂等待，避免过快操作

        if clicked_count > 0:
            print(f"  -> 点击了 {clicked_count} 个“加载更多”按钮。")
        else:
            print("  -> 所有“加载更多”按钮均不可见，结束展开操作。")
            break

    # --- 3. 统一解析所有已加载的评论 ---
    print("\n信息: 所有评论已展开，开始提取数据...")

    # 使用 <shreddit-comment> 标签定位，这是新版 Reddit 封装评论数据的核心组件
    comments = page.eles('tag:shreddit-comment')

    print(f"信息: 当前页面共加载了 {len(comments)} 条评论。")

    data_list = []
    for c in comments:
        # 直接从标签属性读取数据，效率远高于解析内部 HTML
        author = c.attr('author')
        score = c.attr('score')
        comment_id = c.attr('thingid')

        # 评论正文在内部的特定 div 中，使用模糊匹配 'id^="comment-content-"' 提高稳定性
        content_div = c.ele('css:div[id^="comment-content-"]')
        text = content_div.text if content_div else "[内容解析失败]"

        item = {
            "id": comment_id,
            "author": author,
            "score": score,
            "text": text
        }
        data_list.append(item)

    page.quit()
    print("信息: 数据提取完成！")
    return data_list


if __name__ == '__main__':
    # --- 测试用例 ---
    TEST_URL = "https://www.reddit.com/r/Python/comments/1h7x8h2/what_are_some_good_advanced_python_project_ideas/"

    print("=" * 50)
    print("开始执行 Reddit 深度抓取测试")
    print("=" * 50)

    all_comments_data = scrape_reddit_post_with_drission(TEST_URL)

    print(f"\n结果: 成功抓取到 {len(all_comments_data)} 条评论。")

    # 打印前5条作为结果预览
    if all_comments_data:
        print("\n--- 抓取结果预览 (前5条) ---")
        for i, comment in enumerate(all_comments_data[:5]):
            print(f"\n--- 评论 {i+1} ---")
            print(f"  ID: {comment['id']}")
            print(f"  Author: {comment['author']}")
            print(f"  Score: {comment['score']}")
            # 替换换行符，使单行输出更整洁
            print(f"  Text: {comment['text'][:150].replace(chr(10), ' ')}...")
    else:
        print("\n结果: 未抓取到任何评论。")
