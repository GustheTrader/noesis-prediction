#!/usr/bin/env python3
"""
pitcher_stats.py — Fast parallel pitcher stats fetcher.
Collects unique pitcher IDs from game data, then fetches all stats in parallel.
URL fix: use /leagues/mlb/seasons/{year} path
"""

import json, time, requests, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL  = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb"
SEASONS   = [2021, 2022, 2023, 2024, 2025]
RAW_DIR   = Path("data/raw")
STAT_DIR  = Path("data/raw/pitcher_stats")
STAT_DIR.mkdir(parents=True, exist_ok=True)
WORKERS   = 32
H         = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

_cache = {}
_lock  = threading.Lock()

def get(url):
    for attempt in range(2):
        try:
            r = requests.get(url, headers=H, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        if attempt == 0:
            time.sleep(0.2)
    return None

def id_from(ref):
    if not ref: return ""
    return ref.rstrip("/").split("/")[-1].split("?")[0]

def fetch_pitcher_stats(aid, year):
    """Fetch pitching stats for a pitcher."""
    url  = f"{BASE_URL}/seasons/{year}/types/2/athletes/{aid}/statistics/0"
    data = get(url)
    if not data:
        return {}
    cats = (data.get("splits") or {}).get("categories", [])
    pcat = next((c for c in cats if "pitching" in c.get("name","").lower()), None)
    if not pcat:
        return {}

    stats_map = {s["name"]: s.get("value") for s in pcat.get("stats", [])}
    def gs(*names):
        for n in names:
            v = stats_map.get(n)
            if v is not None:
                try: return float(v)
                except: pass
        return None

    ip  = gs("inningsPitched", "innings", "inningsPitchedSimple")
    er  = gs("earnedRuns")
    h   = gs("hitsAllowed", "hits", "hitsAllowedPitching")
    bb  = gs("walksAllowed", "walks")
    k   = gs("strikeoutsThrown", "strikeouts")
    hr  = gs("homeRunsAllowed", "homeRuns")
    gb  = gs("groundBalls", "groundBallsHit")
    fb  = gs("flyBalls", "flyBallsHit")
    bf  = gs("battersFaced", "battersFacedPitching")
    w   = gs("winsPitching", "wins")
    l   = gs("lossesPitching", "losses")

    era  = round((er / ip) * 9, 3)       if ip and er  is not None else None
    whip = round((h + bb) / ip, 3)        if ip and h   is not None and bb is not None else None
    k9   = round((k  / ip) * 9, 3)        if ip and k   is not None else None
    bb9  = round((bb / ip) * 9, 3)        if ip and bb  is not None else None
    kbb  = round(k / bb, 3)               if bb and k   is not None and bb != 0 else None
    gbfb = round(gb / fb, 3)              if fb and gb  is not None and fb != 0 else None

    return {
        "ip":     ip,  "er": er,  "h": h,  "bb": bb,  "k": k,
        "hr":     hr,  "gb": gb,  "fb": fb, "battersFaced": bf,
        "wins":   w,   "losses": l,
        "era":    era, "whip": whip, "k9": k9, "bb9": bb9, "kbb": kbb, "gbfb": gbfb,
    }

def fetch_athlete_info(aid, year):
    """Fetch athlete metadata."""
    url  = f"{BASE_URL}/seasons/{year}/athletes/{aid}"
    data = get(url)
    if not data:
        return {}
    return {
        "id":          aid,
        "displayName": data.get("displayName", ""),
        "position":    (data.get("position") or {}).get("displayName", ""),
        "team":        (data.get("team") or {}).get("displayName", ""),
        "teamId":      id_from((data.get("team") or {}).get("$ref", "")),
        "age":         data.get("age"),
    }

def fetch_pitcher_full(aid, year):
    info  = fetch_athlete_info(aid, year)
    stats = fetch_pitcher_stats(aid, year)
    return {**info, **stats}

def main():
    all_pids = {}
    for yr in SEASONS:
        path = RAW_DIR / f"games_{yr}.json"
        if not path.exists():
            print(f"[!] {path} not found")
            continue
        with open(path) as f:
            games = json.load(f)
        pids = set()
        for g in games:
            for k in ("home_pitcher_id", "away_pitcher_id"):
                pid = g.get(k, "")
                if pid:
                    pids.add(str(pid))
        all_pids[yr] = pids
        print(f"[{yr}] {len(pids)} unique pitchers")

    for yr in SEASONS:
        pids = sorted(all_pids.get(yr, []))
        if not pids:
            continue
        print(f"\n[*] Fetching {len(pids)} pitchers ({yr})...")
        records = []
        for i in range(0, len(pids), 100):
            batch = pids[i:i+100]
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                futures = {ex.submit(fetch_pitcher_full, pid, yr): pid for pid in batch}
                for f in as_completed(futures):
                    rec = f.result()
                    if rec and rec.get("era") is not None:
                        rec["id"] = str(futures[f])
                        records.append(rec)
            print(f"  [{yr}] {min(i+100, len(pids))}/{len(pids)} done ({len(records)} with stats)")
            time.sleep(0.3)

        out = STAT_DIR / f"pitchers_{yr}.json"
        with open(out, "w") as f:
            json.dump(records, f, indent=2)
        print(f"  → {len(records)} records → {out.name}")

    print("\n[+] Done")

if __name__ == "__main__":
    main()
