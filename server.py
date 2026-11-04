import calendar, re, json, os, time, urllib.error, threading, urllib.request, webbrowser
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

SEASON = "E2026"          # EuroLeague 2026-27. Use E2025 for last season (good for testing).
PORT = 8000
GAMES_PER_ROUND = 10      # EuroLeague: 20 teams -> 10 games per round
URL = "https://live.euroleague.net/api/Boxscore?gamecode={}&seasoncode=" + SEASON
SCHED, DEBUG = {}, {}
cache, state = {}, {"players": {}, "games": 0, "live": 0, "updated": None, "error": None}

def fetch(code):
    c = cache.get(code)
    if c and time.time() < c["until"]:
        return c["data"]
    data, err = None, None
    for attempt in range(5):
        try:
            time.sleep(0.6)   # be gentle: Euroleague rate-limits fast requests
            req = urllib.request.Request(URL.format(code), headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                body = r.read().decode("utf-8-sig").strip()
            data = json.loads(body) if body else None   # empty page = game has not started yet
            err = None
            break
        except urllib.error.HTTPError as e:
            err = e
            if e.code == 429:
                try: wait = float(e.headers.get("Retry-After"))
                except Exception: wait = 5 * (attempt + 1)
                state["error"] = f"Euroleague asked us to slow down, waiting {int(wait)}s…"
                time.sleep(min(wait, 60)); continue
            break
        except Exception as e:
            err = e; break
    if err:
        state["error"] = f"Game {code}: {err}"
        cache[code] = {"until": time.time() + 15, "data": "ERR"}
        return "ERR"
    parsed = parse(code, data, is_over(code)) if data else None
    ttl = 1e18 if parsed and parsed["final"] else (15 if parsed else 60)
    cache[code] = {"until": time.time() + ttl, "data": parsed}
    return parsed

def num(s, k):
    try: return float(s.get(k) or 0)
    except: return 0.0

def fantasy(s, won):
    """Basketnews Modern scoring."""
    miss = num(s,"FieldGoalsAttempted2")-num(s,"FieldGoalsMade2")+num(s,"FieldGoalsAttempted3")-num(s,"FieldGoalsMade3")
    ftm = num(s,"FreeThrowsAttempted")-num(s,"FreeThrowsMade")
    f = (num(s,"Points") + num(s,"DefensiveRebounds") + 1.5*num(s,"OffensiveRebounds")
         + 1.5*num(s,"Assistances") + 1.5*num(s,"Steals") + num(s,"BlocksFavour") + num(s,"FoulsReceived")
         - miss - ftm - 1.5*num(s,"Turnovers") - 0.5*num(s,"BlocksAgainst"))
    cats = sum(num(s,k) >= 10 for k in ("Points","TotalRebounds","Assistances","Steals","BlocksFavour"))
    f += 100 if cats >= 4 else 30 if cats == 3 else 10 if cats == 2 else 0
    if num(s,"FoulsCommited") >= 5: f -= 5
    if won is not None: f += 1.5 if won else -1.5
    return round(f, 1)

SCHED_TS = [0]

def is_over(code):
    """A game counts as final only if the schedule says played, or enough time has passed since the latest possible tip-off."""
    g = SCHED.get(code)
    if not g or g.get("played") is True: return True
    return g.get("hi") is None or time.time() > g["hi"] + 2.5 * 3600

def parse(code, d, over=True):
    teams = d.get("Stats") or []
    if len(teams) != 2: return None
    rows = [[p for p in (t.get("PlayersStats") or []) if (p.get("Player_ID") or "").strip()] for t in teams]
    tot = [sum(num(p,"Points") for p in r) for r in rows]
    if sum(tot) == 0: return None
    final = (not d.get("Live")) and over
    out = []
    for i, r in enumerate(rows):
        won = None if not final else tot[i] > tot[1-i]
        for p in r:
            if str(p.get("Minutes","")).upper() in ("DNP","","00:00"): continue
            out.append({"id": p["Player_ID"].strip(), "name": p.get("Player",""), "team": p.get("Team","").strip(),
                "round": SCHED.get(code, {}).get("round") or (code-1)//GAMES_PER_ROUND+1, "game": code, "live": not final,
                "min": p.get("Minutes"), "pts": num(p,"Points"), "reb": num(p,"TotalRebounds"), "oreb": num(p,"OffensiveRebounds"),
                "fg2m": num(p,"FieldGoalsMade2"), "fg2a": num(p,"FieldGoalsAttempted2"), "fg3m": num(p,"FieldGoalsMade3"), "fg3a": num(p,"FieldGoalsAttempted3"),
                "ftm": num(p,"FreeThrowsMade"), "fta": num(p,"FreeThrowsAttempted"), "bla": num(p,"BlocksAgainst"),
                "fc": num(p,"FoulsCommited"), "fd": num(p,"FoulsReceived"), "dreb": num(p,"DefensiveRebounds"),
                "ast": num(p,"Assistances"), "stl": num(p,"Steals"), "blk": num(p,"BlocksFavour"),
                "tov": num(p,"Turnovers"), "pir": num(p,"Valuation"), "fp": fantasy(p, won)})
    return {"final": final, "rows": out}

FETCH_LEAD = 2 * 3600   # start checking a game this long before tip-off
SHOW_LEAD = 3600        # show a new round in the dropdown this long before its first tip-off

def to_epoch(v):
    if isinstance(v, (int, float)) and v > 1e9: return (v / 1000 if v > 1e11 else v), True
    m = re.match(r"(\d{4}-\d\d-\d\d)[T ](\d\d:\d\d)(?::(\d\d))?(?:\.\d+)?\s*(Z|[+-]\d\d:?\d\d)?$", str(v or "").strip())
    if not m: return None, False
    t, z = calendar.timegm(time.strptime(f"{m.group(1)} {m.group(2)}:{m.group(3) or '00'}", "%Y-%m-%d %H:%M:%S")), m.group(4)
    if not z: return t, False
    if z == "Z": return t, True
    sign = 1 if z[0] == "+" else -1
    return t - sign * (int(z[1:3]) * 3600 + int(z[-2:]) * 60), True

def tipoff(g):
    """(earliest, latest) possible tip-off as epoch seconds. Equal when the feed states the timezone."""
    lo = hi = None
    for key in ("utcDate", "dateUtc", "date", "localDate", "startDate"):
        t, exact = to_epoch(g.get(key))
        if t is None: continue
        if exact or key in ("utcDate", "dateUtc"): return t, t
        if lo is None: lo, hi = t - 3 * 3600, t    # time without timezone: could be UTC or local arena time (up to UTC+3)
    return lo, hi

def rounds_info():
    """Rounds to list in the dropdown even before they have stats: from SHOW_LEAD before their first tip-off."""
    now, rounds, out = time.time(), {}, []
    for g in SCHED.values(): rounds.setdefault(g["round"], []).append(g)
    for r, gs in sorted(rounds.items()):
        known = [g for g in gs if g["lo"] is not None]
        if known:
            start = min(g["lo"] for g in known)
            if now >= start - SHOW_LEAD:
                out.append({"round": r, "start": start, "exact": len(known) == len(gs) and all(g["lo"] == g["hi"] for g in known)})
        elif r - 1 in rounds and all(g["played"] is True for g in rounds[r - 1]):
            out.append({"round": r, "start": None, "exact": False})   # no usable time in the feed: list it once the previous round is done
    return out

def schedule():
    for host in ("https://api-live.euroleague.net", "https://feeds.incrowdsports.com/provider/euroleague-feeds"):
        try:
            req = urllib.request.Request(f"{host}/v2/competitions/E/seasons/{SEASON}/games?limit=500", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.loads(r.read().decode("utf-8-sig"))
            items = d.get("data", []) if isinstance(d, dict) else d
            out = {}
            for g in items:
                code, rd = g.get("code") or g.get("gameCode"), g.get("round")
                if isinstance(rd, dict): rd = rd.get("round") or rd.get("number") or rd.get("roundNumber")
                if code and rd:
                    lo, hi = tipoff(g)
                    out[int(code)] = {"round": int(rd), "played": g.get("played"), "lo": lo, "hi": hi}
            DEBUG.update(host=host, n=len(items), sample=items[:2])
            if out: return out
        except Exception as e:
            DEBUG["schedule_error"] = f"{host}: {e}"
    return {}

def wanted(g):
    if g["played"] is True: return True
    return g["lo"] is None or g["lo"] < time.time() + FETCH_LEAD

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"games_{SEASON}_v3.json")
try:
    for k, v in json.load(open(CACHE_FILE)).items(): cache[int(k)] = {"until": 1e18, "data": v}
except Exception: pass

def publish(found, errs):
    players, live = {}, 0
    for g in found.values():
        live += 0 if g["final"] else 1
        for r in g["rows"]:
            players.setdefault(r["id"], {"id": r["id"], "name": r["name"], "team": r["team"], "games": []})["games"].append(r)
    state.update(players=players, games=len(found), live=live, failed=errs, updated=time.strftime("%H:%M:%S"))
    if not errs: state["error"] = None
    try:
        json.dump({str(c): v["data"] for c, v in cache.items() if isinstance(v["data"], dict) and v["data"]["final"]}, open(CACHE_FILE, "w"))
    except Exception: pass

def refresh():
    if not SCHED or time.time() - SCHED_TS[0] > 120:
        new = schedule()
        if new: SCHED.update(new); SCHED_TS[0] = time.time()
    sch = SCHED
    found, errs = {}, 0
    with ThreadPoolExecutor(1) as ex:
        if sch:   # normal path: fetch exactly the games that are played or about to be
            codes = [c for c, g in sorted(sch.items(), reverse=True) if wanted(g)]
            for c, g in zip(codes, ex.map(fetch, codes)):
                if g == "ERR": errs += 1
                elif g:
                    found[c] = g
                    if len(found) % 4 == 0: publish(found, errs)
        else:     # fallback: probe game numbers one after another
            last, code = 0, 1
            while code - last <= 30 and code < 500:
                batch = list(range(code, code+8)); code += 8
                for c, g in zip(batch, ex.map(fetch, batch)):
                    if g == "ERR": errs += 1; last = max(last, c)
                    elif g: last = max(last, c); found[c] = g
    publish(found, errs)

def loop():
    while True:
        try: refresh()
        except Exception as e: state["error"] = str(e)
        time.sleep(10 if state["live"] else 30)

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=os.path.dirname(os.path.abspath(__file__)), **k)
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith("/api/data"):
            body = json.dumps({**state, "players": list(state["players"].values()), "rounds": rounds_info()}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
        elif self.path.startswith("/api/debug"):
            body = json.dumps({"schedule": DEBUG, "rounds_known": len(set(g["round"] for g in SCHED.values())), "games_in_schedule": len(SCHED), "exact_tipoff_times": sum(1 for g in SCHED.values() if g["lo"] is not None and g["lo"] == g["hi"]), "visible_rounds": rounds_info()}, default=str).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(body)
        else: super().do_GET()

if __name__ == "__main__":
    threading.Thread(target=loop, daemon=True).start()
    print(f"Open http://localhost:{PORT}  (close this window to stop)")
    webbrowser.open(f"http://localhost:{PORT}")
    ThreadingHTTPServer(("", PORT), H).serve_forever()
