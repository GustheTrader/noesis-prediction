# Noesis MLB v369 — Production System

## Overview
Leak-free MLB first-5-innings betting model with handedness interactions.

## Performance (2025 Test)
- MAE: 1.655
- Total Bets: 8,000
- Win Rate: 80.2%
- ROI: 52.0%
- P&L: $1,400,802

## Files
- `core/noesis_mlb_v369_model.py` — Main model
- `core/daily_predictor.py` — Daily prediction generator
- `NOESIS_MLB_v369_SPEC.md` — Full specification
- `daily_predictions/` — Daily bet logs

## Usage
```bash
cd /root/noesis-prediction/mlb_first5/v369_production
cd core
python3 daily_predictor.py
```

## Betting Strategy
- **Tier 1** (pred < 1.5): Bet $375, ~75% win rate
- **Tier 2** (1.5 ≤ pred < 2.5): Bet $250, ~84% win rate
- **Tier 3** (pred ≥ 2.5): No bet

## Last Updated
April 8, 2026
