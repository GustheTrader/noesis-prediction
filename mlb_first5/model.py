#!/usr/bin/env python3
"""model.py — Fast MLB first-5-innings model"""
import json, sys
from pathlib import Path
import numpy as np

DATA = Path("data/processed/model_data.csv")
if not DATA.exists():
    print("[!] Run enhanced_pipeline.py first"); sys.exit(1)

# Load CSV manually
rows, headers = [], []
with open(DATA) as f:
    headers = f.readline().strip().split(",")
    for line in f:
        parts = line.strip().split(",")
        if len(parts) == len(headers):
            rows.append(dict(zip(headers, parts)))

print(f"[+] {len(rows)} records")

# Feature columns
F = [
    "pitcher_era","pitcher_whip","pitcher_k9","pitcher_bb9","pitcher_kbb",
    "pitcher_gbfb","pitcher_k_pct","pitcher_ip",
    "is_home","pitcher_days_rest",
    "opp_avg_runs_allowed","opp_avg_first5_allowed",
]
D = ["pitcher_exp_er_5ip","pitcher_exp_h_5ip","pitcher_exp_bb_5ip",
     "pitcher_exp_k_5ip","predicted_f5","edge_vs_opp"]
ALL_F = F + D

X, y = [], []
for r in rows:
    try:
        feat = [float(r.get(c,"") or 0) for c in ALL_F]
        t = float(r["first_5_runs_allowed"])
        X.append(feat); y.append(t)
    except: pass

X, y = np.array(X), np.array(y)
print(f"Shape: {X.shape}, Target mean={y.mean():.2f}, std={y.std():.2f}")

# Split
years = np.array([int(r["year"]) for r in rows])
test_mask = years == 2025
X_train, X_test = X[~test_mask], X[test_mask]
y_train, y_test = y[~test_mask], y[test_mask]
print(f"Train: {len(X_train)} | Test: {len(X_test)}")

# Train
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

print("\n[*] Training RandomForest...")
rf = RandomForestRegressor(n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)

print("[*] Training GradientBoosting...")
gb = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, min_samples_leaf=20, random_state=42)
gb.fit(X_train, y_train)

# Evaluate
for name, m in [("RandomForest", rf), ("GradientBoosting", gb)]:
    tr_pred, te_pred = m.predict(X_train), m.predict(X_test)
    tr_mae, te_mae = mean_absolute_error(y_train, tr_pred), mean_absolute_error(y_test, te_pred)
    tr_rmse = np.sqrt(mean_squared_error(y_train, tr_pred))
    te_rmse = np.sqrt(mean_squared_error(y_test, te_pred))
    print(f"\n{'='*45}")
    print(f"{name}")
    print(f"  Train MAE: {tr_mae:.3f} | RMSE: {tr_rmse:.3f}")
    print(f"  Test  MAE: {te_mae:.3f} | RMSE: {te_rmse:.3f}")

    # Feature importance
    imp = sorted(zip(ALL_F, m.feature_importances_), key=lambda x: -x[1])
    print(f"  Top features:")
    for fn, fi in imp[:8]:
        print(f"    {fn:30s} {fi:.3f}")

# Simple betting simulation (vectorized)
vegas_line = X_test[:, ALL_F.index("predicted_f5")]
rf_pred = rf.predict(X_test)
diff = rf_pred - vegas_line
bets = np.abs(diff) > 0.5
correct = ((diff[bets] > 0) == (y_test[bets] > vegas_line[bets]))
if bets.any():
    acc = correct.mean()
    print(f"\n[*] Betting sim ({bets.sum()} bets):")
    print(f"    Accuracy: {acc:.1%}")
    print(f"    naive baseline: ~52%")
