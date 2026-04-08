#!/bin/bash
# daily_workflow.sh — Complete daily betting workflow
# 
# Steps:
# 1. Scrape today's games
# 2. Check for qualifying pitchers
# 3. Verify lineups
# 4. Send confirmed bets to Telegram
# 5. Log to paper trading journal

set -e

echo "=========================================="
echo "MLB Daily Workflow — $(date)"
echo "=========================================="

# Setup
source /root/mlb-env/bin/activate
cd /root/noesis-prediction/mlb_first5

TODAY=$(date +%Y-%m-%d)

echo "Step 1: Fetching today's games..."
python3 daily_predict.py

if [ -f "daily_bets/${TODAY}_bets.txt" ]; then
    echo "✅ Found qualifying bets"
    
    echo "Step 2: Lineup confirmation..."
    # This would check MLB.com for confirmed starters
    # For now, manual confirmation required
    
    echo "Step 3: Sending to Telegram..."
    # When bets are confirmed, send alert
    # python3 telegram_alerts.py --bet-file confirmed_bet.json
    
    echo "Step 4: Logging to paper trading..."
    # Append to PAPER_TRADING_LOG.md
    
else
    echo "ℹ️  No qualifying bets today"
fi

echo "=========================================="
echo "Workflow complete: $(date)"
echo "=========================================="
