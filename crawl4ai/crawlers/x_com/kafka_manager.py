# crawl4ai/crawlers/x_com/kafka_manager.py

import json
import asyncio
from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from aiokafka.errors import TopicAlreadyExistsError

async def ensure_topic_exists(bootstrap_servers: str, topic_name: str):
    """
    Checks if a Kafka topic exists, and creates it if it does not.
    """
    admin_client = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers)
    try:
        await admin_client.start()
        existing_topics = await admin_client.list_topics()
        if topic_name in existing_topics:
            print(f"Topic '{topic_name}' already exists.")
            return True
        
        print(f"Topic '{topic_name}' not found. Attempting to create it...")
        new_topic = NewTopic(name=topic_name, num_partitions=1, replication_factor=1)
        await admin_client.create_topics([new_topic])
        print(f"Successfully created topic '{topic_name}'.")
        return True

    except TopicAlreadyExistsError:
        print(f"Topic '{topic_name}' was created by another process just now.")
        return True
    except Exception as e:
        print(f"An error occurred while ensuring Kafka topic exists: {e}")
        return False
    finally:
        if admin_client:
            await admin_client.close()

async def send_to_kafka(producer: AIOKafkaProducer, topic: str, data: list, keyword: str, key_prefix: str):
    """
    Sends a batch of scraped data to a Kafka topic, with one message per item,
    using a prefixed ID as the message key.

    Args:
        producer: An already started AIOKafkaProducer instance.
        topic (str): The Kafka topic to send messages to.
        data (list): The list of scraped data dictionaries.
        keyword (str): The search keyword associated with this data.
        key_prefix (str): The prefix to use for the Kafka message key.
    """
    if not data:
        return

    print(f"\n--- Sending {len(data)} individual messages to Kafka topic '{topic}' ---")
    tasks = []
    for item in data:
        # --- FIX: Add ID extraction and construct the new key ---
        # full_url = item.get("url", "")
        # tweet_id = full_url.split("/")[-1] if "/status/" in full_url else ""
        #
        # # Add the new ID field to the item itself
        # item['id'] = tweet_id
        tweet_id = item.get("id", "")
        message_object = {
            "keyword": keyword,
            "tweet_data": item
        }
        message_value = json.dumps(message_object, ensure_ascii=False).encode('utf-8')
        
        # Construct the key with the prefix, e.g., "x.com:123456789"
        message_key = f"{key_prefix}:{tweet_id}".encode('utf-8')
        
        print(f"Sending message with key: {message_key.decode('utf-8')}")
        tasks.append(producer.send(topic, value=message_value, key=message_key))
    
    await asyncio.gather(*tasks)
    print(f"Successfully sent batch of {len(data)} messages to Kafka.")
