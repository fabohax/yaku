import requests
import pandas as pd
from datetime import datetime, timezone

# OKX API Base URL
BASE_URL = "https://www.okx.com"

# Function to fetch the latest OHLCV candle
def fetch_latest_candle(symbol="BTC-USDT", timeframe="1m"):
    try:
        endpoint = f"/api/v5/market/candles"
        params = {
            "instId": symbol,
            "bar": timeframe,
            "limit": "1",  # Fetch only the latest candle
        }
        url = f"{BASE_URL}{endpoint}"
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for HTTP issues
        data = response.json()
        candles = data.get("data", [])

        if not candles:
            print("⚠️ No data received from OKX.")
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'volCcy', 'volCcyQuote', 'confirm'])
        df['timestamp'] = pd.to_datetime(pd.to_numeric(df['timestamp']), unit='ms', utc=True)
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

        # Print latest data
        print("\n📊 Latest Candle Data:")
        print(df[['timestamp', 'open', 'high', 'low', 'close', 'volume']])

        return df

    except Exception as e:
        print(f"❌ Error fetching latest candle: {e}")
        return pd.DataFrame()

# Run the test
if __name__ == "__main__":
    latest_candle_df = fetch_latest_candle()

    if not latest_candle_df.empty:
        print("\n✅ Successfully fetched latest candle.")
