#!/bin/bash
# lineup_analysis_cron_CORRECTED.sh — CORRECTED cron schedule with proper PT times
# ALL TIMES ARE PACIFIC TIME (PT)
# ESPN shows times in UTC (add 7 hours for PT during PDT)
# 
# CORRECTION APPLIED: Games start at 9:35 AM PT, not 4:35 PM!

# ============================================================================
# EARLY GAMES SCHEDULE (9:35 AM - 1:05 PM PT First Pitches)
# ============================================================================

# 6:00 AM PT — Check ESPN for confirmed lineups (T-3.5 hours before 9:35 AM games)
# This is when ESPN typically confirms starters
0 6 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/pitcher_validator.py >> /var/log/noesis/lineup_check_0600_$(date +\%Y\%m\%d).log 2>&1

# 6:15 AM PT — Second lineup check
15 6 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/fetch_confirmed_lineups.py >> /var/log/noesis/lineups_0615_$(date +\%Y\%m\%d).log 2>&1

# 6:30 AM PT — Triple-verify pitchers (ESPN + MLB.com cross-check)
30 6 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/bet_confirmation_protocol.py >> /var/log/noesis/confirm_0630_$(date +\%Y\%m\%d).log 2>&1

# 7:00 AM PT — Final prediction adjustments with confirmed lineups
0 7 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/adjust_predictions.py --time early >> /var/log/noesis/adjust_early_$(date +\%Y\%m\%d).log 2>&1

# 7:15 AM PT — Send Telegram alerts for early games
15 7 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/send_alerts.py --time early >> /var/log/noesis/alerts_early_$(date +\%Y\%m\%d).log 2>&1

# 7:30 AM PT — Push to Google Sheets
30 7 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/push_to_sheets.py --time early >> /var/log/noesis/sheets_early_$(date +\%Y\%m\%d).log 2>&1

# 9:35 AM PT — First pitch (SD @ PIT earliest game)
# 10:10 AM PT — KC @ CLE
# 10:35 AM PT — MIL @ BOS
# 11:10 AM PT — BAL @ CHW
# 11:35 AM PT — SEA @ TEX

# ============================================================================
# LATE GAMES SCHEDULE (12:07 PM - 4:05 PM PT First Pitches)
# ============================================================================

# 10:00 AM PT — Check for late game lineups (T-2 hours before 12:07 games)
0 10 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/fetch_confirmed_lineups.py >> /var/log/noesis/lineups_1000_$(date +\%Y\%m\%d).log 2>&1

# 10:30 AM PT — Analyze late game matchups
30 10 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/analyze_platoon_matchups.py >> /var/log/noesis/analysis_1030_$(date +\%Y\%m\%d).log 2>&1

# 11:00 AM PT — Adjust late game predictions
0 11 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/adjust_predictions.py --time late >> /var/log/noesis/adjust_late_$(date +\%Y\%m\%d).log 2>&1

# 11:15 AM PT — Send late game alerts
15 11 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/send_alerts.py --time late >> /var/log/noesis/alerts_late_$(date +\%Y\%m\%d).log 2>&1

# 11:30 AM PT — Push late games to sheets
30 11 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/push_to_sheets.py --time late >> /var/log/noesis/sheets_late_$(date +\%Y\%m\%d).log 2>&1

# 12:07 PM PT — LAD @ TOR first pitch (first late game)
# 12:10 PM PT — HOU @ COL
# 12:45 PM PT — PHI @ SF
# 1:05 PM PT — STL @ WSH
# 1:07 PM PT — ATL @ LAA

# ============================================================================
# POST-GAME RESULTS
# ============================================================================

# 2:00 PM PT — Fetch early game results
0 14 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/fetch_results.py >> /var/log/noesis/results_early_$(date +\%Y\%m\%d).log 2>&1

# 5:00 PM PT — Fetch late game results
0 17 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/fetch_results.py >> /var/log/noesis/results_late_$(date +\%Y\%m\%d).log 2>&1

# 6:00 PM PT — Update Google Sheets with results
0 18 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_results_sheets.py >> /var/log/noesis/update_sheets_$(date +\%Y\%m\%d).log 2>&1

# ============================================================================
# DAILY EVOLUTION (Overnight)
# ============================================================================

# 1:00 AM PT — Run evolution engine
0 1 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 noesis_evolve.py >> /var/log/noesis/evolve_$(date +\%Y\%m\%d).log 2>&1

# 2:00 AM PT — Auto-research
0 2 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/auto_research.py >> /var/log/noesis/research_$(date +\%Y\%m\%d).log 2>&1

# 3:00 AM PT — Weekly retrain (Sundays)
0 3 * * 0 cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/retrain_model.py >> /var/log/noesis/retrain_$(date +\%Y\%m\%d).log 2>&1

# 4:00 AM PT — Log rotation (Sundays)
0 4 * * 0 cd /var/log/noesis && tar -czf noesis_logs_$(date -d "last week" +\%Y\%m\%d)_$(date +\%Y\%m\%d).tar.gz *.log 2>/dev/null; rm -f *.log
