#!/usr/bin/env python3
"""model_v2.py — MLB first-5 model WITH pitcher handedness"""
import numpy as np
from pathlib import Path

# Load v2 data
DATA = Path("data/processed/model_data_v2.csv")
import csv
rows = []
with open(DATA) as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

F = [
    "pitcher_era","pitcher_whip","pitcher_k9","pitcher_bb9","pitcher_kbb",
    "pitcher_gbfb","pitcher_k_pct","pitcher_ip",
    "is_home","pitcher_days_rest",
    "opp_avg_runs_allowed","opp_avg_first5_allowed",
]
D = ["pitcher_exp_er_5ip","pitcher_exp_h_5ip","pitcher_exp_bb_5ip",
     "pitcher_exp_k_5ip","predicted_f5","edge_vs_opp"]
NEW = ["is_lhp"]  # ← new feature
ALL_F = F + D + NEW

X, y = [], []
for r in rows:
    try:
        feat = [float(r.get(c,"") or 0) for c in ALL_F]
        t = float(r["first_5_runs_allowed"])
        X.append(feat); y.append(t)
    except: pass

X, y = np.array(X), np.array(y)
print(f"Shape: {X.shape}, Target mean={y.mean():.2f}")

years = np.array([int(r["year"]) for r in rows])
test_mask = years == 2025
X_train, X_test = X[~test_mask], X[test_mask]
y_train, y_test = y[~test_mask], y[test_mask]
print(f"Train: {len(X_train)} | Test: {len(X_test)}")

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

print("\n[*] GradientBoosting with handedness...")
gb = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, min_samples_leaf=20, random_state=42)
gb.fit(X_train, y_train)

te_pred = gb.predict(X_test)
mae = mean_absolute_error(y_test, te_pred)
rmse = np.sqrt(mean_squared_error(y_test, te_pred))
print(f"  Test MAE: {mae:.3f} (was 1.640 without handedness)")
print(f"  Test RMSE: {rmse:.3f}")

# Feature importance
imp = sorted(zip(ALL_F, gb.feature_importances_), key=lambda x: -x[1])
print(f"\n  Top features:")
for fn, fi in imp[:10]:
    mark = " ← NEW" if fn == "is_lhp" else ""
    print(f"    {fn:30s} {fi:.4f}{mark}")

# Betting sim
vegas_line = X_test[:, ALL_F.index("predicted_f5")]
diff = te_pred - vegas_line
bets = np.abs(diff) > 0.5
correct = ((diff[bets] > 0) == (y_test[bets] > vegas_line[bets]))
if bets.any():
    acc = correct.mean()
    print(f"\n[*] Betting sim ({bets.sum()} bets): accuracy={acc:.1%}")
