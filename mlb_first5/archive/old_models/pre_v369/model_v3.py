#!/usr/bin/env python3
"""model_v3.py — MLB first-5 model with handedness + platoon features"""
import numpy as np, csv

DATA = "data/processed/model_data_v3.csv"
rows = []
with open(DATA) as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

F = ["pitcher_era","pitcher_whip","pitcher_k9","pitcher_bb9","pitcher_kbb",
     "pitcher_gbfb","pitcher_k_pct","pitcher_ip",
     "is_home","pitcher_days_rest",
     "opp_avg_runs_allowed","opp_avg_first5_allowed"]
D = ["pitcher_exp_er_5ip","pitcher_exp_h_5ip","pitcher_exp_bb_5ip",
     "pitcher_exp_k_5ip","predicted_f5","edge_vs_opp"]
NEW = ["is_lhp","opp_batting_first5","platoon_score"]
ALL = F + D + NEW

X, y = [], []
for r in rows:
    try:
        feat = [float(r.get(c,"") or 0) for c in ALL]
        t = float(r["first_5_runs_allowed"])
        X.append(feat); y.append(t)
    except: pass

X, y = np.array(X), np.array(y)
print(f"Shape: {X.shape}")

years = np.array([int(r["year"]) for r in rows])
X_train, X_test = X[years<2025], X[years==2025]
y_train, y_test = y[years<2025], y[years==2025]
print(f"Train: {len(X_train)} | Test: {len(X_test)}")

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

gb = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.05,
                               min_samples_leaf=20, random_state=42)
gb.fit(X_train, y_train)

te_pred = gb.predict(X_test)
mae  = mean_absolute_error(y_test, te_pred)
rmse = np.sqrt(mean_squared_error(y_test, te_pred))
print(f"\nGradientBoosting (v3):")
print(f"  MAE:  {mae:.3f}  (v1 naive=1.824, v2=1.604")
print(f"  RMSE: {rmse:.3f}")

imp = sorted(zip(ALL, gb.feature_importances_), key=lambda x: -x[1])
print(f"\n  Top features:")
for fn, fi in imp:
    mark = " ← NEW" if fn in NEW else ""
    print(f"    {fn:30s} {fi:.4f}{mark}")

# Betting sim
vegas = X_test[:, ALL.index("predicted_f5")]
diff  = te_pred - vegas
bets  = np.abs(diff) > 0.5
if bets.any():
    acc = ((diff[bets] > 0) == (y_test[bets] > vegas[bets])).mean()
    print(f"\n  Betting sim ({bets.sum()} bets): acc={acc:.1%}")
