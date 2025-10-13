import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 判断程序是否被 PyInstaller 打包
if getattr(sys, 'frozen', False):
    # 如果是打包后的可执行文件，则 .env 文件应该在可执行文件旁边
    base_path = Path(sys.executable).parent
else:
    # 如果是在正常的开发环境中运行，则 .env 文件在项目根目录
    # 当前文件路径: .../crawl4ai/crawl4ai/crawlers/x_com/config.py
    # 项目根目录: .../crawl4ai/
    base_path = Path(__file__).parent.parent.parent.parent

env_path = base_path / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment variables from: {env_path}")
else:
    print(f"Warning: .env file not found at {env_path}. Using system environment variables.")

# Kafka 相关配置
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BROKER_URL")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")

# X.com 凭证
X_USERNAME = os.getenv("X_USERNAME")
X_PASSWORD = os.getenv("X_PASSWORD")

# 代理服务器
PROXY_SERVER = os.getenv("PROXY_SERVER")
