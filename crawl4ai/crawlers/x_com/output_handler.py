# crawl4ai/crawlers/x_com/output_handler.py

import json
from pathlib import Path
import aiofiles
from datetime import datetime

# Define the output directory relative to this file's location
OUTPUT_DIR = Path(__file__).parent / "out" / "scraped"

async def save_output(data: list, keyword: str):
    """
    A flexible output handler for scraped data.

    Saves data to a timestamped JSON file with a fixed prefix,
    and formats the output to include the search keyword.

    Args:
        data (list): The list of scraped data dictionaries to save.
        keyword (str): The search keyword used for this scrape (used in JSON content).
    """
    if not data:
        print("No data to save.")
        return

    # Ensure the output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # --- FIX: Generate a filename with a fixed prefix as requested ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"x_com_scrape_{timestamp}.json"
    file_path = OUTPUT_DIR / filename

    # The JSON object structure remains the same, including the keyword.
    output_object = {
        "keyword": keyword,
        "result": data
    }

    print(f"\n--- Saving {len(data)} items to {file_path} ---")

    try:
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
            await f.write(json.dumps(output_object, indent=4, ensure_ascii=False))
        
        print(f"Successfully saved data to {file_path}")
    except Exception as e:
        print(f"Error saving data to file: {e}")
