# crawl4ai/crawlers/x_com/output_handler.py

import json
from pathlib import Path
import aiofiles
from datetime import datetime
import os
from aiokafka import AIOKafkaProducer

async def save_batch_to_file(data: list, keyword: str, run_dir: Path, batch_num: int):
    """
    Saves a single batch of data to its own numbered JSON file inside a run-specific directory.
    """
    if not data:
        print(f"Batch {batch_num}: No data to save.")
        return

    # The run directory is created by the main process
    filename = f"batch_{batch_num}.json"
    file_path = run_dir / filename

    output_object = {
        "keyword": keyword,
        "batch_number": batch_num,
        "item_count": len(data),
        "result": data
    }

    print(f"--- Saving batch {batch_num} ({len(data)} items) to {file_path} ---")
    try:
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(output_object, indent=4, ensure_ascii=False))
        print(f"Successfully saved batch {batch_num}.")
    except Exception as e:
        print(f"Error saving batch {batch_num} to file: {e}")

async def send_batch_to_kafka(data: list, keyword: str, producer: AIOKafkaProducer, topic: str, batch_num: int):
    """
    Sends a batch of scraped data to a Kafka topic, one message per item.
    """
    if not data:
        print(f"Batch {batch_num}: No data to send to Kafka.")
        return

    print(f"\n--- Sending batch {batch_num} ({len(data)} items) to Kafka topic '{topic}' ---")
    try:
        for item in data:
            # Add the keyword to each individual item for context
            message_object = {
                "keyword": keyword,
                "scraped_item": item
            }
            message = json.dumps(message_object, ensure_ascii=False).encode('utf-8')
            await producer.send(topic, message)
        # Wait for all messages in the batch to be sent
        await producer.flush()
        print(f"Successfully sent batch {batch_num} to Kafka.")
    except Exception as e:
        print(f"Error sending batch {batch_num} to Kafka: {e}")
