# NOESIS MLB v369 — LINEUP ANALYSIS CRON SCHEDULE
## Complete Implementation Guide

---

## 📅 DAILY TIMELINE (PT Timezone)

### EARLY GAMES (~4:00 PM PT First Pitch)

| Time | PT | Script | Action | Output |
|------|-----|--------|--------|--------|
| 10:00 AM | `0 10 * * *` | `daily_predictor.py` | Base predictions (no lineup) | Initial tiers |
| 11:00 AM | `0 11 * * *` | `fetch_confirmed_lineups.py` | **1st lineup check** | T-90 min |
| 11:15 AM | `15 11 * * *` | `fetch_confirmed_lineups.py` | **2nd lineup check** | Update |
| 11:30 AM | `30 11 * * *` | `analyze_platoon_matchups.py` | Calculate platoon advantage | L/R matchups |
| 11:35 AM | `35 11 * * *` | `adjust_predictions.py --time early` | **Adjust predictions** | Final tiers |
| 11:45 AM | `45 11 * * *` | `send_alerts.py --time early` | Send Telegram alerts | Confirmed bets |
| 11:50 AM | `50 11 * * *` | `push_to_sheets.py --time early` | Update Google Sheets | Row 2-30 |
| 4:35 PM | `35 16 * * *` | **First pitch early games** | — | — |
| 8:00 PM | `0 20 * * *` | `fetch_results.py --time early` | Fetch early results | Actual scores |

### LATE GAMES (~7:00 PM PT First Pitch)

| Time | PT | Script | Action | Output |
|------|-----|--------|--------|--------|
| 2:00 PM | `0 14 * * *` | `fetch_confirmed_lineups.py` | **1st late check** | T-90 min |
| 2:15 PM | `15 14 * * *` | `fetch_confirmed_lineups.py` | **2nd late check** | Update |
| 2:30 PM | `30 14 * * *` | `analyze_platoon_matchups.py` | Analyze late matchups | L/R data |
| 2:35 PM | `35 14 * * *` | `adjust_predictions.py --time late` | **Adjust late games** | Final tiers |
| 2:45 PM | `45 14 * * *` | `send_alerts.py --time late` | Send late alerts | Confirmed bets |
| 2:50 PM | `50 14 * * *` | `push_to_sheets.py --time late` | Update Google Sheets | Updated rows |
| 7:00 PM | `0 19 * * *` | **First pitch late games** | — | — |
| 11:00 PM | `0 23 * * *` | `fetch_results.py --time late` | Fetch late results | Final scores |
| 11:30 PM | `30 23 * * *` | `update_results_sheets.py` | Update sheets with results | Complete |

---

## 🔄 DAILY EVOLUTION (Overnight)

| Time | PT | Script | Action |
|------|-----|--------|--------|
| 1:00 AM | `0 1 * * *` | `noesis_evolve.py` | Analyze losses, adapt thresholds |
| 2:00 AM | `0 2 * * *` | `auto_research.py` | Discover new features |
| 3:00 AM | `0 3 * * 0` | `retrain_model.py` | Weekly retrain (Sundays) |
| 4:00 AM | `0 4 * * 0` | Log rotation | Archive weekly logs |

---

## 📊 EXPECTED RESULTS

### Early Games (4:35 PM PT First Pitch)

**Sample Timeline:**

```
10:00 AM — Base Predictions:
  Paul Skenes (PIT): 0.64 runs → ELITE ($500)
  
11:30 AM — Lineup Confirmed (CHC vs Skenes):
  CHC Lineup: 7 RHH, 2 LHH vs RHP
  Platoon Advantage: 22% (unfavorable for hitters)
  Strength Score: 0.85 (WEAK)
  
11:35 AM — Adjusted Prediction:
  Skenes: 0.64 × 0.85 = 0.54 runs → STAY ELITE
  
11:45 AM — Alert Sent:
  "ELITE BET CONFIRMED: Skenes $500"
```

### Late Games (7:07 PM PT First Pitch)

**Sample Timeline:**

```
2:30 PM — Late Matchup Analysis:
  LAD @ TOR: Glasnow vs TOR
  TOR Lineup: 6 LHH, 3 RHH vs RHP
  Platoon Advantage: 67% (strong for hitters)
  Strength Score: 1.18 (STRONG)
  
2:35 PM — Adjusted Prediction:
  Glasnow: 0.72 × 1.18 = 0.85 runs → TIER 1 (was ELITE)
  
2:45 PM — Alert Sent:
  "TIER 1 BET: Glasnow $375 (lineup downgrade)"
```

---

## 🎯 LINEUP DATA FLOW

```
┌─────────────────┐
│  ESPN API       │ ← Roster endpoint (L/R handedness)
│  (T-90 min)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ fetch_confirmed_lineups │ ← Poll every 15 min
│     .py                 │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ analyze_platoon_        │ ← Calculate L/R matchups
│     matchups.py         │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ adjust_predictions.py   │ ← Apply lineup factor
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ send_alerts.py          │ → Telegram alerts
│ push_to_sheets.py       │ → Google Sheets
└─────────────────────────┘
```

---

## 📁 FILE STRUCTURE

```
v369_production/daily_predictions/
├── 20260408_base_predictions.json          (10:00 AM)
├── 20260408_confirmed_lineups.json         (11:00-11:30 AM)
├── 20260408_platoon_analysis.json          (11:30 AM)
├── 20260408_adjusted_early.json            (11:35 AM)
├── 20260408_adjusted_late.json             (14:35 PM)
├── 20260408_results_early.json             (20:00 PM)
├── 20260408_results_late.json              (23:00 PM)
└── 20260408_final_summary.json             (23:30 PM)
```

---

## ⚙️ INSTALLATION

### 1. Create Log Directory
```bash
sudo mkdir -p /var/log/noesis
sudo chown $(whoami) /var/log/noesis
```

### 2. Install Cron Jobs
```bash
cd /root/noesis-prediction/mlb_first5
crontab v369_production/cron/lineup_analysis_cron.sh
```

### 3. Verify Installation
```bash
crontab -l  # List all cron jobs
grep CRON /var/log/syslog  # Check cron execution
```

---

## 🔔 ALERT TIMING

### Early Game Alerts (11:45 AM PT)
- 3 Elite picks (if lineups favorable)
- 5-7 Tier 1 picks
- Stake: ~$3,500

### Late Game Alerts (2:45 PM PT)
- Updated based on confirmed lineups
- May differ from early analysis
- Stake: ~$2,500

---

## 📊 EXPECTED IMPROVEMENT

| Metric | v369 Base | v370 + Lineups | Delta |
|--------|-----------|----------------|-------|
| Win Rate | 62.4% | 65-67% | +2.6-4.6% |
| ROI | 19.1% | 22-24% | +3-5% |
| False Elite | 15% | 8% | -7% |

---

## 🚨 MANUAL OVERRIDE

If cron fails, run manually:

```bash
# Early games
cd /root/noesis-prediction/mlb_first5
python3 v369_production/core/fetch_confirmed_lineups.py
python3 v369_production/core/analyze_platoon_matchups.py
python3 v369_production/core/adjust_predictions.py --time early

# Late games
python3 v369_production/core/fetch_confirmed_lineups.py
python3 v369_production/core/analyze_platoon_matchups.py
python3 v369_production/core/adjust_predictions.py --time late
```

---

## 📞 SUPPORT

**Location:** `/root/noesis-prediction/mlb_first5/v369_production/`
**Logs:** `/var/log/noesis/`
**Sheets:** https://docs.google.com/spreadsheets/d/1IGgDsEXV2DyYNy5b5g2nau63ktjFFVBFRcuKMTH3FiY
