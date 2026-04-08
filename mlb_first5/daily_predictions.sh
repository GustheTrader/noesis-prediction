#!/bin/bash
# daily_predictions.sh — Daily MLB predictions cron job
# Runs at 10:00 AM PT (1:00 PM ET) daily
# Outputs: Today's qualifying bets for paper trading

set -e

echo "=========================================="
echo "MLB Daily Predictions — $(date)"
echo "=========================================="

# Activate virtual environment
source /root/mlb-env/bin/activate

# Change to project directory
cd /root/noesis-prediction/mlb_first5

# Run daily scraper and predictor
python3 daily_predict.py

# Log completion
echo "✅ Predictions complete: $(date)"
echo "Check: /root/noesis-prediction/mlb_first5/daily_bets/$(date +%Y-%m-%d)_bets.txt"
