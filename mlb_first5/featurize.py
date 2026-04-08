#!/usr/bin/env python3
"""
featurize.py - Join pitcher stats to game records and produce a modelling CSV.

Features per pitcher-game:
  Pitcher:  ERA, WHIP, K/9, BB/9, K/BB, GB/FB, IP, age, wins, losses, games
  Game:     home/away, days_rest, opponent_season_runs_allowed
  Target:   first_5_runs_allowed (int)

Output: data/processed/model_data.csv
"""

import json
import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ── config ──────────────────────────────────────────────────────────────────
RAW_DIR   = Path("data/raw")
OUT_DIR   = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEASONS = [2021, 2022, 2023, 2024, 2025]


# ── load helpers ─────────────────────────────────────────────────────────────

def load_games(year: int) -> list[dict]:
    path = RAW_DIR / f"games_{year}.json"
    if not path.exists():
        print(f"[!] {path} not found — run scraper.py first")
        return []
    with open(path) as f:
        return json.load(f)


def load_pitchers(year: int) -> list[dict]:
    path = RAW_DIR / f"pitchers_{year}.json"
    if not path.exists():
        print(f"[!] {path} not found — run pitcher_stats.py first")
        return []
    with open(path) as f:
        return json.load(f)


# ── team runs allowed ────────────────────────────────────────────────────────

def team_runs_allowed(year: int) -> dict[str, int]:
    """
    Compute runs allowed per team across all games in a season.
    Away runs scored against home team = home runs allowed.
    Home runs scored against away team = away runs allowed.
    """
    games = load_games(year)
    ra = defaultdict(int)   # team_id → total runs allowed

    for g in games:
        home_id = str(g.get("home_team_id", ""))
        away_id = str(g.get("away_team_id", ""))
        away_score = int(g.get("away_score") or 0)
        home_score = int(g.get("home_score") or 0)

        if home_id and away_score:
            ra[home_id] += away_score
        if away_id and home_score:
            ra[away_id] += home_score

    return dict(ra)


# ── days rest ────────────────────────────────────────────────────────────────

def build_date_index(games: list[dict]) -> dict[str, str]:
    """Map pitcher_id → most recent game date (ISO string) seen so far."""
    date_by_pid: dict = {}
    for g in sorted(games, key=lambda x: x.get("date", "")):
        date = g.get("date", "")
        for pid_key in ("home_pitcher_id", "away_pitcher_id"):
            pid = str(g.get(pid_key) or "")
            if pid:
                date_by_pid[pid] = date   # later games overwrite earlier
    return date_by_pid


def compute_days_rest(pitcher_id: str, game_date: str, date_by_pid: dict) -> int | None:
    """Days since pitcher last pitched (from date_by_pid index)."""
    if not game_date or not pitcher_id:
        return None
    prev = date_by_pid.get(pitcher_id, "")
    if not prev or prev >= game_date:
        return None
    try:
        gdate = datetime.strptime(game_date, "%Y-%m-%d")
        pdate = datetime.strptime(prev,  "%Y-%m-%d")
        return (gdate - pdate).days
    except ValueError:
        return None


# ── build records ────────────────────────────────────────────────────────────

def build_records() -> list[dict]:
    all_records = []

    for year in SEASONS:
        games    = load_games(year)
        pitchers = load_pitchers(year)
        print(f"\n[*] {year}: {len(games)} games, {len(pitchers)} pitcher records")

        # Index pitchers by id (handle int/str)
        p_idx = {str(p.get("id", "") or ""): p for p in pitchers}

        # Team runs allowed lookup
        opp_ra = team_runs_allowed(year)

        # Build pitcher → last date index for days-rest
        date_by_pid = build_date_index(games)
        # Re-sort by date for sequential days-rest computation
        games_sorted = sorted(games, key=lambda g: g.get("date", ""))

        year_rows = 0
        for g in games_sorted:
            date     = g.get("date", "")
            home_id  = str(g.get("home_team_id", ""))
            away_id  = str(g.get("away_team_id", ""))
            home_pid = str(g.get("home_pitcher_id") or "")
            away_pid = str(g.get("away_pitcher_id") or "")

            # Update days-rest index with current game
            for pid, d in [(home_pid, date), (away_pid, date)]:
                if pid:
                    date_by_pid[pid] = d

            # ── home pitcher row ─────────────────────────────────────────────
            home_p = p_idx.get(home_pid, {})
            if home_pid and home_p.get("ip"):
                dr = compute_days_rest(home_pid, date, date_by_pid)
                all_records.append({
                    "year":                  year,
                    "event_id":              g["event_id"],
                    "date":                  date,
                    "team_id":               home_id,
                    "opponent_id":           away_id,
                    "is_home":               1,
                    "pitcher_id":            home_pid,
                    "pitcher_name":          g.get("home_pitcher_name", ""),
                    # pitcher stats
                    "era":                   home_p.get("era"),
                    "whip":                  home_p.get("whip"),
                    "k9":                    home_p.get("k9"),
                    "bb9":                   home_p.get("bb9"),
                    "kbb":                   home_p.get("kbb"),
                    "gbfb":                  home_p.get("gbfb"),
                    "ip":                    home_p.get("ip"),
                    "wins":                  home_p.get("wins") or 0,
                    "losses":                home_p.get("losses") or 0,
                    "games":                 home_p.get("games") or 0,
                    "age":                   home_p.get("age"),
                    # game context
                    "days_rest":             dr,
                    "opp_runs_allowed":      opp_ra.get(away_id, 0),
                    # target
                    "first_5_runs_allowed":  g.get("home_first5_runs", 0),
                })
                year_rows += 1

            # ── away pitcher row ─────────────────────────────────────────────
            away_p = p_idx.get(away_pid, {})
            if away_pid and away_p.get("ip"):
                dr = compute_days_rest(away_pid, date, date_by_pid)
                all_records.append({
                    "year":                  year,
                    "event_id":              g["event_id"],
                    "date":                  date,
                    "team_id":               away_id,
                    "opponent_id":           home_id,
                    "is_home":               0,
                    "pitcher_id":            away_pid,
                    "pitcher_name":          g.get("away_pitcher_name", ""),
                    # pitcher stats
                    "era":                   away_p.get("era"),
                    "whip":                  away_p.get("whip"),
                    "k9":                    away_p.get("k9"),
                    "bb9":                   away_p.get("bb9"),
                    "kbb":                   away_p.get("kbb"),
                    "gbfb":                  away_p.get("gbfb"),
                    "ip":                    away_p.get("ip"),
                    "wins":                  away_p.get("wins") or 0,
                    "losses":                away_p.get("losses") or 0,
                    "games":                 away_p.get("games") or 0,
                    "age":                   away_p.get("age"),
                    # game context
                    "days_rest":             dr,
                    "opp_runs_allowed":      opp_ra.get(home_id, 0),
                    # target
                    "first_5_runs_allowed":  g.get("away_first5_runs", 0),
                })
                year_rows += 1

        print(f"  → {year_rows} pitcher-game rows added")

    return all_records


def write_csv(records: list[dict], path: Path):
    if not records:
        print("[!] No records to write")
        return
    fieldnames = [
        "year", "event_id", "date", "team_id", "opponent_id",
        "is_home", "pitcher_id", "pitcher_name",
        "era", "whip", "k9", "bb9", "kbb", "gbfb",
        "ip", "wins", "losses", "games", "age",
        "days_rest", "opp_runs_allowed",
        "first_5_runs_allowed",
    ]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)
    print(f"\n[+] {len(records)} rows → {path}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    records = build_records()
    write_csv(records, OUT_DIR / "model_data.csv")

    import statistics
    targets = [r["first_5_runs_allowed"] for r in records if r["first_5_runs_allowed"] is not None]
    if targets:
        print(f"\n[*] Target stats:")
        print(f"    count : {len(targets)}")
        print(f"    mean  : {statistics.mean(targets):.2f}")
        print(f"    median: {statistics.median(targets):.1f}")
        if len(targets) > 1:
            print(f"    std   : {statistics.stdev(targets):.2f}")


if __name__ == "__main__":
    main()
