# MLB Daily Predictions — Setup Guide

## Overview
Automated daily predictions for MLB First-5 Team Total UNDER 2.5 betting.

## Files
- `daily_predict.py` — Main prediction script
- `daily_predictions.sh` — Wrapper script for cron
- `daily_bets/` — Output folder for daily bet logs

## How to Run

### Manual (One-time)
```bash
cd /root/noesis-prediction/mlb_first5
/root/mlb-env/bin/python daily_predict.py
```

### Automated (Cron)
Since cron isn't available in this environment, run manually at:
- **10:00 AM PT / 1:00 PM ET** — Morning lineups
- **5:00 PM PT / 8:00 PM ET** — Late game updates

### Expected Output
```
==========================================
QUALIFYING BETS — 2026-04-08
==========================================
Threshold: Predicted < 1.0 runs allowed
Bet: Opponent Team Total UNDER 2.5
Stake: $250 per bet

✅ FOUND 3 QUALIFYING BETS:

Bet 1:
  Pitcher: Corbin Burnes
  Team: Baltimore Orioles (Home)
  Time: 2026-04-08T18:05Z
  Predicted runs allowed: 0.85
  Pitcher ERA: 2.83
  ➜ BET: Opponent Team Total UNDER 2.5
```

## Paper Trading Workflow

### Daily Steps:
1. **Morning (10 AM PT)**: Run `daily_predict.py`
2. **Review qualifying bets** in console or `daily_bets/YYYY-MM-DD_bets.txt`
3. **Paper trade**: Log virtual bets in `PAPER_TRADING_LOG.md`
4. **Evening**: Check results, update log

### Bet Criteria:
- Pitcher predicted < 1.0 runs allowed
- Opponent Team Total UNDER 2.5
- Stake: $250
- Odds: -110

## Model Performance (Historical)
- **Win rate**: 79.8%
- **Expected value**: +$131 per bet
- **ROI**: 52.3%
- **Max drawdown**: 67% (recovered)
- **Max losing streak**: 5

## Alternative: Systemd Timer
If cron unavailable, use systemd:

```bash
# Create service file
sudo tee /etc/systemd/system/mlb-predict.service << EOF
[Unit]
Description=MLB Daily Predictions

[Service]
Type=oneshot
ExecStart=/root/mlb-env/bin/python /root/noesis-prediction/mlb_first5/daily_predict.py
User=root
EOF

# Create timer
sudo tee /etc/systemd/system/mlb-predict.timer << EOF
[Unit]
Description=Run MLB predictions daily

[Timer]
OnCalendar=*-*-* 10:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable mlb-predict.timer
sudo systemctl start mlb-predict.timer
```

## Troubleshooting

### "No games found"
- ESPN lineups not set yet (too early)
- Try again at 11 AM - 1 PM ET
- Check ESPN.com for confirmed starters

### "No historical data for pitcher"
- Rookie or new pitcher
- Use 2025 averages as proxy
- Or skip the bet (safer)

### Model predicts > 1.0 for everyone
- Early season, small sample sizes
- Use conservative threshold (1.5 instead of 1.0)
- Wait for more 2026 data

## Success Metrics (Paper Trading)
Track weekly:
- Bets placed
- Win rate (target: 75%+)
- Profit/loss
- Max drawdown

Goal: 75%+ win rate for 2 weeks before live betting.
