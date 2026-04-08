# NOESIS MLB v369 — Complete Cron Schedule

## Overview

This directory contains all cron schedules for the NOESIS MLB betting system.

## Files

| File | Purpose |
|------|---------|
| `lineup_analysis_cron_CORRECTED.sh` | Daily lineup checks, predictions, alerts |
| `results_update_cron.sh` | Game result updates (2.5 hrs after each game) |

---

## Daily Timeline (All Times PT)

### 🌅 MORNING (Pre-Game)

```
6:00 AM  — Check ESPN for confirmed lineups
6:15 AM  — Second lineup check
6:30 AM  — Triple-verify pitchers (ESPN + MLB.com + Twitter)
7:00 AM  — Generate predictions with confirmed pitchers
7:15 AM  — Send Telegram alerts
7:30 AM  — Push picks to Google Sheets
```

### 📊 RESULT UPDATES (2.5 Hours After Each Game)

```
12:05 PM — Update 9:35 AM game results
12:40 PM — Update 10:10 AM game results
1:05 PM  — Update 10:35 AM game results
1:40 PM  — Update 11:10 AM game results
2:05 PM  — Update 11:35 AM game results
2:37 PM  — Update 12:07 PM game results
2:40 PM  — Update 12:10 PM game results
3:15 PM  — Update 12:45 PM game results
3:35 PM  — Update 1:05 PM game results
3:37 PM  — Update 1:07 PM game results
3:40 PM  — Update 1:10 PM game results
6:10 PM  — Update 3:40 PM game results
6:35 PM  — Update 4:05 PM game results
7:10 PM  — Update 4:40 PM game results
8:00 PM  — Final summary update (all games)
```

### 🌙 OVERNIGHT (Evolution & Cleanup)

```
1:00 AM  — END OF DAY CLEANUP
           - Archive today's results to "yesterday" section
           - Update running totals (YTD P&L, win rate)
           - Create fresh sheet for next day
           
2:00 AM  — Run evolution engine (analyze losses)
3:00 AM  — Auto-research for new features
4:00 AM  — Weekly model retrain (Sundays only)
5:00 AM  — Log rotation (Sundays only)
```

---

## Installation

```bash
# Create log directory
sudo mkdir -p /var/log/noesis
sudo chown $(whoami) /var/log/noesis

# Install cron jobs
crontab v369_production/cron/lineup_analysis_cron_CORRECTED.sh
crontab v369_production/cron/results_update_cron.sh

# Verify
crontab -l
```

---

## Result Update Logic

The `update_game_results.py` script:

1. Fetches actual F5 scores from ESPN API
2. Compares to predicted runs allowed
3. Calculates win/loss (Under 2.5 = win)
4. Updates Google Sheets columns I & J:
   - Column I: F5 Result (actual runs allowed)
   - Column J: P/L ($ profit/loss)
5. Updates summary section with totals

---

## Why 2.5 Hours?

- Average MLB game: ~3 hours
- F5 completes around inning 5-6
- 2.5 hours ensures games are final or in late innings
- F5 scores available from ESPN linescores

---

## Manual Trigger

If cron is not available, run manually:

```bash
# Update results now
cd /root/noesis-prediction/mlb_first5
python3 v369_production/core/update_game_results.py

# Or for specific game
cd /root/noesis-prediction/mlb_first5  
python3 v369_production/core/update_game_results.py --game "MIL @ BOS"
```

---

## End of Day Workflow

At **1:00 AM PT** (after all games complete):

1. **Archive yesterday's results**
   - Move picks with F5 scores to "yesterday" section
   - Add day summary (wins, losses, P&L)

2. **Update running totals**
   - Cumulative P&L (YTD)
   - Overall win rate
   - Days tracked

3. **Create fresh daily template**
   - New header with today's date
   - Empty pick rows (ready for 6 AM generation)
   - Empty summary section

4. **Preserve archive**
   - All previous days remain in archive section
   - Scroll down to see full history

## File Locations

```
v369_production/cron/
├── lineup_analysis_cron_CORRECTED.sh  # Pre-game schedule
├── results_update_cron.sh              # Post-game updates
└── README.md                           # This file

v369_production/core/
├── generate_todays_picks.py           # Create picks
├── sync_todays_picks_to_sheets.py     # Push to Sheets
├── update_game_results.py             # Fetch & update results
└── end_of_day_cleanup.py              # Archive & reset for next day
```
