# bot_config.py
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
RAILWAY_RUN_AS_ROOT = os.getenv('RAILWAY_RUN_AS_ROOT', 'true')
RAILWAY_RUN_UID = int(os.getenv('RAILWAY_RUN_UID', 0))
REDIS_HOST = os.getenv('REDISHOST', 'monorail.proxy.rlwy.net')
REDIS_PORT = int(os.getenv('REDISPORT', 59006))
REDIS_PASSWORD = os.getenv('REDISPASSWORD', 'ATZNNXnHqiQboUZqJQPOHGBrwRbSUgjn')
REDIS_USER = os.getenv('REDISUSER', 'default')
REDIS_DB = 0
