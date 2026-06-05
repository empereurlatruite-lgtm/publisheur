#!/usr/bin/env python3
"""newspaper.py — Fictitious wartime newspaper HTTP API.

Reads foxhole_war.db and shapes it into newspaper-style endpoints. Templates
only (no LLM). Run `python3 build_war_db.py` first to populate the DB.

Endpoints:
    GET /               — index of available routes
    GET /front-page     — lead story + headlines + war summary
    GET /dispatches?sector=west|center|east|all   — sector narrative
    GET /hex/<hex_name> — per-hex war diary
    GET /headlines      — auto-generated wire headlines

Usage:
    python3 newspaper.py                 # serve on 127.0.0.1:8181
    python3 newspaper.py --port 9000
    curl -s http://127.0.0.1:8181/front-page | jq
"""

import argparse
import json
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import articles as art

DB = Path(__file__).parent.parent / "data-collection" / "foxhole_war.db"
WEB = Path(__file__).parent / "web"
MASTHEAD = "LE PETIT DAIHBI — War #{war} Daily"
SECTOR_NAMES = {"west": "Western Front", "center": "Central Front", "east": "Eastern Front"}


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


# ── Data accessors ─────────────────────────────────────────────────────────
def war_meta(c):
    r = c.execute("SELECT * FROM wars LIMIT 1").fetchone()
    if not r:
        return None
    start = datetime.fromtimestamp(r["conquest_start_ms"] / 1000, tz=timezone.utc)
    day = (datetime.now(timezone.utc) - start).days + 1
    return {
        "war_number": r["war_number"], "shard": r["shard"],
        "started_utc": start.isoformat(), "day_of_war": day,
        "winner": r["winner"], "victory_towns_required": r["required_victory_towns"],
    }


def latest_by_hex(c):
    return {r["hex_name"]: dict(r) for r in c.execute("SELECT * FROM v_latest_casualties")}


def sector_totals(c):
    return [dict(r) for r in c.execute(
        "SELECT * FROM v_sector_totals ORDER BY total_kia DESC"
    )]


def delta_24h_by_hex(c, window_ms=86_400_000):
    """Return {hex_name: (warden_delta, colonial_delta)} over last `window_ms`."""
    q = """
    WITH now_pt(m)   AS (SELECT MAX(sampled_at_ms) FROM casualty_samples),
         ago_pt(m)   AS (SELECT (SELECT m FROM now_pt) - ?),
         latest AS (
           SELECT hex_name, warden_casualties w, colonial_casualties c
           FROM casualty_samples cs
           WHERE id = (SELECT id FROM casualty_samples cs2
                       WHERE cs2.hex_name=cs.hex_name AND cs2.sampled_at_ms<=(SELECT m FROM now_pt)
                       ORDER BY sampled_at_ms DESC LIMIT 1)
         ),
         earlier AS (
           SELECT hex_name, warden_casualties w, colonial_casualties c
           FROM casualty_samples cs
           WHERE id = (SELECT id FROM casualty_samples cs2
                       WHERE cs2.hex_name=cs.hex_name AND cs2.sampled_at_ms<=(SELECT m FROM ago_pt)
                       ORDER BY sampled_at_ms DESC LIMIT 1)
         )
    SELECT h.hex_name,
           COALESCE(l.w,0) - COALESCE(e.w,0) AS dw,
           COALESCE(l.c,0) - COALESCE(e.c,0) AS dc
    FROM hexes h
    LEFT JOIN latest  l USING (hex_name)
    LEFT JOIN earlier e USING (hex_name)
    """
    return {r[0]: (r[1], r[2]) for r in c.execute(q, (window_ms,))}


def hex_chronology(c, hex_name):
    h = c.execute("SELECT * FROM hexes WHERE hex_name=?", (hex_name,)).fetchone()
    if not h:
        return None
    rows = c.execute(
        "SELECT sampled_at_ms, warden_casualties, colonial_casualties, warden_rate,"
        " colonial_rate, source FROM casualty_samples WHERE hex_name=?"
        " ORDER BY sampled_at_ms", (hex_name,)
    ).fetchall()
    if not rows:
        return {"hex": dict(h), "samples": 0}

    first_blood = next(
        (r for r in rows if (r["warden_casualties"] or 0) + (r["colonial_casualties"] or 0) > 0),
        None,
    )
    peak = max(rows, key=lambda r: max(r["warden_rate"] or 0, r["colonial_rate"] or 0))
    latest = rows[-1]
    return {
        "hex_name": h["hex_name"],
        "display_name": h["display_name"],
        "sector": h["sector"],
        "region_id": h["region_id"],
        "samples": len(rows),
        "first_blood_utc": _ts(first_blood["sampled_at_ms"]) if first_blood else None,
        "peak_combat_utc": _ts(peak["sampled_at_ms"]),
        "peak_warden_rate_per_hr": peak["warden_rate"],
        "peak_colonial_rate_per_hr": peak["colonial_rate"],
        "current_warden_kia": latest["warden_casualties"],
        "current_colonial_kia": latest["colonial_casualties"],
        "current_total_kia": (latest["warden_casualties"] or 0) + (latest["colonial_casualties"] or 0),
        "last_sample_utc": _ts(latest["sampled_at_ms"]),
    }


def _ts(ms):
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


# ── Headline generator ────────────────────────────────────────────────────
def generate_headlines(c):
    hexes = c.execute("SELECT hex_name, display_name, sector FROM hexes").fetchall()
    names = {r["hex_name"]: (r["display_name"], r["sector"]) for r in hexes}
    latest = latest_by_hex(c)
    deltas = delta_24h_by_hex(c)
    totals = sector_totals(c)

    heads = []
    # 1. Bloodiest hex overall
    bloodiest = max(latest.values(), key=lambda r: r["total_casualties"] or 0)
    if bloodiest["total_casualties"]:
        heads.append(
            f"BLOOD IN {bloodiest['display_name'].upper()}: "
            f"{bloodiest['total_casualties']:,} DEAD IN {SECTOR_NAMES[bloodiest['sector']].upper()}"
        )

    # 2. Hottest 24h front
    hot = max(deltas.items(), key=lambda kv: sum(kv[1]))
    hot_name, (dw, dc) = hot
    if dw + dc > 0:
        disp, sec = names[hot_name]
        heads.append(
            f"{disp.upper()} BURNS: {dw + dc:,} fresh casualties in 24 hours "
            f"({SECTOR_NAMES[sec]})"
        )

    # 3. Calmest sector
    if totals:
        quietest = min(totals, key=lambda r: r["total_kia"])
        heads.append(
            f"{SECTOR_NAMES[quietest['sector']].upper()} QUIET: "
            f"only {quietest['total_kia']:,} casualties — lowest of the three fronts"
        )

    # 4. Sector with biggest 24h swing
    by_sector_24h = {}
    for hn, (dw, dc) in deltas.items():
        sec = names[hn][1]
        by_sector_24h[sec] = by_sector_24h.get(sec, [0, 0])
        by_sector_24h[sec][0] += dw; by_sector_24h[sec][1] += dc
    if by_sector_24h:
        hot_sec, (dw, dc) = max(by_sector_24h.items(), key=lambda kv: sum(kv[1]))
        heads.append(
            f"{SECTOR_NAMES[hot_sec].upper()} ABLAZE: "
            f"{dw:,} Warden + {dc:,} Colonial killed in the last day"
        )

    # 5. Faction momentum
    war_w = sum(r["warden_casualties"] or 0 for r in latest.values())
    war_c = sum(r["colonial_casualties"] or 0 for r in latest.values())
    if war_w > war_c:
        heads.append(f"COLONIAL PUSH: Wardens take {war_w - war_c:,} more losses than Colonials across the war")
    elif war_c > war_w:
        heads.append(f"WARDEN PUSH: Colonials lose {war_c - war_w:,} more than Wardens across the war")

    return heads


# ── Endpoint builders ─────────────────────────────────────────────────────
def build_front_page(c):
    war = war_meta(c)
    heads = generate_headlines(c)
    latest = latest_by_hex(c)
    deltas = delta_24h_by_hex(c)
    bloodiest = max(latest.values(), key=lambda r: r["total_casualties"] or 0)
    hot_hex_name, (dw, dc) = max(deltas.items(), key=lambda kv: sum(kv[1]))
    hot_hex = latest[hot_hex_name]

    lead = {
        "headline": heads[0] if heads else None,
        "dateline": f"Day {war['day_of_war']}, War #{war['war_number']} — {SECTOR_NAMES.get(bloodiest['sector'], bloodiest['sector']).upper()}",
        "body": (
            f"The {bloodiest['display_name']} hex has become the bloodiest ground of the war, "
            f"with {bloodiest['total_casualties']:,} confirmed casualties — "
            f"{bloodiest['warden_casualties']:,} Warden and {bloodiest['colonial_casualties']:,} Colonial. "
            f"Meanwhile {hot_hex['display_name']} leads 24-hour losses with "
            f"{dw + dc:,} fresh casualties, suggesting active operations continue there."
        ),
    }

    return {
        "masthead": MASTHEAD.format(war=war["war_number"]),
        "issue_date": datetime.now(timezone.utc).date().isoformat(),
        "war": war,
        "lead_story": lead,
        "headlines": heads[1:],
        "sector_totals": sector_totals(c),
    }


def build_dispatches(c, sector):
    war = war_meta(c)
    if sector == "all":
        sectors = ["west", "center", "east"]
    elif sector in ("west", "center", "east"):
        sectors = [sector]
    else:
        return {"error": "sector must be west|center|east|all"}

    latest = latest_by_hex(c)
    deltas = delta_24h_by_hex(c)
    out = {
        "masthead": MASTHEAD.format(war=war["war_number"]),
        "war_day": war["day_of_war"],
        "dispatches": [],
    }
    for sec in sectors:
        hex_rows = [h for h in latest.values() if h["sector"] == sec]
        if not hex_rows:
            continue
        hex_rows.sort(key=lambda r: r["total_casualties"] or 0, reverse=True)
        total_w = sum(h["warden_casualties"] or 0 for h in hex_rows)
        total_c = sum(h["colonial_casualties"] or 0 for h in hex_rows)
        d_w = sum(deltas.get(h["hex_name"], (0, 0))[0] for h in hex_rows)
        d_c = sum(deltas.get(h["hex_name"], (0, 0))[1] for h in hex_rows)
        top3 = hex_rows[:3]

        lede = (
            f"From the {SECTOR_NAMES[sec]}: {total_w + total_c:,} dead so far in War #{war['war_number']}, "
            f"{total_w:,} Warden against {total_c:,} Colonial. "
            f"The last 24 hours added {d_w + d_c:,} more names to the rolls."
        )
        body = "The heaviest fighting remains in " + ", ".join(
            f"{h['display_name']} ({h['total_casualties']:,})" for h in top3
        ) + "."

        out["dispatches"].append({
            "sector": sec,
            "sector_name": SECTOR_NAMES[sec],
            "lede": lede,
            "body": body,
            "cumulative_warden_kia": total_w,
            "cumulative_colonial_kia": total_c,
            "delta_24h_warden": d_w,
            "delta_24h_colonial": d_c,
            "top_hexes": [
                {"hex": h["hex_name"], "display": h["display_name"],
                 "total_kia": h["total_casualties"] or 0,
                 "warden_kia": h["warden_casualties"] or 0,
                 "colonial_kia": h["colonial_casualties"] or 0}
                for h in top3
            ],
        })
    return out


def build_hex_diary(c, hex_name):
    chron = hex_chronology(c, hex_name)
    if chron is None:
        return {"error": f"unknown hex '{hex_name}'"}
    if chron.get("samples", 0) == 0:
        return {**chron, "story": f"No samples recorded for {hex_name}."}

    war = war_meta(c)
    first = chron["first_blood_utc"]
    peak_w, peak_c = chron["peak_warden_rate_per_hr"], chron["peak_colonial_rate_per_hr"]
    peak_rate = max(peak_w or 0, peak_c or 0)
    story = (
        f"War Diary, {chron['display_name']} ({SECTOR_NAMES.get(chron['sector'], chron['sector'])}). "
        f"First combat on {first}. "
        f"Peak fury reached {peak_rate}/hr (Warden {peak_w}/hr, Colonial {peak_c}/hr) at {chron['peak_combat_utc']}. "
        f"To date, {chron['current_total_kia']:,} dead — "
        f"{chron['current_warden_kia']:,} Warden, {chron['current_colonial_kia']:,} Colonial."
    )
    return {
        "masthead": MASTHEAD.format(war=war["war_number"]),
        "story": story,
        **chron,
    }


def build_headlines(c):
    return {
        "masthead": MASTHEAD.format(war=war_meta(c)["war_number"]),
        "issue_date": datetime.now(timezone.utc).date().isoformat(),
        "headlines": generate_headlines(c),
    }


ROUTES_INDEX = {
    "/paper": "★ The laid-out newspaper (print / PDF / PNG export)",
    "/editor": "★ Browser editor — write & manage your articles",
    "/api/feed": "Merged feed: your articles + auto war stories (JSON)",
    "/api/articles": "GET list / POST create your articles",
    "/api/articles/<id>": "GET / PUT / DELETE a single article",
    "/front-page": "Lead story + headlines + war summary (raw JSON)",
    "/dispatches?sector=west|center|east|all": "Per-sector narrative reports",
    "/hex/<hex_name>": "Per-hex war diary (e.g. /hex/DeadLandsHex)",
    "/headlines": "Auto-generated wire headlines",
}


# ── HTTP ───────────────────────────────────────────────────────────────────
_CTYPES = {".html": "text/html; charset=utf-8", ".css": "text/css",
           ".js": "application/javascript", ".png": "image/png",
           ".jpg": "image/jpeg", ".svg": "image/svg+xml"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a, **k): pass

    # -- response helpers -----------------------------------------------------
    def _json(self, status, obj):
        body = json.dumps(obj, indent=2, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path):
        if not path.is_file():
            return self._json(404, {"error": f"missing file {path.name}"})
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", _CTYPES.get(path.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return None

    def _article_id(self):
        """Return (id:int|None, sub:str|None) parsed from /api/articles/<id>[/<sub>]."""
        rest = urlparse(self.path).path[len("/api/articles/"):].strip("/")
        if not rest:
            return None, None
        parts = rest.split("/")
        try:
            return int(parts[0]), (parts[1] if len(parts) > 1 else None)
        except ValueError:
            return None, None

    # -- methods --------------------------------------------------------------
    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)

        # Static web pages
        if u.path in ("/paper", "/editor"):
            return self._file(WEB / f"{u.path.strip('/')}.html")
        if u.path.startswith("/web/"):
            return self._file(WEB / u.path[len("/web/"):])

        c = conn()
        try:
            if u.path == "/":
                return self._json(200, {"newspaper": MASTHEAD.format(war=war_meta(c)["war_number"]),
                                        "routes": ROUTES_INDEX})
            # Editorial API
            if u.path == "/api/feed":
                with closing(art.conn()) as ac:
                    include_auto = (qs.get("auto") or ["1"])[0] != "0"
                    return self._json(200, {
                        "masthead": MASTHEAD.format(war=war_meta(c)["war_number"]),
                        "issue_date": datetime.now(timezone.utc).date().isoformat(),
                        "war": war_meta(c),
                        "articles": art.feed(ac, c, include_auto=include_auto),
                    })
            if u.path == "/api/articles":
                with closing(art.conn()) as ac:
                    return self._json(200, {"articles": art.list_articles(ac)})
            if u.path.startswith("/api/articles/"):
                aid, _ = self._article_id()
                if aid is None:
                    return self._json(400, {"error": "bad article id"})
                with closing(art.conn()) as ac:
                    a = art.get_article(ac, aid)
                return self._json(200 if a else 404, a or {"error": "not found"})

            # Raw war JSON (unchanged)
            if u.path == "/front-page":
                return self._json(200, build_front_page(c))
            if u.path == "/dispatches":
                return self._json(200, build_dispatches(c, (qs.get("sector") or ["all"])[0]))
            if u.path == "/headlines":
                return self._json(200, build_headlines(c))
            if u.path.startswith("/hex/"):
                hx = u.path[len("/hex/"):]
                result = build_hex_diary(c, hx)
                return self._json(200 if "error" not in result else 404, result)
            return self._json(404, {"error": "not found", "routes": list(ROUTES_INDEX)})
        finally:
            c.close()

    def do_POST(self):
        u = urlparse(self.path)
        data = self._read_json()
        if data is None:
            return self._json(400, {"error": "invalid JSON body"})
        if u.path == "/api/articles":
            with closing(art.conn()) as ac:
                return self._json(201, art.create_article(ac, data))
        if u.path.startswith("/api/articles/"):
            aid, sub = self._article_id()
            if aid is not None and sub == "move":
                with closing(art.conn()) as ac:
                    a = art.move_article(ac, aid, data.get("direction", "up"))
                return self._json(200 if a else 404, a or {"error": "not found"})
        return self._json(404, {"error": "not found"})

    def do_PUT(self):
        aid, _ = self._article_id()
        if not urlparse(self.path).path.startswith("/api/articles/") or aid is None:
            return self._json(404, {"error": "not found"})
        data = self._read_json()
        if data is None:
            return self._json(400, {"error": "invalid JSON body"})
        with closing(art.conn()) as ac:
            a = art.update_article(ac, aid, data)
        return self._json(200 if a else 404, a or {"error": "not found"})

    def do_DELETE(self):
        aid, _ = self._article_id()
        if not urlparse(self.path).path.startswith("/api/articles/") or aid is None:
            return self._json(404, {"error": "not found"})
        with closing(art.conn()) as ac:
            ok = art.delete_article(ac, aid)
        return self._json(200 if ok else 404, {"deleted": ok, "id": aid})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8181)
    args = p.parse_args()
    if not DB.exists():
        print(f"ERROR: {DB} missing. Run `python3 build_war_db.py` first.", file=sys.stderr)
        sys.exit(1)
    srv = HTTPServer((args.host, args.port), Handler)
    print(f"{MASTHEAD.format(war='?')} — serving http://{args.host}:{args.port}/")
    for path, desc in ROUTES_INDEX.items():
        print(f"  {path:<45} {desc}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
