#!/usr/bin/env python3
"""
enhanced_pipeline.py — Build model dataset from scraped ESPN data.
Uses seasons with complete pitcher data: 2021, 2022, 2023 (NOT 2024).
"""

import json, os, sys, requests
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import numpy as np

RAW_DIR   = Path("data/raw")
STAT_DIR  = Path("data/raw/pitcher_stats")
OUT_DIR   = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 2024 excluded — ESPN has no pitcher data for that season
SEASONS   = [2021, 2022, 2023, 2025]
TEST_YEAR = 2025
TRAIN_YEARS = [y for y in SEASONS if y != TEST_YEAR]

BASE_URL = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb"
H        = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def get(url):
    for attempt in range(2):
        try:
            r = requests.get(url, headers=H, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        if attempt == 0:
            pass
    return None


def load_games(yr):
    path = RAW_DIR / f"games_{yr}.json"
    if not path.exists():
        return []
    with open(path) as f:
        games = json.load(f)
    # Filter to games with pitcher data
    return [g for g in games if g.get("home_pitcher_name")]


def load_pitcher_stats(yr):
    path = STAT_DIR / f"pitchers_{yr}.json"
    if not path.exists():
        return {}
    with open(path) as f:
        records = json.load(f)
    return {str(r["id"]): r for r in records}


def team_season_averages(games, year):
    """Compute per-opponent team averages for runs/first5 allowed."""
    ta = defaultdict(list)
    for g in games:
        home, away = g["home_team_id"], g["away_team_id"]
        ta[home].append({"ra": g["away_full_runs"],  "f5": g["away_first5_runs"]})
        ta[away].append({"ra": g["home_full_runs"], "f5": g["home_first5_runs"]})

    out = {}
    for tid, vals in ta.items():
        out[tid] = {
            "opp_avg_ra": np.mean([v["ra"] for v in vals]),
            "opp_avg_f5": np.mean([v["f5"] for v in vals]),
        }
    return out


def pitcher_record(pid, games):
    """Sort a pitcher's games by date for days_rest calculation."""
    pgs = sorted([g for g in games if g["home_pitcher_id"] == pid or g["away_pitcher_id"] == pid],
                  key=lambda x: x["date"])
    return pgs


def build_records():
    all_records = []
    all_team_avg = {}

    for yr in SEASONS:
        games = load_games(yr)
        stats = load_pitcher_stats(yr)
        tavg  = team_season_averages(games, yr)
        all_team_avg[yr] = tavg
        print(f"  {yr}: {len(games)} games, {len(stats)} pitchers, {len(tavg)} teams")

        # Index pitcher games by date
        pitcher_games = defaultdict(list)
        for g in games:
            for pid in [g.get("home_pitcher_id"), g.get("away_pitcher_id")]:
                if pid:
                    pitcher_games[pid].append(g)
        for pid in pitcher_games:
            pitcher_games[pid].sort(key=lambda x: x["date"])

        for g in games:
            yr = g["year"]
            date = g["date"]

            for side in ["home", "away"]:
                pid = g.get(f"{side}_pitcher_id", "")
                if not pid or pid not in stats:
                    continue

                p = stats[pid]
                # Target: runs allowed by this pitcher in first 5 innings
                opp_first5 = g["away_first5_runs"] if side == "home" else g["home_first5_runs"]

                # Days rest
                pgs = pitcher_games.get(pid, [])
                this_idx = next((i for i, x in enumerate(pgs)
                                 if x["date"] == date and x["event_id"] == g["event_id"]), None)
                if this_idx and this_idx > 0:
                    prev = datetime.strptime(pgs[this_idx - 1]["date"], "%Y-%m-%d")
                    curr = datetime.strptime(date, "%Y-%m-%d")
                    days_rest = (curr - prev).days
                else:
                    days_rest = None

                # Opponent team
                opp_tid = g["away_team_id"] if side == "home" else g["home_team_id"]
                opp_s = all_team_avg[yr].get(opp_tid, {})

                # Derived per-5-IP rates
                ip = p.get("ip") or 0
                er = p.get("er") or 0
                h  = p.get("h")  or 0
                bb = p.get("bb") or 0
                k  = p.get("k")  or 0
                gb = p.get("gb") or 0
                fb = p.get("fb") or 0

                exp_er_5ip  = round((er / ip) * 5, 2) if ip > 0 else None
                exp_h_5ip   = round((h  / ip) * 5, 2) if ip > 0 else None
                exp_bb_5ip  = round((bb / ip) * 5, 2) if ip > 0 else None
                exp_k_5ip   = round((k  / ip) * 5, 2) if ip > 0 else None

                # Naive prediction
                base_er = (p.get("era") or 0) / 9 * 5 if p.get("era") else 2.5
                opp_adj = (opp_s.get("opp_avg_f5") or 2.5) - 2.5
                predicted_f5 = round(base_er + opp_adj * 0.3, 2)

                rec = {
                    # Target
                    "first_5_runs_allowed": opp_first5,
                    # Pitcher stats
                    "pitcher_id":   pid,
                    "pitcher_name": g.get(f"{side}_pitcher_name", ""),
                    "pitcher_era":  p.get("era") or 0,
                    "pitcher_whip": p.get("whip") or 0,
                    "pitcher_k9":   p.get("k9")  or 0,
                    "pitcher_bb9":  p.get("bb9") or 0,
                    "pitcher_kbb":  p.get("kbb") or 0,
                    "pitcher_gbfb": p.get("gbfb") or 0,
                    "pitcher_ip":   ip,
                    "pitcher_k_pct": round(k / (p.get("battersFaced") or 1), 4) if k else 0,
                    "pitcher_hr_pct": round((p.get("hr") or 0) / (p.get("battersFaced") or 1), 4),
                    "pitcher_wins":   p.get("wins", 0) or 0,
                    "pitcher_losses": p.get("losses", 0) or 0,
                    "pitcher_exp_er_5ip":  exp_er_5ip,
                    "pitcher_exp_h_5ip":   exp_h_5ip,
                    "pitcher_exp_bb_5ip":   exp_bb_5ip,
                    "pitcher_exp_k_5ip":    exp_k_5ip,
                    "pitcher_days_rest":     days_rest,
                    # Game context
                    "is_home":   1 if side == "home" else 0,
                    "year":       yr,
                    "date":       date,
                    "team_id":    opp_tid,
                    # Opponent context
                    "opp_avg_runs_allowed":  round(opp_s.get("opp_avg_ra", 4.5), 2),
                    "opp_avg_first5_allowed": round(opp_s.get("opp_avg_f5", 2.5), 2),
                    # Naive betting line
                    "predicted_f5": predicted_f5,
                    "edge_vs_opp":  round((opp_s.get("opp_avg_f5") or 2.5) - predicted_f5, 2),
                    "event_id": g["event_id"],
                }
                all_records.append(rec)

    return all_records


def save_csv(records, path):
    if not records:
        print("[!] No records to save")
        return
    import csv
    cols = list(records[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(records)
    print(f"  → Saved {len(records)} records → {path}")


def main():
    print("[*] Building feature records...")
    records = build_records()
    print(f"\n[+] Total records: {len(records)}")

    train = [r for r in records if r["year"] in TRAIN_YEARS]
    test  = [r for r in records if r["year"] == TEST_YEAR]
    print(f"    Train ({TRAIN_YEARS}): {len(train)}")
    print(f"    Test  ({TEST_YEAR}):  {len(test)}")

    save_csv(records, OUT_DIR / "model_data.csv")
    save_csv(train,   OUT_DIR / "train_data.csv")
    save_csv(test,    OUT_DIR / "test_data.csv")

    # Summary stats
    targets = [r["first_5_runs_allowed"] for r in records]
    print(f"\n[*] Target distribution:")
    print(f"    Mean: {np.mean(targets):.2f} | Std: {np.std(targets):.2f}")
    print(f"    Min:  {np.min(targets):.0f}  | Max: {np.max(targets):.0f}")

    # Naive baseline MAE
    preds   = [r["predicted_f5"] for r in records]
    mae     = np.mean([abs(t - p) for t, p in zip(targets, preds)])
    print(f"\n[*] Naive baseline MAE: {mae:.3f}")


if __name__ == "__main__":
    main()
