#!/usr/bin/env python3
"""
scraper.py — MLB first-5-innings data fetcher (optimized).
Fetches game events and dereferences team/linescores/score in parallel.
~20 mins per year of games — reasonable for 5 years.
"""

import json, time, requests, threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://sports.core.api.espn.com/v2/sports/baseball"
SEASONS  = [2021, 2022, 2023, 2025]
TYPE     = 2
OUT_DIR  = Path("data/raw")
OUT_DIR.mkdir(parents=True, exist_ok=True)
WORKERS  = 16   # parallel HTTP calls

H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# ── team name cache (30 teams reused across all games) ──────────────────────
_team_cache = {}
_cache_lock = threading.Lock()

def get(url, retries=1):
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=H, timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        if attempt < retries:
            time.sleep(0.3)
    return None

def team_name(tid):
    if not tid:
        return ""
    with _cache_lock:
        if tid in _team_cache:
            return _team_cache[tid]
    name = ""
    if tid:
        # strip any query off tid
        tid_clean = tid.split("?")[0]
        data = get(f"{BASE_URL}/leagues/mlb/seasons/2025/teams/{tid_clean}")
        if data:
            name = data.get("displayName", "")
    with _cache_lock:
        _team_cache[tid] = name
    return name

def id_from(ref):
    if not ref:
        return ""
    return ref.rstrip("/").split("/")[-1].split("?")[0]

def resolve_competitor(rc: dict, year: int) -> dict:
    """Resolve team name, linescores, score from $ref links — parallel."""
    ha = rc.get("homeAway", "")
    team_ref = (rc.get("team") or {}).get("$ref", "")
    team_id  = id_from(team_ref)

    def fetch_team():
        if team_ref:
            data = get(team_ref)   # $ref is already a full URL
            return (data.get("displayName", "") if data else "") if data else ""
        return ""

    def fetch_pitcher_name():
        # Athlete ref is nested inside probables
        for p in rc.get("probables", []):
            pid = p.get("playerId")
            if not pid:
                athlete_ref = (p.get("athlete") or {}).get("$ref", "")
                if athlete_ref:
                    adata = get(athlete_ref)
                    if adata:
                        return str(adata.get("id", "")), adata.get("displayName", "")
            else:
                # playerId is inline; try displayName from athlete first
                pname = (p.get("athlete") or {}).get("displayName", "")
                if not pname:
                    athlete_ref = (p.get("athlete") or {}).get("$ref", "")
                    if athlete_ref:
                        adata = get(athlete_ref)
                        if adata:
                            pname = adata.get("displayName", "")
                return str(pid), pname
        return "", ""

    def fetch_linescores():
        ls_ref = (rc.get("linescores") or {}).get("$ref", "")
        if not ls_ref:
            return 0, 0
        lsdata = get(ls_ref)       # $ref is already a full URL
        if not lsdata:
            return 0, 0
        first5, full = 0, 0
        for p in lsdata.get("items", []):
            runs = int(p.get("value", 0) or 0)
            period = p.get("period", 0)
            full += runs
            if 1 <= period <= 5:
                first5 += runs
        return first5, full

    def fetch_score():
        sv = rc.get("score", {})
        if isinstance(sv, dict) and sv.get("$ref"):
            sdata = get(sv["$ref"])   # $ref is already a full URL
            return sdata.get("value", 0) if sdata else 0
        if isinstance(sv, dict):
            return sv.get("value", 0) or 0
        return sv if sv else 0

    # Parallel fetch of team + linescores + score + pitcher name
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        ft = ex.submit(fetch_team)
        fl = ex.submit(fetch_linescores)
        fs = ex.submit(fetch_score)
        fp = ex.submit(fetch_pitcher_name)
        name   = ft.result()
        (first5, full) = fl.result()
        score   = fs.result()
        (pid, pname)   = fp.result()

    if full == 0 and score > 0:
        full = score

    return dict(team_id=team_id, team_name=name, ha=ha,
                pitcher_id=pid, pitcher_name=pname,
                first5=first5, full=full)


def parse_game(event_id, year):
    data = get(f"{BASE_URL}/leagues/mlb/events/{event_id}")
    if not data:
        return None

    date_str = data.get("date", "")
    try:
        date_iso = datetime.fromisoformat(date_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        date_iso = date_str[:10] if date_str else ""

    comps = data.get("competitions", [])
    if not comps:
        return None
    competitors = comps[0].get("competitors", [])
    if len(competitors) < 2:
        return None

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(resolve_competitor, rc, year) for rc in competitors]
        results = [f.result() for f in as_completed(futures)]

    by_ha = {r["ha"]: r for r in results}
    home = by_ha.get("home", results[0])
    away = by_ha.get("away", results[-1])

    if not home.get("team_id") or not away.get("team_id"):
        return None

    return dict(
        event_id=event_id, year=year, date=date_iso,
        home_team_id=home["team_id"], home_team_name=home["team_name"],
        away_team_id=away["team_id"], away_team_name=away["team_name"],
        home_pitcher_id=home["pitcher_id"], home_pitcher_name=home["pitcher_name"],
        away_pitcher_id=away["pitcher_id"], away_pitcher_name=away["pitcher_name"],
        home_first5_runs=home["first5"], away_first5_runs=away["first5"],
        home_full_runs=home["full"], away_full_runs=away["full"],
    )


def main():
    all_games = []
    for year in SEASONS:
        print(f"\n[*] {year}")
        # Collect all event IDs (paginate properly)
        event_ids = []
        base_page_url = f"{BASE_URL}/leagues/mlb/seasons/{year}/types/{TYPE}/events"
        pi = 1
        while True:
            page_url = f"{base_page_url}?page={pi}"
            data = get(page_url)
            if not data:
                break
            items = data.get("items", [])
            if not items:
                break
            for e in items:
                eid = id_from(e.get("$ref", ""))
                if eid:
                    event_ids.append(eid)
            pc = data.get("pageCount", 1)
            if pi >= pc:
                break
            pi += 1
            time.sleep(0.05)

        print(f"  → {len(event_ids)} events")

        year_games = []
        for i, eid in enumerate(event_ids):
            g = parse_game(eid, year)
            if g:
                year_games.append(g)
            if (i + 1) % 500 == 0:
                print(f"  [{year}] {i+1}/{len(event_ids)}, {len(year_games)} valid")

        # Deduplicate by (date, home_team, away_team)
        seen = set()
        unique = []
        for g in year_games:
            key = (g["date"], g["home_team_name"], g["away_team_name"])
            if key not in seen and g["home_team_name"]:
                seen.add(key)
                unique.append(g)
        if len(unique) < len(year_games):
            print(f"  → Deduped: {len(year_games)} → {len(unique)}")
        all_games.extend(unique)
        out = OUT_DIR / f"games_{year}.json"
        with open(out, "w") as f:
            json.dump(unique, f, indent=2)
        print(f"  → Saved {out.name}")

    with open(OUT_DIR / "games_all.json", "w") as f:
        json.dump(all_games, f, indent=2)
    print(f"\n[+] {len(all_games)} total games")


if __name__ == "__main__":
    main()
