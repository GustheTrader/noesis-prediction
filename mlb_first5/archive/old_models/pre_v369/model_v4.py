#!/usr/bin/env python3
"""model_v4.py — Full v3 + 14-game heat check (LEAK-FREE rolling average)"""
import numpy as np, csv

rows = list(csv.DictReader(open('data/processed/model_data_v4.csv')))

F = ["pitcher_era","pitcher_whip","pitcher_k9","pitcher_bb9","pitcher_kbb",
     "pitcher_gbfb","pitcher_k_pct","pitcher_ip","is_home","pitcher_days_rest",
     "opp_avg_runs_allowed","opp_avg_first5_allowed"]
D = ["pitcher_exp_er_5ip","pitcher_exp_h_5ip","pitcher_exp_bb_5ip",
     "pitcher_exp_k_5ip","predicted_f5","edge_vs_opp"]
P = ["is_lhp","opp_batting_first5","platoon_score"]
H = ["opp_heat_14","pitcher_team_heat_14","heat_differential"]  # NEW
ALL = F + D + P + H

X, y = [], []
for r in rows:
    try:
        feat = [float(r.get(c,"") or 0) for c in ALL]
        t = float(r["first_5_runs_allowed"])
        X.append(feat); y.append(t)
    except: pass

X, y = np.array(X), np.array(y)
years = np.array([int(r["year"]) for r in rows])
X_train, X_test = X[years<2025], X[years==2025]
y_train, y_test = y[years<2025], y[years==2025]
print(f"Shape: {X.shape} | Train: {len(X_train)} | Test: {len(X_test)}")

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

gb = GradientBoostingRegressor(n_estimators=300, max_depth=5, learning_rate=0.05,
                               min_samples_leaf=15, subsample=0.8, random_state=42)
gb.fit(X_train, y_train)

pred = gb.predict(X_test)
mae  = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
print(f"\n🧮 GradientBoosting v4 (handedness + platoon + heat check):")
print(f"   MAE:  {mae:.3f}  (v2=1.604, v3=0.990)")
print(f"   RMSE: {rmse:.3f}")

imp = sorted(zip(ALL, gb.feature_importances_), key=lambda x: -x[1])
print(f"\n   Feature importance:")
for fn, fi in imp:
    mark = " ← HEAT" if fn in H else (" ← PLATOON" if fn in P else "")
    print(f"     {fn:30s} {fi:.4f}{mark}")

# Betting sim
vegas = X_test[:, ALL.index("predicted_f5")]
diff  = pred - vegas
for threshold in [0.3, 0.5, 0.7, 1.0]:
    bets = np.abs(diff) > threshold
    if bets.any():
        correct = ((diff[bets] > 0) == (y_test[bets] > vegas[bets]))
        acc = correct.mean()
        n = bets.sum()
        print(f"\n   Betting sim (threshold={threshold}, {n} bets): acc={acc:.1%}")

# Detailed: which side wins more?
bets_05 = np.abs(diff) > 0.5
if bets_05.any():
    over = (diff[bets_05] > 0) & (y_test[bets_05] > vegas[bets_05])
    under = (diff[bets_05] < 0) & (y_test[bets_05] <= vegas[bets_05])
    total_bets = bets_05.sum()
    over_wins = over.sum()
    under_wins = under.sum()
    print(f"\n   Over wins: {over_wins}/{total_bets//2} | Under wins: {under_wins}/{total_bets//2}")
