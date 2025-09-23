# crawl4ai/crawlers/x_com/output_handler.py

import json
from pathlib import Path
import aiofiles
from datetime import datetime
import asyncio
import os

from aiokafka import AIOKafkaProducer

async def save_batch_to_file(data: list, keyword: str, file_path: Path):
    """
    Saves a single batch of data to a specific file path.

    Args:
        data (list): The list of scraped data dictionaries for this batch.
        keyword (str): The search keyword associated with this data.
        file_path (Path): The absolute path to the output file for this batch.
    """
    if not data:
        print("No data to save for this batch.")
        return

    # The parent directory is now created by the main function.
    print(f"\n--- Saving batch of {len(data)} items to {file_path} ---")

    output_object = {
        "keyword": keyword,
        "result": data
    }

    try:
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(output_object, indent=4, ensure_ascii=False))
        print(f"Successfully saved batch to {file_path}")
    except Exception as e:
        print(f"Error saving batch to file: {e}")

async def send_to_kafka(producer: AIOKafkaProducer, topic: str, data: list, keyword: str):
    """
    Sends a batch of scraped data to a Kafka topic, with one message per item.
    """
    if not data:
        print("No data to send to Kafka.")
        return

    print(f"\n--- Sending {len(data)} individual messages to Kafka topic '{topic}' ---")
    tasks = []
    for item in data:
        message_object = {
            "keyword": keyword,
            "tweet_data": item
        }
        message = json.dumps(message_object, ensure_ascii=False).encode('utf-8')
        tasks.append(producer.send(topic, message))
    
    await asyncio.gather(*tasks)
    print(f"Successfully sent batch of {len(data)} messages to Kafka.")
