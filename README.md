# Publisheur

A small collaborative newspaper publisher for Foxhole / 2ᵉ REI. Write articles in
a browser, they're stored in **Supabase**, laid out automatically on a vintage
front page, and published to a **print-grade PDF + images** via **Scribus**.

The default edition shipped here is ***Le Petit Daihbi*** (Journal du Front), but
Publisheur builds custom or shared papers for any newsroom.

```
web/        Static site (GitHub Pages): editor + paper + landing
  index.html    Landing page
  editor.html   Newsroom — write/manage articles (email login)
  paper.html    The laid-out paper (web view, print-to-PDF, PNG)
  daihbi.js     Shared Supabase data + auth layer
  config.js     ← your Supabase URL + anon key go here
supabase/
  schema.sql    Run once in the Supabase SQL editor (tables, RLS, storage)
publish/        Scribus publisher (print-grade PDF/PNG)  ← built next
.github/workflows/pages.yml   Auto-deploy web/ to GitHub Pages
```

## 1. Set up Supabase (backend)

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

## 2. Deploy the site (frontend)

Push to GitHub, then **Settings → Pages → Source: GitHub Actions**. The
`pages.yml` workflow publishes `web/` on every push to `main`. Collaborators
just visit the URL and sign in with their email.

**Run locally instead:**
```bash
cd web && python3 -m http.server 8200   # → http://127.0.0.1:8200
```

## 3. Write & publish

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

  **Layout note:** prominence maps to typography — `lead` is a full-width,
  drop-capped 3-column hero; `major`/`minor`/`brief` flow through a 5-column
  well across as many A3 pages as needed.

## Foxhole war-wire

Auto-generated war stories (bloodiest hex, sector dispatches, casualty
headlines) come from the local `foxhole_war.db`. Because that database is local,
the war-wire is merged at **publish time** by the Scribus step — not in the
browser, which only shows human-written articles from Supabase.
