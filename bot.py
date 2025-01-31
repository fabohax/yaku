import requests
import pandas as pd
from ta.trend import MACD
from datetime import datetime, timedelta
from telegram.ext import ApplicationBuilder
import asyncio
import time

from config import OKX_API_KEY, OKX_API_SECRET, OKX_API_PASSWORD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# OKX API Base URL
BASE_URL = "https://www.okx.com"

# Variables to track bullish crossover
bullish_cross_time = None
bullish_cross_price = None
signaled_19_min = False
signaled_50_percent = False


# Function to fetch OHLCV data
def fetch_ohlcv(symbol="BTC-USDT", timeframe="1m", limit=100):
    try:
        endpoint = f"/api/v5/market/candles"
        params = {
            "instId": symbol,
            "bar": timeframe,
            "limit": str(limit),
        }
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for HTTP issues
        data = response.json()
        candles = data.get("data", [])
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])

        # Convert timestamp to datetime, explicitly cast to numeric
        df['timestamp'] = pd.to_datetime(pd.to_numeric(df['timestamp']), unit='ms', utc=True)
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        
        print(df.tail(1))  # Print the last row of the fetched data for visibility

        return df

    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()


# Function to calculate MACD
def calculate_macd(df):
    macd = MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
    df['macd'] = macd.macd()
    df['signal'] = macd.macd_signal()
    df['hist'] = macd.macd_diff()
    return df


# Function to detect MACD events
def check_macd_signals(df):
    global bullish_cross_time, bullish_cross_price, signaled_19_min, signaled_50_percent

    if len(df) < 2:
        return None

    # Check for bullish crossover
    if df['macd'].iloc[-2] < df['signal'].iloc[-2] and df['macd'].iloc[-1] > df['signal'].iloc[-1]:
        bullish_cross_time = datetime.now()
        bullish_cross_price = df['close'].iloc[-1]
        signaled_19_min = False
        signaled_50_percent = False
        return f"📈 Bullish Crossover at {bullish_cross_price:.2f}"

    # Check for bearish crossover
    if df['macd'].iloc[-2] > df['signal'].iloc[-2] and df['macd'].iloc[-1] < df['signal'].iloc[-1]:
        return "📉 Bearish Crossover"

    # Check for 19-minute signal after bullish crossover
    if bullish_cross_time and not signaled_19_min:
        elapsed_time = datetime.now() - bullish_cross_time
        if elapsed_time >= timedelta(minutes=19):
            signaled_19_min = True
            return "⏳ 19 Minutes After Bullish Crossover - Selling Signal"

    # Check for 0.50% above bullish crossing price
    if bullish_cross_price and not signaled_50_percent:
        current_price = df['close'].iloc[-1]
        target_price = bullish_cross_price * 1.005  # 0.50% above crossing price
        if current_price >= target_price:
            signaled_50_percent = True
            return f"🎯 Price Reached 0.50% Above Bullish Crossing Price at {current_price:.2f}"

    return None


# Function to send alert via Telegram
async def send_telegram_alert(message):
    try:
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("✅ Telegram alert sent.")
    except Exception as e:
        print(f"❌ Error sending Telegram alert: {e}")


# Main loop
def run_bot(symbol="BTC-USDT"):
    while True:
        try:
            df = fetch_ohlcv(symbol)
            if not df.empty:
                df = calculate_macd(df)
                signal = check_macd_signals(df)

                if signal:
                    message = f"{datetime.now()} - {signal}"
                    print(message)
                    asyncio.run(send_telegram_alert(message))

            # Print a point to indicate progress
            print(".", end="", flush=True)
            time.sleep(60)  # Wait for the next minute
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)


# Start the bot
if __name__ == "__main__":
    run_bot()
