#!/bin/bash
source venv/bin/activate
nohup python3 bot.py > logs/bot.log 2>&1 &
echo "Bot started successfully!"
