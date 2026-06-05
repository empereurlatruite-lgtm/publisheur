# Publisheur

> *« Le 120 est bon marché, le moral est précieux. »*
> **120mm is cheap, morale is expensive.**

**Publisheur** is a collaborative newspaper platform for the **francophone Warden
press** of *Foxhole* — a shared newsroom where players from many regiments write
articles together and the layout happens **automatically**.

Write in the browser → articles are stored in **Supabase** → Publisheur lays them
out on a real front page and exports a **print-grade PDF, page images, and a web
edition** via **Scribus**. No Canva, no fighting with text boxes, no broken
mise en page after compression.

## Why it exists

Across the Warden francophonie there are already several papers — *L'Écho du
Front*, *L'Horizon Bleu*, *Le Petit Daihbi*, and more — each carried by one or two
people. The writing is the fun part. **The layout is what kills it:** doing the
*mise en page* by hand, regiment after regiment, issue after issue, is too much
work for too few hands, and good editions die after two issues.

Publisheur turns that around so a regiment can document its war effort — heroic
soldiers, operations, the bloodiest hexes — without anyone burning out on layout.
More contributors from more regiments means better information, recognition for
everyone's part in the war, and a real morale boost for the whole front.

## How it works — the newsroom

Two kinds of contributors share one platform:

- **Journalists** — write, edit, and curate the articles, set each story's
  prominence, and publish the edition.
- **Reporters** — members of a regiment who send field reports from their own
  unit: an operation, a heroic soldier, a notable fight. Journalists pick up those
  dispatches to fill the paper.

Every regiment can keep **its own title** (its edition) *and* feed a **common
Warden journal** — the same articles can serve a regiment's paper and the shared
one. *Le Petit Daihbi* (Journal du Front · 2ᵉ REI) is the reference edition
shipped in this repo.

## Editorial charter

A shared paper only works if everyone trusts the tone. The ground rules:

- **Apolitique** — no real-world politics.
- **Pro-Warden** — we support the war effort, all regiments welcome.
- **No gratuitous attacks**, no settling scores between units.
- **No point Godwin.**

## What works today

- **Browser newsroom** (`web/editor.html`) — email magic-link login, write/edit
  articles, reorder them, live preview, real-time sync between collaborators.
- **Auto-layout** — a story's **prominence** (`lead` · `major` · `minor` ·
  `brief`) drives the typography: `lead` is a full-width, drop-capped 3-column
  hero; the rest auto-flow through a 5-column well across as many A3 pages as
  needed.
- **Three outputs** — web edition (`paper.html`), quick browser PDF/PNG, and a
  **print-grade PDF + page images** from the Scribus publisher.
- **Multiple editions** — switch the `ISSUE` value to run separate papers /
  titles from the same newsroom.
- **Foxhole war-wire** — auto-generated war stories (bloodiest hex, sector
  dispatches, casualty headlines) merged in at publish time.

## Roadmap — the bigger vision

Ideas from the founding regiments, not built yet:

- **Reporter roles & channels** — distinct journalist/reporter permissions, each
  regiment with its own intake feed (today every signed-in user is an equal
  collaborator).
- **Reporters assigned to OPs** — cover a specific operation as it happens.
- **Manufacturer ads** — paid/sponsor slots in the layout for in-game makers.
- **F1 leaderboard** — collect everyone's `F1` stat screenshots and compile a
  ranking automatically (candidate: a local **Qwen3** model doing the read +
  tally).

---

## Setup

```
web/        Static site (GitHub Pages): editor + paper + landing
  index.html    Landing page
  editor.html   Newsroom — write/manage articles (email login)
  paper.html    The laid-out paper (web view, print-to-PDF, PNG)
  daihbi.js     Shared Supabase data + auth layer
  config.js     ← your Supabase URL + anon key go here
supabase/
  schema.sql    Run once in the Supabase SQL editor (tables, RLS, storage)
publish/        Scribus publisher (print-grade PDF/PNG)
.github/workflows/pages.yml      Auto-deploy web/ to GitHub Pages
.github/workflows/publish.yml    Run the Scribus publisher in CI
```

### 1. Set up Supabase (backend)

1. Create a project at [supabase.com](https://supabase.com).
2. **SQL Editor → New query →** paste `supabase/schema.sql` → **Run**.
3. **Authentication → Providers →** enable **Email** (magic-link is simplest).
4. **Authentication → URL Configuration →** add your GitHub Pages URL
   (e.g. `https://USER.github.io/publisheur/`) as a redirect URL.
5. **Settings → API →** copy the **Project URL** and **anon public key** into
   `web/config.js`.

> The anon key is safe to commit — it's public by design. Row-Level Security
> (in `schema.sql`) is what protects the data. Never put the `service_role` key
> in `config.js`.

### 2. Deploy the site (frontend)

Push to GitHub, then **Settings → Pages → Source: GitHub Actions**. The
`pages.yml` workflow publishes `web/` on every push to `main`. Collaborators
just visit the URL and sign in with their email.

**Run locally instead:**
```bash
cd web && python3 -m http.server 8200   # → http://127.0.0.1:8200
```

### 3. Write & publish

- **Write:** open `/editor.html`, sign in, add articles. Pick a **prominence**
  per article — `lead` (front banner) · `major` (wide) · `minor` (column) ·
  `brief` (short item) — which drives the auto-layout. Changes sync live
  between collaborators.
- **Read / quick PDF:** `/paper.html` → **Print / PDF** (browser) or **PNG**.
- **Print-grade publish:** the Scribus publisher auto-flows everything into a
  real Scribus layout and exports a print-ready PDF + page images.

  ```bash
  cd publish && ./publish.sh            # → out/issue.pdf + out/page-*.png
  ./publish.sh special-1                # a named issue
  ```
  Needs `scribus`, `poppler-utils`, `xvfb`. It runs three steps:
  `build_issue.py` (gather articles → `out/issue.json`) → `layout.py` (Scribus
  Scripter, run headless via `xvfb-run scribus -g -ns -py`) → `pdftoppm` (PNG).

  **Source:** set `SUPABASE_URL` + `SUPABASE_KEY` to pull from the cloud;
  otherwise it falls back to the local `articles.db`. The Foxhole **war-wire**
  (`../../data-collection/foxhole_war.db`) is merged in unless `--no-wire`.

  **In CI:** `.github/workflows/publish.yml` runs the same publisher on demand
  (Actions → "Publish issue") and uploads the PDF/PNG as an artifact. Add
  `SUPABASE_URL` / `SUPABASE_KEY` as repo secrets. (CI has no `foxhole_war.db`,
  so it publishes Supabase articles only.)
