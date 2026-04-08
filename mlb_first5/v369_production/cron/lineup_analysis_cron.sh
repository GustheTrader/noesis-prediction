#!/bin/bash
# lineup_analysis_cron.sh — Cron schedule for lineup analysis system
# Add these to crontab with: crontab -e

# ============================================================================
# NOESIS MLB v369 — LINEUP ANALYSIS CRON SCHEDULE
# ============================================================================
# Timezone: PT (Pacific Time)
# Early Games: ~4:00 PM PT (16:35 first pitch)
# Late Games: ~7:00 PM PT (19:00 first pitch)

# ============================================================================
# EARLY GAMES SCHEDULE (16:35 first pitch)
# ============================================================================

# 10:00 AM PT — Base predictions (no lineup data)
0 10 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/daily_predictor.py >> /var/log/noesis/early_base_$(date +\%Y\%m\%d).log 2>&1

# 11:00 AM PT — First lineup check (T-90 minutes)
0 11 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/fetch_confirmed_lineups.py >> /var/log/noesis/lineups_1100_$(date +\%Y\%m\%d).log 2>&1

# 11:15 AM PT — Second lineup check
15 11 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/fetch_confirmed_lineups.py >> /var/log/noesis/lineups_1115_$(date +\%Y\%m\%d).log 2>&1

# 11:30 AM PT — Lineup analysis (should have most by now)
30 11 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/analyze_platoon_matchups.py >> /var/log/noesis/analysis_1130_$(date +\%Y\%m\%d).log 2>&1

# 11:35 AM PT — Adjust predictions with lineup data
35 11 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/adjust_predictions.py --time early >> /var/log/noesis/adjust_early_$(date +\%Y\%m\%d).log 2>&1

# 11:45 AM PT — Send alerts for early games
45 11 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/send_alerts.py --time early >> /var/log/noesis/alerts_early_$(date +\%Y\%m\%d).log 2>&1

# 11:50 AM PT — Push to Google Sheets
50 11 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/push_to_sheets.py --time early >> /var/log/noesis/sheets_early_$(date +\%Y\%m\%d).log 2>&1

# ============================================================================
# LATE GAMES SCHEDULE (19:00+ first pitch)
# ============================================================================

# 2:00 PM PT — Check for late game lineups (T-90 from 19:00)
0 14 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/fetch_confirmed_lineups.py >> /var/log/noesis/lineups_1400_$(date +\%Y\%m\%d).log 2>&1

# 2:15 PM PT — Second check
15 14 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/fetch_confirmed_lineups.py >> /var/log/noesis/lineups_1415_$(date +\%Y\%m\%d).log 2>&1

# 2:30 PM PT — Late game lineup analysis
30 14 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/analyze_platoon_matchups.py >> /var/log/noesis/analysis_1430_$(date +\%Y\%m\%d).log 2>&1

# 2:35 PM PT — Adjust late game predictions
35 14 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/adjust_predictions.py --time late >> /var/log/noesis/adjust_late_$(date +\%Y\%m\%d).log 2>&1

# 2:45 PM PT — Send late game alerts
45 14 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/send_alerts.py --time late >> /var/log/noesis/alerts_late_$(date +\%Y\%m\%d).log 2>&1

# 2:50 PM PT — Push late games to sheets
50 14 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/push_to_sheets.py --time late >> /var/log/noesis/sheets_late_$(date +\%Y\%m\%d).log 2>&1

# ============================================================================
# POST-GAME RESULTS
# ============================================================================

# 8:00 PM PT — Fetch early game results
0 20 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/fetch_results.py --time early >> /var/log/noesis/results_early_$(date +\%Y\%m\%d).log 2>&1

# 11:00 PM PT — Fetch late game results
0 23 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/fetch_results.py --time late >> /var/log/noesis/results_late_$(date +\%Y\%m\%d).log 2>&1

# 11:30 PM PT — Update Google Sheets with results
30 23 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_results_sheets.py >> /var/log/noesis/update_sheets_$(date +\%Y\%m\%d).log 2>&1

# ============================================================================
# DAILY EVOLUTION (Run overnight)
# ============================================================================

# 1:00 AM PT — Run evolution engine (analyze losses, adapt thresholds)
0 1 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 noesis_evolve.py >> /var/log/noesis/evolve_$(date +\%Y\%m\%d).log 2>&1

# 2:00 AM PT — Auto-research for new features
0 2 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/auto_research.py >> /var/log/noesis/research_$(date +\%Y\%m\%d).log 2>&1

# 3:00 AM PT — Retrain model with new data (weekly on Sundays)
0 3 * * 0 cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/retrain_model.py >> /var/log/noesis/retrain_$(date +\%Y\%m\%d).log 2>&1

# ============================================================================
# LOG ROTATION (Weekly)
# ============================================================================

# Sunday 4 AM — Rotate logs
0 4 * * 0 cd /var/log/noesis && tar -czf noesis_logs_$(date -d "last week" +\%Y\%m\%d)_$(date +\%Y\%m\%d).tar.gz *.log && rm -f *.log
