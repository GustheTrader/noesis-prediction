# NOESIS MLB v369 — AGENT DIRECTORY

Complete list of all agents, their duties, and execution schedules.

---

## 🕕 PRE-GAME AGENTS (6:00 AM PT)

### Agent: `pitcher_validator.py`
**Duty:** Triple-check pitcher validation (Source #1: ESPN API)
**Cron Time:** `0 6 * * *` (6:00 AM PT)
**Runtime:** ~30 seconds

**Actions:**
1. Polls ESPN API for confirmed starting pitchers
2. Returns status: ✅ CONFIRMED or ⏳ PENDING
3. Saves to: `/tmp/pitcher_validation_YYYYMMDD.json`

**Triple Validation:**
- ✅ Automated ESPN API check
- ⏳ Manual MLB.com verify (next step)
- ⏳ Manual Twitter verify (next step)

---

### Agent: `fetch_confirmed_lineups.py`
**Duty:** Poll ESPN for lineups every 15 minutes
**Cron Time:** 
- `0 6 * * *` (6:00 AM)
- `15 6 * * *` (6:15 AM)
- `30 10 * * *` (10:30 AM for late games)
**Runtime:** ~45 seconds

**Actions:**
1. Fetches roster data from ESPN `/events/{id}/rosters`
2. Extracts batting order with L/R handedness
3. Identifies starting pitchers
4. Saves to: `daily_predictions/YYYYMMDD_confirmed_lineups.json`

**Lineup Data Captured:**
- Batter name and position
- L/R/S handedness
- Batting order (1-9)
- Pitcher name and throwing hand
- Confirmation timestamp

---

### Agent: `bet_confirmation_protocol.py`
**Duty:** Triple-check checklist and manual verification
**Cron Time:** `30 6 * * *` (6:30 AM PT)
**Runtime:** ~10 seconds

**Actions:**
1. Displays verification checklist
2. Waits for manual confirmation
3. Cross-references 3 sources:
   - ✅ ESPN API (automated)
   - ✅ MLB.com (manual verify)
   - ✅ Team Twitter (manual verify)
4. Outputs: CONFIRMED or DO NOT BET

**Triple Validation Complete When:**
- All 3 sources match pitcher name
- Lineup confirmed by team
- No last-minute changes detected

---

### Agent: `analyze_platoon_matchups.py`
**Duty:** Calculate L/R platoon advantage
**Cron Time:** `35 6 * * *` (6:35 AM PT)
**Runtime:** ~15 seconds

**Actions:**
1. Loads confirmed lineups
2. Calculates platoon advantage %
3. Determines lineup strength score
4. Generates adjustment recommendations:
   - >60% advantage = +0.4 runs
   - 30-60% = neutral
   - <30% = -0.4 runs

**Lineup Strength Formula:**
```
strength_score = 1.0 + (platoon_advantage - 0.5) * 0.8 + (avg_ops - 0.730) * 0.5
```

---

### Agent: `generate_todays_picks.py`
**Duty:** Generate paper trade picks with confirmed data
**Cron Time:** `0 7 * * *` (7:00 AM PT) or MANUAL
**Runtime:** ~2 minutes

**Actions:**
1. Trains model on 2021-2023 data
2. Matches confirmed pitchers to historical stats
3. Generates predictions for each game
4. Assigns tiers (ELITE/TIER 1/TIER 2)
5. Outputs: `daily_predictions/YYYYMMDD_paper_trades.csv`

**Data Validation:**
- ✅ Pitcher confirmed via ESPN
- ✅ Historical stats in database
- ✅ Game time verified (PT)
- ❌ Unknown pitchers excluded

---

### Agent: `sync_todays_picks_to_sheets.py`
**Duty:** Push picks to Google Sheets
**Cron Time:** `30 7 * * *` (7:30 AM PT)
**Runtime:** ~20 seconds

**Actions:**
1. Loads CSV from `generate_todays_picks.py`
2. Builds clean sheet format
3. Updates Google Sheets via API
4. Clears old data, writes fresh

**Sheet Structure:**
- Row 1: Title with date
- Row 2: Subtitle
- Row 4: Headers
- Rows 5-13: Picks
- Rows 15-18: Summary
- Rows 20-24: Tier breakdown

---

## 🕐 IN-GAME AGENTS (+2.5 Hours After Each Game)

### Agent: `update_game_results.py`
**Duty:** Fetch actual F5 scores and update sheet
**Cron Time:** Multiple (see schedule below)
**Runtime:** ~30 seconds

**Cron Schedule:**
| Game Start | Update Time | Cron |
|------------|-------------|------|
| 9:35 AM | 12:05 PM | `5 12 * * *` |
| 10:10 AM | 12:40 PM | `40 12 * * *` |
| 10:35 AM | 1:05 PM | `5 13 * * *` |
| 11:10 AM | 1:40 PM | `40 13 * * *` |
| 11:35 AM | 2:05 PM | `5 14 * * *` |
| 12:07 PM | 2:37 PM | `37 14 * * *` |
| 12:10 PM | 2:40 PM | `40 14 * * *` |
| 12:45 PM | 3:15 PM | `15 15 * * *` |
| 1:05 PM | 3:35 PM | `35 15 * * *` |
| 1:07 PM | 3:37 PM | `37 15 * * *` |
| 1:10 PM | 3:40 PM | `40 15 * * *` |
| 3:40 PM | 6:10 PM | `10 18 * * *` |
| 4:05 PM | 6:35 PM | `35 18 * * *` |
| 4:40 PM | 7:10 PM | `10 19 * * *` |
| **All Games** | **8:00 PM** | `0 20 * * *` |

**Actions:**
1. Fetches game status from ESPN
2. Calculates F5 runs from linescores
3. Determines win/loss (Under 2.5)
4. Calculates P&L (-120 odds)
5. Updates Google Sheets columns H & I
6. Updates summary totals

**Data Validation:**
- ✅ Only counts completed innings
- ✅ Waits until 5th inning reached
- ✅ Uses final score if game complete

---

## 🌙 POST-GAME AGENTS (1:00 AM PT)

### Agent: `end_of_day_cleanup.py`
**Duty:** Archive results and reset for next day
**Cron Time:** `0 1 * * *` (1:00 AM PT)
**Runtime:** ~1 minute

**Actions:**
1. Loads yesterday's picks and results
2. Archives to "yesterday" section
3. Updates running totals:
   - Cumulative YTD P&L
   - Overall win rate
   - Total days tracked
4. Creates fresh template for today
5. Clears and rebuilds sheet

**Archive Section Includes:**
- All picks with final F5 scores
- Day summary (wins/losses/P&L)
- Win rate for the day
- Timestamp

---

## 🔧 EVOLUTION AGENTS (Overnight)

### Agent: `noesis_evolve.py`
**Duty:** Run full evolution pipeline
**Cron Time:** `0 2 * * *` (2:00 AM PT)
**Runtime:** ~5 minutes

**Actions:**
1. Analyzes yesterday's losses
2. Adapts threshold boundaries
3. Triggers auto-research
4. Queues v370 candidates

**Evolution Pipeline:**
- Daily loss analysis
- Weekly threshold optimization
- Monthly auto-research
- Quarterly vNext deployment

---

### Agent: `adaptive_thresholds.py`
**Duty:** RL-based threshold optimization
**Called by:** `noesis_evolve.py`
**Runtime:** ~3 minutes

**Actions:**
1. Grid search for optimal tier boundaries
2. Tests different confidence thresholds
3. Maximizes Sharpe ratio
4. Updates tier definitions

---

### Agent: `auto_research.py`
**Duty:** Discover new features
**Cron Time:** `0 3 * * *` (3:00 AM PT)
**Runtime:** ~10 minutes

**Actions:**
1. Analyzes feature importance
2. Tests hypotheses:
   - Weather effects
   - Travel/rest days
   - Park factors
   - Lineup strength vs hand
3. Scores v370 candidates
4. Generates research report

---

## 📋 MANUAL AGENTS (On-Demand)

### Agent: `manual_lookup.py`
**Duty:** Quick pitcher stat lookup
**Usage:** `python3 manual_lookup.py "Pitcher Name"`

**Actions:**
1. Searches database for pitcher
2. Returns: ERA, WHIP, K/9, recent performance
3. Shows last 5 starts

---

### Agent: `telegram_alerts.py`
**Duty:** Send bet alerts to Telegram
**Usage:** `python3 telegram_alerts.py --tier elite`

**Actions:**
1. Formats bet message
2. Sends to chat ID 7803920476
3. Includes: pitcher, stake, odds, confidence

---

## 🎯 TRIPLE VALIDATION WORKFLOW

### Pre-Bet Validation (6:00-7:00 AM PT)

```
6:00 AM — Agent: pitcher_validator.py
   └─ ESPN API check (automated)
   
6:15 AM — Agent: fetch_confirmed_lineups.py
   └─ Lineup data with L/R handedness
   
6:30 AM — Agent: bet_confirmation_protocol.py
   ├─ Cross-check ESPN API
   ├─ Manual: Verify MLB.com
   └─ Manual: Check Team Twitter
   
6:35 AM — Agent: analyze_platoon_matchups.py
   └─ Calculate platoon advantage
   
7:00 AM — Agent: generate_todays_picks.py
   └─ Generate with VALIDATED data only
```

**Validation Complete When:**
- ✅ ESPN API confirms pitcher
- ✅ MLB.com confirms lineup
- ✅ Team Twitter confirms no changes
- ✅ Platoon analysis complete
- ✅ Prediction generated with validated data

---

## 📊 AGENT SUMMARY TABLE

| Agent | Type | Cron Time | Duty |
|-------|------|-----------|------|
| pitcher_validator.py | Pre-game | 6:00 AM | ESPN API validation |
| fetch_confirmed_lineups.py | Pre-game | 6:00, 6:15 AM | Lineup polling |
| bet_confirmation_protocol.py | Pre-game | 6:30 AM | Triple-check |
| analyze_platoon_matchups.py | Pre-game | 6:35 AM | L/R analysis |
| generate_todays_picks.py | Pre-game | 7:00 AM | Generate picks |
| sync_todays_picks_to_sheets.py | Pre-game | 7:30 AM | Update sheet |
| update_game_results.py | In-game | +2.5 hrs | Fetch F5 results |
| end_of_day_cleanup.py | Post-game | 1:00 AM | Archive & reset |
| noesis_evolve.py | Evolution | 2:00 AM | Full evolution |
| adaptive_thresholds.py | Evolution | 2:30 AM | Threshold opt |
| auto_research.py | Evolution | 3:00 AM | Feature research |
| manual_lookup.py | Manual | On-demand | Pitcher lookup |
| telegram_alerts.py | Manual | On-demand | Send alerts |

---

## 🚨 CRITICAL VALIDATION POINTS

### Must Pass Before Betting:
1. **Pitcher Confirmed** (ESPN API)
2. **Lineup Confirmed** (ESPN roster endpoint)
3. **Triple-Check Complete** (ESPN + MLB.com + Twitter)
4. **Platoon Analysis** (L/R matchups calculated)

### Data Quality Checks:
- Pitcher in database? (Known stats)
- Game time verified? (PT conversion correct)
- No TBD pitchers? (Confirmed starters only)
- Lineup strength calculated? (Platoon advantage %)

---

## 📁 FILE LOCATIONS

```
v369_production/
├── core/
│   ├── pitcher_validator.py
│   ├── fetch_confirmed_lineups.py
│   ├── bet_confirmation_protocol.py
│   ├── analyze_platoon_matchups.py
│   ├── generate_todays_picks.py
│   ├── sync_todays_picks_to_sheets.py
│   ├── update_game_results.py
│   ├── end_of_day_cleanup.py
│   ├── noesis_evolve.py
│   ├── adaptive_thresholds.py
│   ├── auto_research.py
│   ├── manual_lookup.py
│   └── telegram_alerts.py
├── cron/
│   ├── lineup_analysis_cron_CORRECTED.sh
│   ├── results_update_cron.sh
│   └── README.md
└── daily_predictions/
    └── YYYYMMDD_paper_trades.csv
```

---

## 🎯 START TIMES REFERENCE

| Slot | First Game | Last Game |
|------|------------|-----------|
| **Morning** | 9:35 AM PT | 11:35 AM PT |
| **Afternoon** | 12:07 PM PT | 1:10 PM PT |
| **Evening** | 3:40 PM PT | 4:40 PM PT |

**Triple Validation Window:** 6:00-7:00 AM PT (before first pitch)

---

_Last Updated: April 8, 2026_
