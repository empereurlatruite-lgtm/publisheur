# Publisheur — Claude Code context

Collaborative newspaper platform for the **francophone Warden press** of *Foxhole*.
Multiple régiments write articles together; the app auto-lays them out like a vintage
newspaper and outputs web / PDF / page images. See `README.md` for the full vision.

## Core model — writing ≠ layout (READ THIS FIRST)

The whole app is built around separating two editorial jobs:

- **Writers** write **chronicles** — just the *text* (kicker, headline, subhead,
  byline, body) + an optional **suggested photo**. They submit to a shared **pool**.
  A chronicle is NOT bound to any paper.
- **Editors-in-chief** decide **layout** — they pull chronicles from the pool into
  their edition (a **placement**) and set prominence / order / photo / publish on a
  mise-en-page board. **Editors do not edit a chronicle's text** (the author owns the
  words); writers do not set prominence/layout.
- **One chronicle can run in several papers**, laid out differently in each.

Data model: `articles` = chronicle (text, `status` = draft|submitted). `placements`
= an editor running a chronicle in an edition (`weight` lead/major/minor/brief,
`position`, `image_url` override, `published`; `unique(article_id, issue)`). A paper
= its **published placements** joined to chronicles, ordered by weight then position;
photo = `placement.image_url || article.image_url`.

## Architecture

- **Backend = Supabase** (Postgres + Auth + Storage + RLS + Realtime). No separate
  backend server. Project ref `atnmzlaiglmkykzryjar`. The anon key lives in
  `web/config.js` (public by design — **RLS** is what protects data).
- **Frontend = static site** in `web/`, talking directly to Supabase via
  `@supabase/supabase-js`. Deployed to **GitHub Pages** *and* **Cloudflare Pages**
  (`https://publisheur.pages.dev`). Cloudflare is needed for the Pages Function.
- **Print engine = Scribus**, scripted headless in `publish/` (`build_issue.py` →
  `layout.py` → `pdftoppm`), run locally or via the `publish.yml` GitHub Action.

### Key files
- `web/daihbi.js` — shared data/auth layer (IIFE → `window.Daihbi`). APIs: `Auth`,
  `Chronicles` (pool: listMine/listPool/get/create/update/remove/submit), `Placements`
  (layout: forIssue/publishedForIssue/add/update/remove/subscribe), `Papers`,
  `Profiles`, `Portfolio`, `Comments`, `Ads`, `Revisions`, `Media`.
- `web/editor.html` — **writer workspace** ("Mes chroniques", text + suggested photo)
  + editors' "Mes journaux" dashboard.
- `web/board.html` — **editor mise-en-page board** (pool → placements → publish).
- `web/paper.html` — the rendered paper (from placements). `web/index.html` — kiosque.
- `web/ads.html` — ad studio. `web/papers.js` — fallback editions registry.
- `web/functions/api/export.js` — Cloudflare Pages Function: verifies an editor JWT,
  dispatches `publish.yml` to render the print PDF.
- `supabase/*.sql` — migrations, applied by pasting into the Supabase SQL Editor **in
  order**: `schema → roles → comments → portfolio → ads → papers → revisions →
  edited_by → pool → transparency → authors → ad_placements → media → i18n →
  theme → styles → regiments`.
  (`i18n` adds content `lang` to articles/ads/papers + `preferred_lang`/`ui_lang`
  to profiles, and opens chronicle writing to any signed-in user — editors still
  publish. `theme` adds `papers.theme` — the per-edition visual skin the
  rédacteur en chef picks; theme keys live in `web/themes.js`, applied in
  `paper.html`. **Required**: until it's run, saving any paper setting fails,
  since `Papers.update/create` now write the `theme` column.
  `styles` adds a `styles` table (owner-scoped writes, public read) for **custom
  styles** the editor creates on the board's 🎨 picker ("+ Créer un style…"):
  palette + fonts + photo stored as a `def` JSON. A paper points at one via
  `papers.theme = "style:<id>"`; `paper.html` applies the `def` as inline CSS
  variables. **Required** for creating/using custom styles — until it's run, the
  board's create-style modal can't save and `Styles.list()` 404s, **but the page
  degrades gracefully** (built-in themes still work; `paper.html` only queries
  the table when a paper actually uses a `style:` theme).
  `regiments` adds a `regiments` table (public read, any signed-in user may
  insert) for a **user-extensible régiment list**: `Daihbi.Regiments.list()`
  merges `papers.js`' `DAIHBI_CLANS` defaults with these rows, and the régiment
  pickers in `editor.html` (chronicle source, journal Régiment, profile) get a
  "＋ Ajouter un régiment…" option. Degrades to the defaults if not run.)

## Roles
`reader` (read anon, comment signed-in) · `writer` / `illustrator` (write chronicles;
illustrators also fill the portfolio) · `editor` (lay out + publish their papers;
scoped by `manages_issue(issue)` / `owns_issue(issue)`) · `annonceur` (ad studio).
**Since the `i18n` migration, *any* signed-in user can write chronicles AND post
réclames** (the role labels are now hints, not a write gate); editors still control
what runs — they publish chronicles and approve ads. Content is multilingual: every
chronicle/ad/paper has a `lang`; readers filter the kiosque by language.

## Working rules
- **Git/GitHub:** committing & pushing IS allowed here (Marcel authed `gh` for this).
  Push as the **empereurlatruite-lgtm** account — run `gh auth switch --user
  empereurlatruite-lgtm` first (his main `TimeKidGray` can't push to this repo). End
  commit messages with the `Co-Authored-By: Claude …` trailer.
- **Deploy to Cloudflare from INSIDE the staged dir**, excluding the devlogin:
  `rsync -a --exclude _devlogin.html web/ /tmp/publisheur_deploy && cd /tmp/publisheur_deploy && npx wrangler pages deploy . --project-name publisheur --branch main`.
  Deploying from elsewhere ships `functions/` as static files → `/api/export` 405s.
- **Never** put the `service_role` key in `config.js` (anon key only). **Never**
  publish `web/_devlogin.html` (gitignored; has test creds).
- **SQL migrations:** the anon key can't run DDL — write the `.sql` file, then have
  Marcel paste it into the Supabase SQL Editor (copy to clipboard with `xclip`).
- **Verify headless** when changing UI/layout: serve `web/` (`python3 -m http.server
  8012`) and screenshot with `google-chrome --headless=new --screenshot`. Use
  `web/_devlogin.html` (redirects to the editor) for an authenticated session.

## Test fixtures
- Local dev login: `web/_devlogin.html` → `reporter@publisheur.test` / `Publisheur!2026`
  (an editor who owns the seed editions: `current`, `horizon-bleu`, `echo-du-front`).

## Pending (user-side, can't be done via API)
- Supabase **Auth → Confirm email → OFF** (smooth self-signup; magic-link else bounces).
- For the 🖨 print button: Cloudflare Pages secret **`GITHUB_TOKEN`** (fine-grained
  PAT, Actions r+w) + GitHub repo secrets **`SUPABASE_URL` / `SUPABASE_KEY` /
  `SUPABASE_SERVICE_KEY`**.
