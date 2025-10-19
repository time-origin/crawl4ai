# crawl4ai/crawlers/x_com/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- X.com Credentials ---
# It's recommended to use environment variables for sensitive data.
X_USERNAME = os.getenv("X_USERNAME")
X_PASSWORD = os.getenv("X_PASSWORD")

# --- Proxy Settings ---
# Example: "http://your_proxy_server:port"
PROXY_SERVER = os.getenv("PROXY_SERVER")

# --- Kafka Configuration ---
# [修正] 兼容 KAFKA_BOOTSTRAP_SERVERS 和 KAFKA_BROKER_URL 两个变量名
# 优先使用 KAFKA_BOOTSTRAP_SERVERS，如果不存在，则尝试 KAFKA_BROKER_URL
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BROKER_URL")

# The main topic to which scraped tweet data will be sent.
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "x_com_scraped_data")

# The topic for task control messages (e.g., TASK_INIT).
KAFKA_TASK_TOPIC = os.getenv("KAFKA_TASK_TOPIC", "task_control_topic")

# --- Authentication File Path ---
# Allows overriding the auth state file path via environment variable.
# Useful for Docker deployments where the file is mounted at a specific location.
AUTH_JSON_PATH = os.getenv("AUTH_JSON_PATH")

# --- [修正] 从环境变量获取抓取失败时的最大重试次数 ---
# 定义了在首次尝试抓取一条推文的回复失败后，额外进行的重试次数。
# 值为 "1" 表示总共会尝试 1 (首次) + 1 (重试) = 2 次。
# 值为 "0" 表示不进行任何重试。
# 环境变量需要设置为字符串，程序内部会转换为整数。
MAX_RETRIES_ON_FAILURE = int(os.getenv("MAX_RETRIES_ON_FAILURE", 1))
