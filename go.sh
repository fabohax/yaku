#!/bin/bash
python3 -m venv venv &
source venv/bin/activate &
nohup python3 bot.py > logs/bot.log 2>&1 &
echo "Bot started successfully!"
