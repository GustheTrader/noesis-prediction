#!/bin/bash
# results_update_cron.sh — Cron schedule to update game results 2.5 hours after start
# This runs update_game_results.py at specific times after each game starts
# All times are PT (Pacific)

# ============================================================================
# RESULT UPDATES — Run 2.5 hours after each game start time
# This ensures F5 results are available and final
# ============================================================================

# Morning Games (9:35 AM - 12:00 PM starts)
# 9:35 AM game → 12:05 PM update
5 12 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1205.log 2>&1

# 10:10 AM games → 12:40 PM update
40 12 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1240.log 2>&1

# 10:35 AM games → 1:05 PM update
5 13 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1305.log 2>&1

# 11:10 AM games → 1:40 PM update
40 13 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1340.log 2>&1

# 11:35 AM games → 2:05 PM update
5 14 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1405.log 2>&1

# Afternoon Games (12:00 PM - 3:00 PM starts)
# 12:07 PM game → 2:37 PM update
37 14 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1437.log 2>&1

# 12:10 PM game → 2:40 PM update
40 14 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1440.log 2>&1

# 12:45 PM game → 3:15 PM update
15 15 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1515.log 2>&1

# 1:05 PM game → 3:35 PM update
35 15 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1535.log 2>&1

# 1:07 PM game → 3:37 PM update
37 15 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1537.log 2>&1

# 1:10 PM game → 3:40 PM update
40 15 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1540.log 2>&1

# Evening Games (3:00 PM - 7:00 PM starts)
# 3:40 PM games → 6:10 PM update
10 18 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1810.log 2>&1

# 4:05 PM game → 6:35 PM update
35 18 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1835.log 2>&1

# 4:40 PM game → 7:10 PM update
10 19 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_1910.log 2>&1

# ============================================================================
# FINAL SUMMARY UPDATE — 8:00 PM PT (all games complete)
# ============================================================================
0 20 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/update_game_results.py >> /var/log/noesis/results_update_final.log 2>&1

# ============================================================================
# DAILY RECAP EMAIL — 9:00 PM PT (optional)
# ============================================================================
# 0 21 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/send_daily_recap.py >> /var/log/noesis/daily_recap.log 2>&1

# ============================================================================
# END OF DAY CLEANUP — 1:00 AM PT
# Archive today's results to 'yesterday' section, update running totals
# Prepare fresh sheet for next day
# ============================================================================
0 1 * * * cd /root/noesis-prediction/mlb_first5 && /root/mlb-env/bin/python3 v369_production/core/end_of_day_cleanup.py >> /var/log/noesis/end_of_day_cleanup.log 2>&1
