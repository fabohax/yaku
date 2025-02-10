import requests
import logging
import pandas as pd
from ta.trend import MACD
from datetime import datetime, timedelta, timezone
from telegram.ext import ApplicationBuilder
import asyncio
import time

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# OKX API Base URL
BASE_URL = "https://www.okx.com"

# Variables to track bullish crossover
bullish_cross_time = None
bullish_cross_price = None
signaled_19_min = False
signaled_50_percent = False


# Configure logging
logging.basicConfig(
    filename='logs/bot.log',
    filemode='a',  # Append mode
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  # Set logging level to INFO
)

# Example: Log a startup message
logging.info("Bot started successfully.")


# Function to fetch sufficient OHLCV data
def fetch_ohlcv(symbol="BTC-USDT", timeframe="1m", required_candles=200):
    try:
        endpoint = f"/api/v5/market/candles"
        limit_per_call = 100
        total_candles = 0
        all_candles = []
        
        now = datetime.now(timezone.utc)
        after = int((now - timedelta(minutes=required_candles * 2)).timestamp() * 1000)  # Ensure it covers enough range

        while total_candles < required_candles:
            params = {
                "instId": symbol,
                "bar": timeframe,
                "limit": str(limit_per_call),
                "after": after,
            }
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            candles = data.get("data", [])

            if not candles:
                break  # Stop if no more data is returned
            
            all_candles.extend(candles)
            total_candles += len(candles)
            after = int(pd.to_numeric(candles[-1][0]))  # Update 'after' to fetch newer data
            
            print(f"Fetched {len(candles)} more candles. Total so far: {total_candles}")

        # 🔹 Ensure we have the latest candles (OKX API returns newest first)
        all_candles.reverse()

        # 🔹 Define all columns
        column_names = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm']
        df = pd.DataFrame(all_candles, columns=column_names)

        # 🔹 Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(pd.to_numeric(df['timestamp']), unit='ms', utc=True)

        # 🔹 Convert relevant columns to float
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

        # 🔍 Debugging: Print timestamps to verify freshness
        print("Fetched OHLCV data timestamps (UTC):")
        print(df[['timestamp', 'close']].tail())  # Print last few rows for verification
        print(f"✅ Latest fetched close price: {df['close'].iloc[-1]}")
        print(df.head())  # First few rows
        print(df.tail())  # Last few rows

        return df.iloc[-required_candles:]  # Return the exact number of required candles

    except Exception as e:
        print(f"❌ Error fetching data: {e}")
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
        bullish_cross_time = datetime.now(timezone.utc)
        bullish_cross_price = df['close'].iloc[-1]
        signaled_19_min = False
        signaled_50_percent = False
        return f"📈 Bullish Crossover at {bullish_cross_price:.2f}"

    # Check for bearish crossover
    if df['macd'].iloc[-2] > df['signal'].iloc[-2] and df['macd'].iloc[-1] < df['signal'].iloc[-1]:
        return "📉 Bearish Crossover"

    # Check for 19-minute signal after bullish crossover
    if bullish_cross_time and not signaled_19_min:
        elapsed_time = datetime.now(timezone.utc) - bullish_cross_time
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


# Function to send starting alert via Telegram
async def send_started_alert():
    try:
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text='🤖 Bot started successfully.')
        print("✅ Started alert sent.")
    except Exception as e:
        print(f"❌ Error sending Telegram alert: {e}")

# Function to send alert when the bot ends
async def send_stopped_alert():
    try:
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="⚠️ Bot has stopped running.")
        print("✅ Stopped alert sent.")
    except Exception as e:
        print(f"❌ Error sending stopped alert: {e}")

# Function to send alert via Telegram
async def send_telegram_alert(message):
    try:
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        print("✅ Signal sent.")
    except Exception as e:
        print(f"❌ Error sending Telegram alert: {e}")

# Main loop
def run_bot(symbol="BTC-USDT"):
    # Create a single event loop for all async calls
    loop = asyncio.new_event_loop()
    
    try:
        loop.run_until_complete(send_started_alert())  # Send a start alert

        while True:
            try:
                # Log start of iteration
                logging.info("Starting new iteration...")

                # Fetch OHLCV data
                df = fetch_ohlcv(symbol)
                if not df.empty:
                    logging.info("Data fetched successfully. Proceeding with MACD calculation.")
                    
                    # Calculate MACD
                    df = calculate_macd(df)
                    logging.info("MACD calculated successfully.")

                    # Print the most recent MACD, signal, and histogram values
                    latest_macd = df.iloc[-1]['macd']
                    latest_signal = df.iloc[-1]['signal']
                    latest_hist = df.iloc[-1]['hist']
                    print(f"Latest MACD: {latest_macd:.6f}, Signal: {latest_signal:.6f}, Histogram: {latest_hist:.6f}")
                    logging.info(f"MACD: {latest_macd:.6f}, Signal: {latest_signal:.6f}, Histogram: {latest_hist:.6f}")

                    # Check for signals
                    signal = check_macd_signals(df)
                    if signal:
                        message = f"{datetime.now(timezone.utc)} - {signal}"
                        print(message)
                        logging.info(f"Signal detected: {message}")
                        
                        # Use the event loop to send Telegram alert
                        loop.run_until_complete(send_telegram_alert(message))
                        logging.info("Telegram alert sent.")

                # Print a point to indicate progress
                print(".", end="", flush=True)

                # Log completion of iteration
                logging.info("Iteration complete. Waiting for next minute.")
                time.sleep(60)  # Wait for the next minute
            except Exception as e:
                logging.error(f"Error during bot execution: {e}")
                print(f"Error: {e}")
                time.sleep(60)  # Wait before retrying
    except KeyboardInterrupt:
        logging.info("Bot stopped manually.")
        loop.run_until_complete(send_stopped_alert())  # Send a stopped alert
        print("\nBot stopped manually.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        loop.run_until_complete(send_stopped_alert())  # Send a stopped alert
        print(f"Unexpected error: {e}")
    finally:
        loop.close()
        logging.info("Event loop closed. Bot shutdown complete.")

# Start the bot
if __name__ == "__main__":
    run_bot()
