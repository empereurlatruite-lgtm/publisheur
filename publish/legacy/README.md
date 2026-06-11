# publish/legacy — dormant offline / war-wire fallback

These two modules predate the current architecture (Supabase + static `web/` +
Scribus). They are the **original** Publisheur prototype: a standalone Python HTTP
newspaper API over local SQLite. They are kept only as a graceful fallback for the
print pipeline — **not part of the live product** and not served anywhere.

- **`articles.py`** — a local SQLite article store (`articles.db`) + a merged "feed"
  that combines hand-written articles with auto-generated war stories.
- **`newspaper.py`** — a fictitious wartime newspaper HTTP API that reads a Foxhole
  war DB (`foxhole_war.db`) and shapes it into newspaper endpoints (the "war-wire").

## Who uses them

Only `publish/build_issue.py`, lazily and defensively:

- `fetch_local()` — full fallback when there are **no Supabase creds** (or the
  Supabase fetch throws): reads `articles.db` via `articles.py`.
- `war_wire()` — merges auto-generated war-wire stories from `newspaper.py` into the
  issue (default; skipped with `--no-wire`).
- `war_meta()` — the "WAR No. … DAY …" masthead line from the war DB.

Every call is wrapped in `try/except`: when the SQLite DBs are absent (they are **not**
in the repo), each returns `[]` / `None` and prints a one-line warning. So in the real
CI flow (Supabase creds present, no local DBs) these contribute nothing to the output.

## If you want to remove them

Delete this folder **and** strip the `fetch_local` / `war_wire` / `war_meta` branches
(plus the `sys.path.insert(... "legacy")`) from `publish/build_issue.py`; otherwise the
lazy imports will raise. That makes the pipeline Supabase-only.
