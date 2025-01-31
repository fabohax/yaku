<p>
  <img src="yaku.png" alt="yaku-bot" width="400" style="display: block; margin: auto;">
</p>

# yaku 

**yaku** is a high-performance cryptocurrency trading signaler bot built in Python. It follows a custom strategy called **Strato**, which is based on **MACD crossovers** and specific timing rules to maximize profitability.

---

## **Strato Strategy - Explained 🚀**

The **Strato** strategy is a systematic approach based on **MACD crossovers** with additional confirmations:

1. **Bullish MACD Crossover**  
   - A signal is triggered when the **MACD line crosses above the signal line**.
   - This marks the start of an uptrend, where the bot begins monitoring price movement.

2. **19-Minute Confirmation**  
   - If **19 minutes** pass after the bullish crossover and price remains above the crossover level, a selling signal is issued.
   - This prevents false signals caused by small fluctuations.

3. **0.50% Target Price**  
   - If the price rises **0.50% above the bullish crossover level**, the bot issues an alert.
   - This ensures profit-taking at a reasonable gain before potential reversals.

4. **Bearish MACD Crossover**  
   - If the **MACD line crosses below the signal line**, a bearish crossover is detected.
   - This serves as an early warning to reconsider market conditions.

---

## **Project Structure 📂**

```
yaku/
│── bot.py               # Main signaler bot script
│── config.py            # Configuration loader for API keys and bot settings
│── go.sh                # Bash script to run the bot
│── README.md            # Project documentation
│── .env                 # Environment variables (ignored by Git)
│── requirements.txt     # Python dependencies
│── logs/                # Directory to store bot logs
```

---

## **Installation & Setup 🔧**

### **1. Install Python 🐍**
Make sure Python 3.9 or higher is installed on your system. You can check with:
```sh
python3 --version
```

---

### **2. Clone the Repository 📂**
```sh
git clone https://github.com/fabohax/yaku.git
cd yaku
```

---

### **3. Set Up Dependencies 📦**
Install the required dependencies:
```sh
pip install -r requirements.txt
```

---

### **4. Set Up Environment Variables 🔑**
Create a `.env` file and add your **OKX API keys** and **Telegram bot credentials**:

```env
OKX_API_KEY=your_api_key
OKX_API_SECRET=your_api_secret
OKX_API_PASSWORD=your_password
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

### **5. Run the Bot Using `go.sh` 🚀**
You can use the `go.sh` script to run the bot in the background and log the output:

Make the script executable:
```sh
chmod +x go.sh
```

Run the script:
```sh
./go.sh
```

The bot will start and log its output to `logs/bot.log`.

---

## **Deployment on a Server (VPS) 💻**
To run yaku 24/7, deploy it on a **VPS** or cloud server:

1. **Install Python and Set Up Virtual Environment**
   ```sh
   sudo apt update && sudo apt install python3 python3-venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Using `go.sh`**
   ```sh
   ./go.sh
   ```

3. **Using `systemd` for Auto-Restart**
   Create a new service file:
   ```sh
   sudo nano /etc/systemd/system/yaku.service
   ```
   Add the following:
   ```ini
   [Unit]
   Description=yaku.signals
   After=network.target

   [Service]
   ExecStart=/path/to/your/yaku/go.sh
   Restart=always
   User=your_user

   [Install]
   WantedBy=multi-user.target
   ```

   Enable and start the service:
   ```sh
   sudo systemctl enable yaku
   sudo systemctl start yaku
   ```

---

## **Future Improvements 🚧**
- **Web Dashboard:** Monitor real-time signals.
- **Backtesting Module:** Test the strategy on historical data.

---

## **Contributing 🤝**
Pull requests and issues are welcome! If you'd like to contribute, feel free to fork the repo and submit PRs.

---

<br/>
<sub>⚠ Warning: yaku is designed primarily for BTC/USDT due to its high liquidity and optimal volatility performance. Usage on other pairs may result in inconsistent signals. Always conduct your own risk assessment before trading. 🚀📊</sub>
