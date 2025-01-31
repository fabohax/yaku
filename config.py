import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OKX API Credentials
OKX_API_KEY = os.getenv("OKX_API_KEY")
OKX_API_SECRET = os.getenv("OKX_API_SECRET")
OKX_API_PASSWORD = os.getenv("OKX_API_PASSWORD")

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Trading Parameters
SYMBOL = "BTC/USDT"  # Default trading pair
TIMEFRAME = "1m"     # Timeframe for MACD analysis
MACD_FAST = 12       # Fast period for MACD
MACD_SLOW = 26       # Slow period for MACD
MACD_SIGNAL = 9      # Signal line period

# Logging
LOG_FILE = "logs/bot.log"

# Notification Settings
ENABLE_TELEGRAM_ALERTS = True