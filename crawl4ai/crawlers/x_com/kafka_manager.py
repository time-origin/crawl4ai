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

async def send_to_kafka(producer: AIOKafkaProducer, topic: str, data: list, keyword: str, original_task_id: int):
    """
    Sends a batch of scraped data to a Kafka topic, with one message per item,
    using a prefixed ID as the message key.

    Args:
        producer: An already started AIOKafkaProducer instance.
        topic (str): The Kafka topic to send messages to.
        data (list): The list of scraped data dictionaries.
        keyword (str): The search keyword associated with this data.
        original_task_id (int): The ID of the original task.
    """
    if not data:
        return

    print(f"\n--- Sending {len(data)} individual messages to Kafka topic '{topic}' ---")
    tasks = []
    for item in data:
        tweet_id = item.get("id", "")
        message_object = {
            "original_task_id": original_task_id,
            "keyword": keyword,
            "tweet_data": item
        }
        message_value = json.dumps(message_object, ensure_ascii=False).encode('utf-8')
        
        message_key = f"{original_task_id}:{tweet_id}".encode('utf-8')
        
        print(f"Sending message with key: {message_key.decode('utf-8')}")
        tasks.append(producer.send(topic, value=message_value, key=message_key))
    
    await asyncio.gather(*tasks)
    print(f"Successfully sent batch of {len(data)} messages to Kafka.")

# [ADD] New function to send the task initialization message
async def send_task_init_message(producer: AIOKafkaProducer, topic: str, original_task_id: int, total_tweets: int):
    """
    Sends a single TASK_INIT message to Kafka to signal the start and scale of a job.

    Args:
        producer: An already started AIOKafkaProducer instance.
        topic (str): The Kafka topic for task control messages.
        original_task_id (int): The unique ID for the entire task.
        total_tweets (int): The total number of tweets that will be processed.
    """
    message_object = {
        "type": "TASK_INIT",
        "original_task_id": original_task_id,
        "total_tweets": total_tweets
    }
    message_value = json.dumps(message_object, ensure_ascii=False).encode('utf-8')
    
    # Use the original_task_id as the key to ensure messages for the same task are ordered.
    message_key = str(original_task_id).encode('utf-8')
    
    print(f"--- Sending TASK_INIT message to topic '{topic}' ---")
    print(f"    Key: {message_key.decode('utf-8')}")
    print(f"    Value: {message_value.decode('utf-8')}")
    
    try:
        # Using send_and_wait to ensure this critical message is sent before proceeding.
        await producer.send_and_wait(topic, value=message_value, key=message_key)
        print("--- Successfully sent TASK_INIT message. ---")
    except Exception as e:
        print(f"--- 🛑 Failed to send TASK_INIT message: {e} ---")
