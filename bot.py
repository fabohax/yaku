import requests
import logging
import pandas as pd
from ta.trend import MACD
from datetime import datetime, timezone, timedelta
from telegram.ext import ApplicationBuilder
import asyncio
import os

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# OKX API Base URL
BASE_URL = "https://www.okx.com"
CSV_FILE = "ohlcv_data.csv"

# Variables to track trade signals
bullish_cross_time = None
bullish_cross_price = None
sell_triggered = False  # To avoid redundant sell alerts

# Logging Configuration
logging.basicConfig(
    filename='logs/bot.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logging.info("Bot started successfully.")


# Function to fetch the latest OHLCV candle
def fetch_latest_candle(symbol="BTC-USDT", timeframe="1m"):
    try:
        endpoint = "/api/v5/market/candles"
        params = {
            "instId": symbol,
            "bar": timeframe,
            "limit": "1",
        }
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        candle = data.get("data", [])

        if not candle:
            return None
        
        timestamp, open_, high, low, close, volume, *_ = candle[0]
        timestamp = datetime.fromtimestamp(int(timestamp) / 1000, tz=timezone.utc)  # ✅ FIXED: Correct UTC handling

        candle_data = {
            "timestamp": timestamp,
            "open": float(open_),
            "high": float(high),
            "low": float(low),
            "close": float(close),
            "volume": float(volume),
        }

        # ✅ PRINT CANDLE EVERY TIME IT'S FETCHED
        print(f"📊 Candle Fetched: {timestamp} | Open: {open_} | High: {high} | Low: {low} | Close: {close} | Volume: {volume}")

        return candle_data

    except Exception as e:
        logging.error(f"Error fetching latest candle: {e}")
        return None


# Function to save new candle data locally
def save_candle_locally(new_candle):
    try:
        if not os.path.exists(CSV_FILE):
            df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
            df.to_csv(CSV_FILE, index=False)

        df = pd.read_csv(CSV_FILE)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        if not df[df["timestamp"] == new_candle["timestamp"].strftime("%Y-%m-%d %H:%M:%S")].empty:
            return False  # Candle already exists

        new_row = pd.DataFrame([new_candle])  # ✅ FIXED: Ensure correct structure before concatenation
        new_row["timestamp"] = pd.to_datetime(new_row["timestamp"])

        df = pd.concat([df, new_row], ignore_index=True)

        df = df.iloc[-200:]  # Keep last 200 records

        df.to_csv(CSV_FILE, index=False)

        logging.info(f"📊 New candle saved: {new_candle['timestamp']} - Close: {new_candle['close']}")
        return True

    except Exception as e:
        logging.error(f"Error saving candle: {e}")
        return False


# Function to calculate MACD
def calculate_macd(df):
    macd = MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
    df['macd'] = macd.macd()
    df['signal'] = macd.macd_signal()
    df['hist'] = macd.macd_diff()
    return df


# Function to check MACD buy/sell signals
def check_macd_signals():
    global bullish_cross_time, bullish_cross_price, sell_triggered

    try:
        if not os.path.exists(CSV_FILE):
            return None

        df = pd.read_csv(CSV_FILE)
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        if len(df) < 30:
            logging.warning(f"Not enough candles available (received {len(df)}).")
            return None

        df = calculate_macd(df)

        last_timestamp = df["timestamp"].iloc[-1]
        last_price = df["close"].iloc[-1]

        # Check for Bullish MACD Crossover (Buy Signal)
        if df['macd'].iloc[-3] < df['signal'].iloc[-3] and df['macd'].iloc[-2] > df['signal'].iloc[-2]:
            bullish_cross_time = last_timestamp
            bullish_cross_price = last_price
            sell_triggered = False
            print(f"⭕ Bullish Crossover detected at {bullish_cross_price:.2f}")
            return f"📊 Bullish Crossover at {bullish_cross_price:.2f}"

        # Check for Sell Conditions
        if bullish_cross_time and not sell_triggered:
            elapsed_time = (last_timestamp - bullish_cross_time).total_seconds() / 60  # Minutes since buy signal

            # 1️⃣ Sell after 19 minutes of MACD crossover
            if elapsed_time >= 19:
                sell_triggered = True
                return f"⏳ Sell signal: 19 min after MACD buy signal at {last_price:.2f}"

            # 2️⃣ Sell after Bearish MACD Crossover
            if df['macd'].iloc[-3] > df['signal'].iloc[-3] and df['macd'].iloc[-2] < df['signal'].iloc[-2]:
                sell_triggered = True
                return f"📉 Bearish MACD crossover - Sell at {last_price:.2f}"

            # 3️⃣ Sell after 15 minutes if price remains within ±0.1%
            price_range = bullish_cross_price * 0.001
            if elapsed_time >= 15 and (bullish_cross_price - price_range) <= last_price <= (bullish_cross_price + price_range):
                sell_triggered = True
                return f"⏳ Sell signal: 15 min passed, price still in ±0.1% range at {last_price:.2f}"

            # 4️⃣ Sell if price increases by more than 0.5%
            if last_price >= bullish_cross_price * 1.005:
                sell_triggered = True
                return f"📈 Price reached +0.5% profit at {last_price:.2f} - Sell now!"

    except Exception as e:
        logging.error(f"Error in signal detection: {e}")

    return None


# Function to send Telegram alerts
async def send_telegram_alert(message):
    try:
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f"✅ {message} Sent successfully.")
    except Exception as e:
        logging.error(f"❌ Error in Telegram alert: {e}")


# Function to send bot status alerts
async def send_start_stop_alert(status="start"):
    try:
        message = "🤖 Bot started successfully." if status == "start" else "⚠️ Bot has stopped running."
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        await app.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f"{message} sent.")
    except Exception as e:
        logging.error(f"❌ Error sending {status} alert: {e}")


# Main bot loop
async def run_bot(symbol="BTC-USDT"):
    try:
        await send_start_stop_alert("start")

        while True:
            new_candle = fetch_latest_candle(symbol)
            if new_candle:
                saved = save_candle_locally(new_candle)
                if saved:
                    signal = check_macd_signals()
                    if signal:
                        await send_telegram_alert(f"{datetime.now(timezone.utc)} - {signal}")

            await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("\nBot stopped manually.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        await send_start_stop_alert("stop")


if __name__ == "__main__":
    asyncio.run(run_bot())
