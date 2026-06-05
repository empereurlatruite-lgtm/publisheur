#!/usr/bin/env python3
"""build_issue.py — gather one issue's articles into publish/out/issue.json.

This runs in normal python3 (NOT inside Scribus). It is the data half of the
publisher: it collects the articles, merges the Foxhole war-wire, normalizes
everything, and writes a single JSON file that the Scribus script (layout.py)
then lays out.

Data source, in order of preference:
  1. Supabase  — if SUPABASE_URL + SUPABASE_KEY are set in the environment
                 (or read from ../web/config.js). Fetches published articles
                 for the issue via the PostgREST API (stdlib urllib only).
  2. Local DB  — ../articles.db (the legacy local store), if present.
Either way, the local war-wire (../../data-collection/foxhole_war.db) is merged
in unless --no-wire is given.

Usage:
    python3 build_issue.py [--issue current] [--no-wire] [--out out/issue.json]
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent                      # the project root (publisheur)
sys.path.insert(0, str(PARENT))           # so we can import articles.py / newspaper.py

WEIGHTS = ("lead", "major", "minor", "brief")
WRANK = {w: i for i, w in enumerate(WEIGHTS)}


# ── Supabase (optional) ─────────────────────────────────────────────────
def _creds_from_config():
    """Pull SUPABASE_URL / anon key out of ../web/config.js if present."""
    cfg = PARENT / "web" / "config.js"
    if not cfg.exists():
        return None, None
    txt = cfg.read_text()
    url = re.search(r'SUPABASE_URL:\s*"([^"]+)"', txt)
    key = re.search(r'SUPABASE_ANON_KEY:\s*"([^"]+)"', txt)
    url = url.group(1) if url else ""
    key = key.group(1) if key else ""
    if "YOUR-PROJECT" in url or "YOUR-ANON" in key or not url or not key:
        return None, None
    return url, key


def fetch_supabase(url, key, issue):
    endpoint = (
        f"{url.rstrip('/')}/rest/v1/articles"
        f"?issue=eq.{issue}&published=eq.true&select=*"
    )
    req = urllib.request.Request(endpoint, headers={
        "apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        rows = json.loads(r.read())
    for a in rows:
        a["source"] = "db"
    return rows


# ── Local DB + war-wire (via the legacy modules) ────────────────────────
def fetch_local(issue, include_wire):
    items = []
    try:
        import articles as art
        ac = art.conn()
        items = [a for a in art.list_articles(ac, only_published=True)]
    except Exception as e:
        print(f"  (local articles.db unavailable: {e})", file=sys.stderr)
    if include_wire:
        items += war_wire()
    return items


def war_wire():
    try:
        import articles as art
        import newspaper as np
        wc = np.conn()
        return art.auto_articles(wc)
    except Exception as e:
        print(f"  (war-wire unavailable: {e})", file=sys.stderr)
        return []


def war_meta():
    try:
        import newspaper as np
        return np.war_meta(np.conn())
    except Exception:
        return None


# ── Normalize + order ───────────────────────────────────────────────────
def normalize(a):
    return {
        "kicker": (a.get("kicker") or "").strip(),
        "headline": (a.get("headline") or "Untitled").strip(),
        "subhead": (a.get("subhead") or "").strip(),
        "byline": (a.get("byline") or "").strip(),
        "body": a.get("body") or "",
        "weight": a["weight"] if a.get("weight") in WEIGHTS else "minor",
        "image_url": (a.get("image_url") or "").strip(),
        "source": a.get("source", "db"),
        "position": a.get("position", 0),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issue", default="current")
    ap.add_argument("--no-wire", action="store_true", help="skip the Foxhole war-wire")
    ap.add_argument("--out", default=str(HERE / "out" / "issue.json"))
    args = ap.parse_args()

    include_wire = not args.no_wire

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not (url and key):
        url, key = _creds_from_config()

    if url and key:
        print(f"• Fetching from Supabase ({url}) …")
        try:
            items = fetch_supabase(url, key, args.issue)
            if include_wire:
                items += war_wire()
        except Exception as e:
            print(f"  Supabase fetch failed ({e}); falling back to local.", file=sys.stderr)
            items = fetch_local(args.issue, include_wire)
    else:
        print("• No Supabase creds — using local articles.db + war-wire.")
        items = fetch_local(args.issue, include_wire)

    items = [normalize(a) for a in items]
    items.sort(key=lambda a: (WRANK.get(a["weight"], 9), a["position"]))

    war = war_meta() or {}
    edition = (f"WAR No. {war['war_number']} · DAY {war['day_of_war']}"
               if war.get("war_number") is not None else f"ÉDITION « {args.issue} »")

    issue = {
        "masthead": "Le Petit Daihbi",
        "tagline": "Journal Quotidien du Front — « Tout pour le Régiment »",
        "issue": args.issue,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "date_fr": _fr_date(),
        "edition": edition,
        "war": war,
        "articles": items,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(issue, indent=2, ensure_ascii=False, default=str))
    print(f"✓ {len(items)} articles → {out}")
    by_w = {w: sum(1 for a in items if a['weight'] == w) for w in WEIGHTS}
    print(f"  weights: {by_w}")


_FR_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
              "août", "septembre", "octobre", "novembre", "décembre"]
_FR_DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def _fr_date():
    d = datetime.now(timezone.utc)
    return f"{_FR_DAYS[d.weekday()]} {d.day} {_FR_MONTHS[d.month - 1]} {d.year}"


if __name__ == "__main__":
    main()
