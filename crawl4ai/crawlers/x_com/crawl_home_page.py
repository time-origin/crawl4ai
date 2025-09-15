"""
抓取X.com首页内容并进行格式化
使用生产版本的爬虫来保持浏览器会话
"""

import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from crawl4ai.crawlers.x_com.production_crawler import ProductionXCrawler


class HomePageCrawler:
    """
    专门用于抓取X.com首页内容的爬虫
    """
    
    def __init__(self):
        self.crawler: Optional[ProductionXCrawler] = ProductionXCrawler()
    
    async def crawl_home_timeline(self):
        """
        抓取首页时间线内容并进行格式化
        """
        print("📖 开始抓取首页时间线内容...")
        
        try:
            # 检查crawler和page是否已初始化
            if not self.crawler or not self.crawler.page:
                print("❌ 爬虫或页面未初始化")
                return None
            
            # 导航到首页 - 使用更灵活的等待策略
            print("🌐 正在导航到首页...")
            
            # 尝试多种等待策略 - 使用有效的wait_until值
            navigation_strategies: List[tuple[Literal["load", "domcontentloaded", "networkidle"], int]] = [
                ("load", 10000),
                ("domcontentloaded", 10000),
                ("networkidle", 15000)
            ]
            
            navigation_success = False
            for wait_until, timeout in navigation_strategies:
                try:
                    print(f"   尝试使用 {wait_until} 策略...")
                    _ = await self.crawler.page.goto("https://x.com/home", wait_until=wait_until, timeout=timeout)
                    print(f"✅ 已到达首页 (使用 {wait_until} 策略)")
                    navigation_success = True
                    break
                except Exception as e:
                    print(f"   {wait_until} 策略失败: {e}")
                    continue
            
            if not navigation_success:
                print("⚠️  所有导航策略都失败，尝试直接访问...")
                try:
                    await self.crawler.page.goto("https://x.com/home", timeout=15000)
                    print("✅ 已到达首页 (直接访问)")
                except Exception as e:
                    print(f"❌ 导航到首页失败: {e}")
                    return None
            
            # 等待内容加载 - 使用更灵活的选择器
            print("⏳ 等待内容加载...")
            
            content_selectors = [
                '[data-testid="tweet"]',
                '[data-testid="primaryColumn"]',
                'article',
                '.tweet',
                '[role="article"]'
            ]
            
            content_loaded = False
            for selector in content_selectors:
                try:
                    await self.crawler.page.wait_for_selector(selector, timeout=10000)
                    print(f"✅ 内容已加载 (检测到选择器: {selector})")
                    content_loaded = True
                    break
                except:
                    continue
            
            if not content_loaded:
                print("⚠️  无法检测到内容选择器，等待固定时间...")
                await self.crawler.page.wait_for_timeout(5000)
                print("✅ 已等待固定时间")
            
            # 抓取推文内容
            tweets = await self._extract_tweets()
            print(f"✅ 成功抓取 {len(tweets)} 条推文")
            
            # 格式化输出
            formatted_content = self._format_content(tweets)
            
            return formatted_content
            
        except Exception as e:
            print(f"❌ 抓取首页内容出错: {e}")
            return None
    
    async def _extract_tweets(self) -> List[Dict[str, Any]]:
        """
        提取推文内容
        """
        if not self.crawler or not self.crawler.page:
            print("❌ 页面未初始化，无法提取推文")
            return []
        
        try:
            result = await self.crawler.page.evaluate(expression="""
            () => {
                const tweetElements = document.querySelectorAll('[data-testid="tweet"]');
                const tweets = [];
                
                for (const tweet of tweetElements) {
                    try {
                        // 提取推文文本
                        const textElement = tweet.querySelector('[data-testid="tweetText"]');
                        const text = textElement ? textElement.textContent.trim() : '';
                        
                        // 提取作者信息
                        const authorElement = tweet.querySelector('[data-testid="User-Name"]');
                        const author = authorElement ? authorElement.textContent.trim() : '';
                        
                        // 提取时间戳
                        const timeElement = tweet.querySelector('time');
                        const timestamp = timeElement ? timeElement.getAttribute('datetime') : '';
                        
                        // 提取互动数据（点赞、转发、回复等）
                        const likeButton = tweet.querySelector('[data-testid="like"]');
                        const retweetButton = tweet.querySelector('[data-testid="retweet"]');
                        const replyButton = tweet.querySelector('[data-testid="reply"]');
                        
                        const likes = likeButton ? likeButton.textContent.trim() : '0';
                        const retweets = retweetButton ? retweetButton.textContent.trim() : '0';
                        const replies = replyButton ? replyButton.textContent.trim() : '0';
                        
                        // 提取媒体内容（图片、视频）
                        const mediaElements = tweet.querySelectorAll('img, video');
                        const media = [];
                        
                        for (const mediaEl of mediaElements) {
                            if (mediaEl.src && !mediaEl.src.includes('data:')) {
                                media.push({
                                    type: mediaEl.tagName.toLowerCase(),
                                    src: mediaEl.src,
                                    alt: mediaEl.alt || ''
                                });
                            }
                        }
                        
                        if (text) {
                            tweets.push({
                                text: text,
                                author: author,
                                timestamp: timestamp,
                                engagement: {
                                    likes: likes,
                                    retweets: retweets,
                                    replies: replies
                                },
                                media: media,
                                url: window.location.href
                            });
                        }
                    } catch (e) {
                        console.error('Error parsing tweet:', e);
                    }
                    
                    // 限制抓取数量，避免性能问题
                    if (tweets.length >= 20) break;
                }
                
                return tweets;
            }
        """)
            
            return result or []
        except Exception as e:
            print(f"❌ 提取推文时出错: {e}")
            return []
    
    def _format_content(self, tweets: List[Dict[str, Any]]) -> str:
        """
        格式化抓取的内容
        """
        if not tweets:
            return "❌ 没有抓取到任何内容"
        
        formatted_output = []
        
        # 添加标题和时间戳
        formatted_output.append("=" * 80)
        formatted_output.append(f"X.COM 首页内容抓取报告")
        formatted_output.append(f"抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        formatted_output.append(f"抓取数量: {len(tweets)} 条推文")
        formatted_output.append("=" * 80)
        formatted_output.append("")
        
        # 格式化每条推文
        for i, tweet in enumerate(tweets, 1):
            formatted_output.append(f"📝 推文 #{i}")
            formatted_output.append(f"👤 作者: {tweet.get('author', '未知')}")
            formatted_output.append(f"⏰ 时间: {tweet.get('timestamp', '未知时间')}")
            formatted_output.append("")
            formatted_output.append(f"💬 内容:")
            formatted_output.append(f"   {tweet.get('text', '')}")
            formatted_output.append("")
            
            # 互动数据
            engagement = tweet.get('engagement', {})
            formatted_output.append(f"📊 互动数据:")
            formatted_output.append(f"   ❤️  点赞: {engagement.get('likes', '0')}")
            formatted_output.append(f"   🔄 转发: {engagement.get('retweets', '0')}")
            formatted_output.append(f"   💬 回复: {engagement.get('replies', '0')}")
            formatted_output.append("")
            
            # 媒体内容
            media = tweet.get('media', [])
            if media:
                formatted_output.append(f"🖼️  媒体内容 ({len(media)} 个):")
                for media_item in media:
                    formatted_output.append(f"   - {media_item['type'].upper()}: {media_item['src'][:50]}...")
                formatted_output.append("")
            
            formatted_output.append("-" * 80)
            formatted_output.append("")
        
        # 添加统计信息 - 简化计算，避免转换错误
        total_likes = sum(int(tweet.get('engagement', {}).get('likes', '0')) for tweet in tweets)
        total_retweets = sum(int(tweet.get('engagement', {}).get('retweets', '0')) for tweet in tweets)
        
        formatted_output.append("📈 统计摘要:")
        formatted_output.append(f"   总推文数: {len(tweets)}")
        formatted_output.append(f"   总点赞数: {total_likes}")
        formatted_output.append(f"   总转发数: {total_retweets}")
        formatted_output.append(f"   平均互动率: {(total_likes + total_retweets) / len(tweets):.1f} 每推文")
        
        return "\n".join(formatted_output)
    
    async def run(self) -> Optional[str]:
        """
        运行完整的抓取流程
        """
        print("🚀 开始X.com首页内容抓取")
        
        try:
            # 检查crawler是否初始化
            if not self.crawler:
                print("❌ 爬虫未初始化")
                return None
            
            # 登录
            print("🔐 正在登录...")
            await self.crawler.login()
            print("✅ 登录成功")
            
            # 再次检查页面是否初始化成功
            if not self.crawler.page:
                print("❌ 登录后页面仍未初始化")
                return None
            
            # 抓取首页内容
            content = await self.crawl_home_timeline()
            
            if content:
                # 保存到文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"x_home_content_{timestamp}.txt"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✅ 内容已保存到: {filename}")
                print("\n📋 抓取内容预览:")
                print("-" * 50)
                print(content[:500] + "..." if len(content) > 500 else content)
                
                return content
            else:
                print("❌ 抓取失败")
                return None
                
        except Exception as e:
            print(f"❌ 抓取过程中出错: {e}")
            return None
        finally:
            # 关闭浏览器
            if self.crawler:
                await self.crawler.close()
                print("🔒 浏览器已关闭")
            else:
                print("⚠️  无需关闭浏览器（爬虫未初始化）")


async def main():
    """
    主函数 - 运行首页内容抓取
    """
    crawler = HomePageCrawler()
    result = await crawler.run()
    
    if result:
        print("\n🎉 首页内容抓取完成！")
    else:
        print("\n💥 抓取失败，请检查错误信息")


if __name__ == "__main__":
    asyncio.run(main())