#!/usr/bin/env python3
"""
pipeline_v2.py — Rebuilt from scratch. Proper deduplication + all features.
Key fix: event_id is NOT unique per game. Use (date, home_team, away_team) as game key.
"""
import json, csv, numpy as np
from collections import defaultdict
from pathlib import Path
from datetime import datetime

RAW = Path("data/raw")
SEASONS = [2021, 2022, 2023, 2025]  # 2024 excluded

# Load handedness
with open("data/pitcher_handedness.json") as f:
    handedness = json.load(f)

def load_games(yr):
    with open(RAW / f"games_{yr}.json") as f:
        games = json.load(f)
    return [g for g in games if g.get("home_pitcher_name")]

def load_stats(yr):
    with open(RAW / f"pitcher_stats/pitchers_{yr}.json") as f:
        return {str(r["id"]): r for r in json.load(f)}

def game_key(g):
    """Unique key for a game — event_id is NOT unique in ESPN data."""
    return (g["date"], g["home_team_name"], g["away_team_name"])

print("[1] Loading data...")
all_records = []

for yr in SEASONS:
    games = load_games(yr)
    stats = load_stats(yr)
    print(f"  {yr}: {len(games)} games, {len(stats)} pitchers")
    
    # Team season averages (opponent's avg runs allowed/f5)
    team_avg = defaultdict(list)
    for g in games:
        ht, at = g["home_team_id"], g["away_team_id"]
        team_avg[ht].append({"ra": g["away_full_runs"], "f5": g["away_first5_runs"]})
        team_avg[at].append({"ra": g["home_full_runs"], "f5": g["home_first5_runs"]})
    
    team_s = {}
    for tid, vals in team_avg.items():
        team_s[tid] = {
            "opp_avg_ra": round(np.mean([v["ra"] for v in vals]), 3),
            "opp_avg_f5": round(np.mean([v["f5"] for v in vals]), 3),
        }
    
    # Pitcher game history for days_rest
    pitcher_games = defaultdict(list)
    for g in games:
        for side in ["home", "away"]:
            pid = g.get(f"{side}_pitcher_id")
            if pid:
                pitcher_games[str(pid)].append(g)
    for pid in pitcher_games:
        pitcher_games[pid].sort(key=lambda x: x["date"])
    
    # Build records — ONE per (game, side)
    seen = set()
    yr_records = 0
    
    for g in games:
        gk = game_key(g)
        
        for side in ["home", "away"]:
            pid = str(g.get(f"{side}_pitcher_id", ""))
            if not pid or pid not in stats:
                continue
            
            # Dedup check
            rec_key = (gk, side, pid)
            if rec_key in seen:
                continue
            seen.add(rec_key)
            
            p = stats[pid]
            pname = g.get(f"{side}_pitcher_name", "").strip()
            opp_first5 = g["away_first5_runs"] if side == "home" else g["home_first5_runs"]
            
            # Days rest
            pgs = pitcher_games.get(pid, [])
            this_idx = next((i for i, x in enumerate(pgs) 
                            if x["date"] == g["date"] and game_key(x) == gk), None)
            if this_idx and this_idx > 0:
                prev = datetime.strptime(pgs[this_idx-1]["date"], "%Y-%m-%d")
                curr = datetime.strptime(g["date"], "%Y-%m-%d")
                days_rest = (curr - prev).days
            else:
                days_rest = 4  # default
            
            # Opponent team
            opp_tid = g["away_team_id"] if side == "home" else g["home_team_id"]
            opp_s = team_s.get(opp_tid, {"opp_avg_ra": 4.5, "opp_avg_f5": 2.5})
            
            # Derived stats
            ip = p.get("ip") or 0
            er = p.get("er") or 0
            h  = p.get("h")  or 0
            bb = p.get("bb") or 0
            k  = p.get("k")  or 0
            
            exp_er = round((er/ip)*5, 2) if ip > 0 else 0
            exp_h  = round((h/ip)*5, 2) if ip > 0 else 0
            exp_bb = round((bb/ip)*5, 2) if ip > 0 else 0
            exp_k  = round((k/ip)*5, 2) if ip > 0 else 0
            
            # Naive prediction
            base_er = (p.get("era") or 0) / 9 * 5 if p.get("era") else 2.5
            opp_adj = (opp_s.get("opp_avg_f5") or 2.5) - 2.5
            predicted_f5 = round(base_er + opp_adj * 0.3, 2)
            
            # Handedness
            hand = handedness.get(pname)
            is_lhp = 1 if hand == "L" else 0
            
            rec = {
                "first_5_runs_allowed": opp_first5,
                "pitcher_id": pid,
                "pitcher_name": pname,
                "pitcher_era": p.get("era") or 0,
                "pitcher_whip": p.get("whip") or 0,
                "pitcher_k9": p.get("k9") or 0,
                "pitcher_bb9": p.get("bb9") or 0,
                "pitcher_kbb": p.get("kbb") or 0,
                "pitcher_gbfb": p.get("gbfb") or 0,
                "pitcher_ip": ip,
                "pitcher_k_pct": round(k / (p.get("battersFaced") or 1), 4) if k else 0,
                "pitcher_exp_er_5ip": exp_er,
                "pitcher_exp_h_5ip": exp_h,
                "pitcher_exp_bb_5ip": exp_bb,
                "pitcher_exp_k_5ip": exp_k,
                "pitcher_days_rest": days_rest,
                "is_home": 1 if side == "home" else 0,
                "year": yr,
                "date": g["date"],
                "opp_avg_runs_allowed": round(opp_s.get("opp_avg_ra", 4.5), 2),
                "opp_avg_first5_allowed": round(opp_s.get("opp_avg_f5", 2.5), 2),
                "predicted_f5": predicted_f5,
                "edge_vs_opp": round((opp_s.get("opp_avg_f5") or 2.5) - predicted_f5, 2),
                "is_lhp": is_lhp,
                "game_key": f"{g['date']}|{g['home_team_name']}|{g['away_team_name']}",
            }
            all_records.append(rec)
            yr_records += 1
    
    print(f"    Records: {yr_records}")

# Verify uniqueness
keys = [(r["game_key"], r["pitcher_id"]) for r in all_records]
print(f"\n[2] Total records: {len(all_records)}")
print(f"    Unique (game, pitcher): {len(set(keys))}")
print(f"    Unique games: {len(set(r['game_key'] for r in all_records))}")

# Save
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "model_data_clean.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=all_records[0].keys())
    writer.writeheader()
    writer.writerows(all_records)
print(f"\n[+] Saved model_data_clean.csv ({len(all_records)} records)")
