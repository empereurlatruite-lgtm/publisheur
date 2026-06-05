#!/usr/bin/env python3
"""articles.py — Editorial article store for LE PETIT DAIHBI.

A small SQLite store (`articles.db`) for hand-written articles, plus a merged
"feed" that combines your own articles with the auto-generated war stories from
newspaper.py. The web editor writes here; the layout page reads /api/feed.

The store lives in its own DB file so rebuilding foxhole_war.db (backfills, etc.)
never touches your writing.

Weights drive the layout:
    lead   — full-width banner headline + drop cap (one per issue, usually)
    major  — large headline, spans a couple of columns of attention
    minor  — standard column story
    brief  — short wire item / one-liner
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).parent / "articles.db"

WEIGHTS = ("lead", "major", "minor", "brief")
_WEIGHT_RANK = {w: i for i, w in enumerate(WEIGHTS)}

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    kicker     TEXT    DEFAULT '',
    headline   TEXT    NOT NULL,
    subhead    TEXT    DEFAULT '',
    byline     TEXT    DEFAULT '',
    body       TEXT    DEFAULT '',
    weight     TEXT    DEFAULT 'minor',
    image_url  TEXT    DEFAULT '',
    published  INTEGER DEFAULT 1,
    position   INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
"""


def _now():
    return datetime.now(timezone.utc).isoformat()


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c


def _clean_weight(w):
    w = (w or "minor").lower().strip()
    return w if w in WEIGHTS else "minor"


def _row_to_dict(r):
    d = dict(r)
    d["published"] = bool(d["published"])
    d["source"] = "db"
    return d


# ── CRUD ────────────────────────────────────────────────────────────────────
def list_articles(c, only_published=False):
    q = "SELECT * FROM articles"
    if only_published:
        q += " WHERE published = 1"
    rows = c.execute(q).fetchall()
    items = [_row_to_dict(r) for r in rows]
    items.sort(key=lambda a: (_WEIGHT_RANK.get(a["weight"], 9), a["position"], -a["id"]))
    return items


def get_article(c, aid):
    r = c.execute("SELECT * FROM articles WHERE id=?", (aid,)).fetchone()
    return _row_to_dict(r) if r else None


def create_article(c, data):
    now = _now()
    max_pos = c.execute("SELECT COALESCE(MAX(position), 0) FROM articles").fetchone()[0]
    cur = c.execute(
        """INSERT INTO articles
           (kicker, headline, subhead, byline, body, weight, image_url,
            published, position, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data.get("kicker", ""),
            data.get("headline", "Untitled"),
            data.get("subhead", ""),
            data.get("byline", ""),
            data.get("body", ""),
            _clean_weight(data.get("weight")),
            data.get("image_url", ""),
            1 if data.get("published", True) else 0,
            int(data.get("position", max_pos + 1)),
            now,
            now,
        ),
    )
    c.commit()
    return get_article(c, cur.lastrowid)


def update_article(c, aid, data):
    existing = get_article(c, aid)
    if not existing:
        return None
    fields = {
        "kicker": data.get("kicker", existing["kicker"]),
        "headline": data.get("headline", existing["headline"]),
        "subhead": data.get("subhead", existing["subhead"]),
        "byline": data.get("byline", existing["byline"]),
        "body": data.get("body", existing["body"]),
        "weight": _clean_weight(data.get("weight", existing["weight"])),
        "image_url": data.get("image_url", existing["image_url"]),
        "published": 1 if data.get("published", existing["published"]) else 0,
        "position": int(data.get("position", existing["position"])),
        "updated_at": _now(),
    }
    c.execute(
        """UPDATE articles SET kicker=?, headline=?, subhead=?, byline=?, body=?,
           weight=?, image_url=?, published=?, position=?, updated_at=? WHERE id=?""",
        (*fields.values(), aid),
    )
    c.commit()
    return get_article(c, aid)


def delete_article(c, aid):
    cur = c.execute("DELETE FROM articles WHERE id=?", (aid,))
    c.commit()
    return cur.rowcount > 0


def move_article(c, aid, direction):
    """Swap position with the adjacent article in the same weight band."""
    a = get_article(c, aid)
    if not a:
        return None
    siblings = [s for s in list_articles(c) if s["weight"] == a["weight"]]
    idx = next((i for i, s in enumerate(siblings) if s["id"] == aid), None)
    if idx is None:
        return a
    swap = idx - 1 if direction == "up" else idx + 1
    if 0 <= swap < len(siblings):
        other = siblings[swap]
        c.execute("UPDATE articles SET position=? WHERE id=?", (other["position"], aid))
        c.execute("UPDATE articles SET position=? WHERE id=?", (a["position"], other["id"]))
        c.commit()
    return get_article(c, aid)


# ── Auto war stories → article shape ────────────────────────────────────────
def auto_articles(war_conn):
    """Convert newspaper.py's generated war content into feed articles.

    Imported lazily so articles.py has no hard dependency on the war DB.
    """
    try:
        import newspaper as np
    except Exception:
        return []

    out = []
    try:
        fp = np.build_front_page(war_conn)
    except Exception:
        return []

    war = fp.get("war") or {}
    day = war.get("day_of_war", "?")
    wnum = war.get("war_number", "?")

    lead = fp.get("lead_story") or {}
    if lead.get("headline"):
        out.append({
            "id": "auto-lead",
            "source": "auto",
            "kicker": "FROM THE FRONT",
            "headline": _titleish(lead["headline"]),
            "subhead": lead.get("dateline", ""),
            "byline": "Wire Desk",
            "body": lead.get("body", ""),
            "weight": "lead",
            "image_url": "",
            "published": True,
        })

    # Sector dispatches → major/minor stories
    try:
        disp = np.build_dispatches(war_conn, "all").get("dispatches", [])
    except Exception:
        disp = []
    for i, d in enumerate(disp):
        out.append({
            "id": f"auto-disp-{d.get('sector', i)}",
            "source": "auto",
            "kicker": d.get("sector_name", "Dispatch").upper(),
            "headline": _titleish(d.get("sector_name", "Dispatch") + " — Latest from the Lines"),
            "subhead": "",
            "byline": "Field Correspondent",
            "body": (d.get("lede", "") + "\n\n" + d.get("body", "")).strip(),
            "weight": "major" if i == 0 else "minor",
            "image_url": "",
            "published": True,
        })

    # Remaining wire headlines → briefs
    for i, h in enumerate(fp.get("headlines", [])):
        out.append({
            "id": f"auto-brief-{i}",
            "source": "auto",
            "kicker": "WIRE",
            "headline": _titleish(h),
            "subhead": "",
            "byline": "",
            "body": "",
            "weight": "brief",
            "image_url": "",
            "published": True,
        })

    return out


def _titleish(s):
    """SHOUTY wire copy → headline case-ish (keep it punchy, not all-caps)."""
    if not s:
        return s
    # Split on first colon: keep a kicker-like prefix in caps small, title the rest.
    if s.isupper() or sum(ch.isupper() for ch in s) > len(s) * 0.6:
        return s.title()
    return s


# ── Merged feed ─────────────────────────────────────────────────────────────
def feed(art_conn, war_conn=None, include_auto=True):
    """Published DB articles + auto war stories, ordered for layout."""
    items = list_articles(art_conn, only_published=True)
    if include_auto and war_conn is not None:
        items = items + auto_articles(war_conn)
    items.sort(key=lambda a: (_WEIGHT_RANK.get(a.get("weight", "minor"), 9),
                              a.get("position", 0)))
    return items
