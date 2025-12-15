# crawl4ai/middlewares/kafka/producer.py

import json
import asyncio
from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError
from typing import List, Dict, Any

# 这个文件是项目的中央Kafka生产中间件。
# 它被设计成通用、健壮且易于使用，并考虑到了在Docker/Ubuntu生产环境中运行的需求。

async def ensure_topic_exists(bootstrap_servers: str, topic_name: str, **kwargs):
    """
    检查Kafka主题是否存在，如果不存在则创建它。
    [增强] 现在会将额外的连接参数传递给AdminClient。
    """
    admin_client = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers, **kwargs)
    try:
        await admin_client.start()
        existing_topics = await admin_client.list_topics()
        if topic_name in existing_topics:
            print(f"主题 '{topic_name}' 已存在。")
            return True
        
        print(f"未找到主题 '{topic_name}'。正在尝试创建...")
        new_topic = NewTopic(name=topic_name, num_partitions=1, replication_factor=1)
        await admin_client.create_topics([new_topic])
        print(f"成功创建主题 '{topic_name}'。")
        return True

    except TopicAlreadyExistsError:
        print(f"主题 '{topic_name}' 刚刚被另一个进程创建。")
        return True
    except Exception as e:
        print(f"确保Kafka主题存在时发生错误: {e}")
        return False
    finally:
        if admin_client:
            await admin_client.close()

class KafkaMiddleware:
    """
    一个封装了Kafka生产者逻辑的中间件类，简化爬虫中的调用。
    它通过`async with`语法管理生产者的生命周期，并支持高级连接参数。
    """
    def __init__(self, bootstrap_servers: str, **kwargs):
        """
        初始化Kafka中间件。

        Args:
            bootstrap_servers (str): Kafka broker的地址，例如 "localhost:9092"。
            **kwargs: 其他所有传递给AIOKafkaProducer的参数。
                      这对于生产环境中的SASL认证和SSL加密至关重要。
                      例如:
                      security_protocol="SASL_PLAINTEXT",
                      sasl_mechanism="PLAIN",
                      sasl_plain_username="your_user",
                      sasl_plain_password="your_password"
        """
        if not bootstrap_servers:
            raise ValueError("Kafka bootstrap_servers 地址不能为空。")
        self.bootstrap_servers = bootstrap_servers
        self.connection_kwargs = kwargs  # 存储所有额外的连接参数
        self.producer = None

    async def __aenter__(self):
        """支持异步上下文管理器 (async with)"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            **self.connection_kwargs
        )
        await self.producer.start()
        print(f"✅ KafkaMiddleware: 生产者已启动，连接到 {self.bootstrap_servers}。")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """在退出上下文时自动关闭生产者"""
        if self.producer:
            print("⏳ KafkaMiddleware: 正在停止生产者...")
            await self.producer.stop()
            print("✅ KafkaMiddleware: 生产者已停止。")

    async def ensure_topic(self, topic_name: str):
        """确保主题存在"""
        return await ensure_topic_exists(self.bootstrap_servers, topic_name, **self.connection_kwargs)

    async def send(self, topic: str, messages: List[Dict[str, Any]]):
        """
        异步发送一批消息。

        Args:
            topic (str): 目标主题。
            messages (list): 消息字典的列表。每个字典必须包含 'key' 和 'value'。
        """
        if not self.producer:
            raise ConnectionError("生产者未启动。请在 'async with' 块中使用此方法。")
        
        if not messages:
            return

        print(f"\n--- 正在向Kafka主题 '{topic}' 异步发送 {len(messages)} 条消息 ---")
        tasks = []
        for msg in messages:
            try:
                key = str(msg['key']).encode('utf-8')
                value = json.dumps(msg['value'], ensure_ascii=False).encode('utf-8')
                tasks.append(self.producer.send(topic, value=value, key=key))
            except KeyError as e:
                print(f"错误: 消息字典缺少必要的键: {e}。消息: {msg}")
            except (TypeError, OverflowError) as e:
                print(f"错误: 消息值无法被JSON序列化: {e}。消息: {msg.get('value')}")

        if tasks:
            await asyncio.gather(*tasks)
            print(f"--- 成功发送了一批 {len(tasks)} 条消息。 ---")

    async def send_and_wait(self, topic: str, key: str, value: Dict[str, Any]):
        """
        发送一条消息并等待确认，确保其被成功发送。
        这对于关键的信令消息（如任务初始化）非常有用。

        Args:
            topic (str): 目标主题。
            key (str): 消息的键。
            value (dict): 可以被JSON序列化的消息内容。
        """
        if not self.producer:
            raise ConnectionError("生产者未启动。请在 'async with' 块中使用此方法。")

        print(f"--- 正在向Kafka主题 '{topic}' 同步发送单条关键消息 ---")
        try:
            key_bytes = str(key).encode('utf-8')
            value_bytes = json.dumps(value, ensure_ascii=False).encode('utf-8')
            
            print(f"    键: {key}")
            print(f"    值: {value}")

            await self.producer.send_and_wait(topic, value=value_bytes, key=key_bytes)
            print("--- 关键消息已成功发送并确认。 ---")
        except Exception as e:
            print(f"--- 🛑 发送关键消息时失败: {e} ---")
            raise
