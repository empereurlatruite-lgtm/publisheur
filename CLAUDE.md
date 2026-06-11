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
  `publish/legacy/` holds the dormant pre-Supabase prototype (`newspaper.py` +
  `articles.py`) — a SQLite offline/war-wire **fallback** imported lazily by
  `build_issue.py` and failing gracefully (its DBs aren't in the repo); not the
  live path. See `publish/legacy/README.md`.

### Key files
- `web/daihbi.js` — shared data/auth layer (IIFE → `window.Daihbi`). APIs: `Auth`,
  `Chronicles` (pool: listMine/listPool/get/create/update/remove/submit), `Placements`
  (layout: forIssue/publishedForIssue/add/update/remove/subscribe), `Papers`,
  `Profiles`, `Portfolio`, `Comments`, `Ads`, `Revisions`, `Media`.
- `web/editor.html` — **writer workspace** ("Mes chroniques", text + suggested photo)
  + editors' "Mes journaux" dashboard.
- `web/board.html` — **editor mise-en-page board** (pool → placements → publish).
  Single-click a story/ad → layout dock; **double-click** (preview or pool card)
  → in-place **edit modal** (chronicle text incl. ✦ Rédigé/Traduit par IA toggles;
  or réclame content + approve). Pool cards: single-click places, double-click edits.
- `web/paper.html` — the rendered paper (from placements). `web/index.html` — kiosque.
- `web/flip.html` — **flipbook reader** (page-turn, no PDF for the reader): a
  [StPageFlip](https://github.com/Nodlik/StPageFlip) book of the Scribus page
  images. Reads `?issue=`, fetches `media/exports/<issue>/manifest.json`
  (`{issue,pages}`) from public Storage and loads `page-1.png … page-N.png`.
  Degrades gracefully to a "pas encore imprimée" notice (with web-view + kiosque
  links) when an edition has no published pages yet. Linked from the `paper.html`
  toolbar (📖 Feuilleter) and each kiosque card. The page PNGs + manifest are
  published by `publish.yml` (see below) — the print pipeline now feeds both the
  PDF *and* the flipbook.
- `web/illustrateurs.html` — **illustrators' board**: a flat **infinite-scroll image
  wall** (CSS-column masonry, ~48/page via an IntersectionObserver sentinel; author
  shown on hover). **Nav-bar filter chips** (by `tags` type — historical/fanart/ai/
  official — and by `clan`/régiment) + search rebuild the wall. **Double-click a tile
  → fullscreen** with an **info panel on the left** (caption, author, type tags,
  régiment, license, source link) + actions (copy-URL, open-source, approve, remove).
  Pending-moderation badges + Approve (`can_moderate`); **add-image modal**
  (`can_upload`): URL or `Media.upload`, plus author, type (tags), régiment, source,
  license, caption. Gated to editors + illustrators; linked from the editor nav
  (🎨 Illustrateurs). The `tags`/`source`/`license` columns come from
  `illustrator_meta.sql`.
- `web/ads.html` — ad studio. `web/papers.js` — fallback editions registry.
- `web/functions/api/export.js` — Cloudflare Pages Function: verifies an editor JWT,
  dispatches `publish.yml` to render the print PDF.
- `.github/workflows/publish.yml` — Scribus CI: gathers placements → lays out →
  PDF + page PNGs. Uploads `exports/<issue>.pdf` **and** the flipbook assets
  (`exports/<issue>/page-N.png` + `manifest.json`) to the public `media` bucket
  with the `SUPABASE_SERVICE_KEY`.
- `supabase/*.sql` — migrations, applied by pasting into the Supabase SQL Editor **in
  order**: `schema → roles → comments → portfolio → ads → papers → revisions →
  edited_by → pool → transparency → authors → ad_placements → media → i18n →
  theme → styles → regiments → columns → chronicle_edit → ai_labels →
  paper_purpose → ai_zone → image_moderation → img_pos → img_crop →
  img_crop_tool → illustrator_meta → sections → image_fill`.
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
  "＋ Ajouter un régiment…" option. Degrades to the defaults if not run.
  `columns` adds **editor-controlled layout**: `papers.grid_cols` (front-page
  well column count, 0 = auto), `placements.col_span` (how many columns an
  article spans, 0 = auto by weight) and `placements.img_cols` (photo width in
  columns — floats with text wrapping when narrower than the span, 0 = full
  width). Set on the board's ▦ Colonnes picker + the dock editor's Colonnes /
  Taille image rows; `paper.html` lays out the grid accordingly. All default to
  0, so editions are unchanged until an editor opts in — degrades gracefully if
  not run.
  `chronicle_edit` lets a managing editor edit a **chronicle's text** in place
  from the board (double-click a story in the preview or a pool card → edit
  modal), not just lay it out — relaxing the "author owns the words" rule for
  rédacteurs en chef. It re-adds an `art editor update` RLS policy scoped via
  **placements** (an editor may edit a chronicle placed in an edition they
  manage; the author keeps editing their own), and fixes `snapshot_article()` to
  `coalesce(issue,'')` so editing a pooled chronicle (null issue) no longer
  throws on the revision trigger. Edits are stamped (`last_edited_by`) and the
  prior version is archived to `article_revisions`. **Required** for the board's
  edit-chronicle modal to save.
  `ai_labels` adds `articles.ai_translated boolean` for the **transparency
  toggles** in the edit-chronicle modal: "✦ Rédigé par IA" (reuses the
  `source="IA"` sentinel) and "✦ Traduit par IA" (the new flag). `paper.html`
  renders a "✦ Traduit par IA" badge in the byline (content-language localized,
  like the other transparency labels). Defaults false; degrades gracefully.
  `paper_purpose` adds `papers.purpose text` — a short "what's this paper about"
  summary set in **Gérer le journal** and shown on the **kiosque** card. (The same
  manage modal also gained a language picker, a "Police du titre" shortcut that
  applies a custom style, and a delete button; the dashboard cards gained a
  **🔄 Republier** button that bumps the edition's published placements'
  `updated_at` so the kiosque re-flags it "à la une" — reusing the existing
  freshness ranking, no extra column.)
  `ai_zone` adds `papers.ai_zone boolean` — per-edition opt-in for the **separate
  "Rédigé par l'IA" sidebar**. Off by default: a chronicle flagged AI keeps its
  "✦ Rédigé par IA" badge but stays in the normal well (no layout split). On:
  `paper.html` pulls AI chronicles into the two-zone front layout. Toggled in
  Gérer le journal.
  `image_moderation` gates **image uploads + visibility**: `profiles.can_upload`
  / `profiles.can_moderate` (granted to specific users **via SQL**; editors keep
  both via `is_editor()`), plus `images.approved` / `media.approved`. Only
  `can_upload` users may write to the public **media** Storage bucket (the
  `storage.objects` "media auth write" insert policy now requires `can_upload()`)
  or insert portfolio/media rows; uploads start unapproved and the public sees
  **approved only** (owners/moderators see pending). `can_moderate` users approve
  pending images in the editor's Portfolio (pending badge + Approve). Caveat: the
  media bucket is public, so a raw object URL is still reachable — the gate is on
  *who can upload* and *what the app surfaces*; truly hiding bytes would need a
  private bucket + signed URLs.)
  `img_pos` adds `placements.img_pos` (`top`|`left`|`right`, default `top`) — a
  Word/Docs-style image position. `top` = banner across the story columns;
  `left`/`right` = the photo floats and the text wraps (single-column body).
  Set in the board dock **and** the double-click edit-chronicle modal's new
  **Mise en page** section (column span + image position + image size), alongside
  `col_span`/`img_cols` from columns.sql; `paper.html` `applyStorySpans()` renders it.
  `img_crop` adds `placements.img_crop` (`''` natural | `16x9`|`3x2`|`4x3`|`1x1`|`3x4`)
  — Word-style **crop-to-fill**: the photo is cropped (`object-fit:cover` + a forced
  `aspect-ratio`) to that ratio so blocks line up. Set via the **Recadrage** control
  in the dock + edit-modal layout section; applied in `applyStorySpans()`.)
  `img_crop_tool` adds `placements.img_focus` (CSS `object-position`, e.g.
  `"50% 35%"`) and `placements.img_zoom` (scale, 1 = none) for the **interactive
  crop tool** — a slide-up **image panel below the board preview** (`#imgPanel` in
  `board.html`), opened by **double-clicking a photo** in the preview or the **✎**
  corner button on hover (paper.html posts `daihbi-edit-image`). The panel has a
  drag-the-focal-point + zoom **crop stage** (WYSIWYG, mirrors the render) plus
  position / ratio / size / photo-source controls; each change saves to the
  placement and reloads the iframe so the change shows live (the double-click text
  modal used to hide the preview). In `paper.html` the **lead** now honours
  `img_pos="top"` as a **full-width banner above the text** (was always float-right);
  focus/zoom are applied to the lead banner and to story photos via a `.cropwrap`
  frame. Defaults are neutral, so editions are unchanged except leads, which move
  from float-right to a top banner unless the editor picks Gauche/Droite.
  Story photos in the preview also get a **drag-to-resize grip** (bottom-right
  corner, edit mode): dragging scales the photo live keeping its proportion and
  **snaps the width to the story's column span** (paper.html posts
  `daihbi-resize-image` → board sets `img_cols`). The snap uses the story's applied
  span (`data-applied`), not `--bodycols` (a floated photo forces that to 1).
  Every newspaper photo is a `<figure class="photo">` wrapping the image (or
  `.cropwrap`) **plus an author credit** (`<figcaption class="credit">Illustration :
  …</figcaption>`); the author is resolved by image URL via `Media.creditsFor()`
  (portfolio `images` then `media`, by `uploader_name`; anon sees approved provenance
  only) for the lead + stories. `web/illustrateurs.html` also gained a **double-click
  fullscreen lightbox** (image + caption + author).)

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

## Database schema (reference snapshot)

Live `public` schema, for orientation only. **Source of truth = the `supabase/*.sql`
migrations** (applied in the order under Architecture › Key files); this dump is
context only — table order/constraints aren't valid for direct execution, and RLS
policies aren't shown (they live in the migrations). Regenerate when the schema
changes.

```sql
-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.articles (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  issue text,
  kicker text NOT NULL DEFAULT ''::text,
  headline text NOT NULL DEFAULT 'Untitled'::text,
  subhead text NOT NULL DEFAULT ''::text,
  byline text NOT NULL DEFAULT ''::text,
  body text NOT NULL DEFAULT ''::text,
  weight text NOT NULL DEFAULT 'minor'::text CHECK (weight = ANY (ARRAY['lead'::text, 'major'::text, 'minor'::text, 'brief'::text])),
  image_url text NOT NULL DEFAULT ''::text,
  published boolean NOT NULL DEFAULT false,
  position integer NOT NULL DEFAULT 0,
  author_id uuid DEFAULT auth.uid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'draft'::text CHECK (status = ANY (ARRAY['draft'::text, 'submitted'::text])),
  last_edited_by uuid,
  author_avatar text NOT NULL DEFAULT ''::text,
  source text NOT NULL DEFAULT ''::text,
  lang text NOT NULL DEFAULT 'fr'::text,
  ai_translated boolean NOT NULL DEFAULT false,
  CONSTRAINT articles_pkey PRIMARY KEY (id),
  CONSTRAINT articles_author_id_fkey FOREIGN KEY (author_id) REFERENCES auth.users(id),
  CONSTRAINT articles_last_edited_by_fkey FOREIGN KEY (last_edited_by) REFERENCES auth.users(id)
);
CREATE TABLE public.profiles (
  id uuid NOT NULL,
  display_name text NOT NULL DEFAULT ''::text,
  role text NOT NULL DEFAULT 'reader'::text CHECK (role = ANY (ARRAY['reader'::text, 'writer'::text, 'illustrator'::text, 'editor'::text, 'annonceur'::text])),
  clan text NOT NULL DEFAULT ''::text,
  avatar_url text NOT NULL DEFAULT ''::text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  preferred_lang text NOT NULL DEFAULT ''::text,
  ui_lang text NOT NULL DEFAULT ''::text,
  can_upload boolean NOT NULL DEFAULT false,
  can_moderate boolean NOT NULL DEFAULT false,
  CONSTRAINT profiles_pkey PRIMARY KEY (id),
  CONSTRAINT profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id)
);
CREATE TABLE public.comments (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  issue text NOT NULL,
  article_id uuid,
  author_id uuid DEFAULT auth.uid(),
  author_name text NOT NULL DEFAULT ''::text,
  body text NOT NULL CHECK (char_length(body) >= 1 AND char_length(body) <= 2000),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT comments_pkey PRIMARY KEY (id),
  CONSTRAINT comments_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id),
  CONSTRAINT comments_author_id_fkey FOREIGN KEY (author_id) REFERENCES auth.users(id)
);
CREATE TABLE public.images (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  uploader_id uuid DEFAULT auth.uid(),
  uploader_name text NOT NULL DEFAULT ''::text,
  url text NOT NULL,
  caption text NOT NULL DEFAULT ''::text,
  clan text NOT NULL DEFAULT ''::text,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  mime text NOT NULL DEFAULT ''::text,
  bytes integer NOT NULL DEFAULT 0,
  width integer NOT NULL DEFAULT 0,
  height integer NOT NULL DEFAULT 0,
  approved boolean NOT NULL DEFAULT false,
  CONSTRAINT images_pkey PRIMARY KEY (id),
  CONSTRAINT images_uploader_id_fkey FOREIGN KEY (uploader_id) REFERENCES auth.users(id)
);
CREATE TABLE public.ads (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  advertiser_id uuid DEFAULT auth.uid(),
  advertiser_name text NOT NULL DEFAULT ''::text,
  title text NOT NULL DEFAULT ''::text,
  body text NOT NULL DEFAULT ''::text,
  category text NOT NULL DEFAULT 'fabricant'::text CHECK (category = ANY (ARRAY['recrutement'::text, 'troc'::text, 'parodie'::text, 'createur'::text, 'fabricant'::text])),
  maker text NOT NULL DEFAULT ''::text,
  link text NOT NULL DEFAULT ''::text,
  image_url text NOT NULL DEFAULT ''::text,
  issue text NOT NULL DEFAULT 'all'::text,
  status text NOT NULL DEFAULT 'draft'::text CHECK (status = ANY (ARRAY['draft'::text, 'review'::text, 'approved'::text, 'rejected'::text])),
  approved boolean NOT NULL DEFAULT false,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  lang text NOT NULL DEFAULT 'fr'::text,
  CONSTRAINT ads_pkey PRIMARY KEY (id),
  CONSTRAINT ads_advertiser_id_fkey FOREIGN KEY (advertiser_id) REFERENCES auth.users(id)
);
CREATE TABLE public.papers (
  issue text NOT NULL,
  name text NOT NULL DEFAULT ''::text,
  tagline text NOT NULL DEFAULT ''::text,
  plate text NOT NULL DEFAULT 'plate-fraktur'::text,
  ear jsonb NOT NULL DEFAULT '["", "", ""]'::jsonb,
  slogans jsonb NOT NULL DEFAULT '[]'::jsonb,
  emblem_left text NOT NULL DEFAULT ''::text,
  emblem_right text NOT NULL DEFAULT ''::text,
  clan text NOT NULL DEFAULT ''::text,
  owner_id uuid DEFAULT auth.uid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  theme text NOT NULL DEFAULT 'classic'::text,
  lang text NOT NULL DEFAULT 'fr'::text,
  grid_cols smallint NOT NULL DEFAULT 0,
  purpose text NOT NULL DEFAULT ''::text,
  ai_zone boolean NOT NULL DEFAULT false,
  CONSTRAINT papers_pkey PRIMARY KEY (issue),
  CONSTRAINT papers_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES auth.users(id)
);
CREATE TABLE public.paper_editors (
  issue text NOT NULL,
  editor_id uuid NOT NULL,
  CONSTRAINT paper_editors_pkey PRIMARY KEY (issue, editor_id),
  CONSTRAINT paper_editors_issue_fkey FOREIGN KEY (issue) REFERENCES public.papers(issue),
  CONSTRAINT paper_editors_editor_id_fkey FOREIGN KEY (editor_id) REFERENCES auth.users(id)
);
CREATE TABLE public.article_revisions (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  article_id uuid,
  issue text NOT NULL DEFAULT ''::text,
  kicker text,
  headline text,
  subhead text,
  byline text,
  body text,
  weight text,
  image_url text,
  published boolean,
  status text,
  author_id uuid,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  edited_by uuid,
  CONSTRAINT article_revisions_pkey PRIMARY KEY (id),
  CONSTRAINT article_revisions_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id)
);
CREATE TABLE public.placements (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  article_id uuid NOT NULL,
  issue text NOT NULL,
  weight text NOT NULL DEFAULT 'minor'::text CHECK (weight = ANY (ARRAY['lead'::text, 'major'::text, 'minor'::text, 'brief'::text])),
  position integer NOT NULL DEFAULT 0,
  image_url text NOT NULL DEFAULT ''::text,
  published boolean NOT NULL DEFAULT false,
  placed_by uuid DEFAULT auth.uid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  col_span smallint NOT NULL DEFAULT 0,
  img_cols smallint NOT NULL DEFAULT 0,
  img_pos text NOT NULL DEFAULT 'top'::text,
  img_crop text NOT NULL DEFAULT ''::text,
  CONSTRAINT placements_pkey PRIMARY KEY (id),
  CONSTRAINT placements_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id),
  CONSTRAINT placements_issue_fkey FOREIGN KEY (issue) REFERENCES public.papers(issue),
  CONSTRAINT placements_placed_by_fkey FOREIGN KEY (placed_by) REFERENCES auth.users(id)
);
CREATE TABLE public.media (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  uploader_id uuid DEFAULT auth.uid(),
  uploader_name text NOT NULL DEFAULT ''::text,
  url text NOT NULL,
  path text NOT NULL DEFAULT ''::text,
  folder text NOT NULL DEFAULT ''::text,
  mime text NOT NULL DEFAULT ''::text,
  bytes integer NOT NULL DEFAULT 0,
  width integer NOT NULL DEFAULT 0,
  height integer NOT NULL DEFAULT 0,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  approved boolean NOT NULL DEFAULT false,
  CONSTRAINT media_pkey PRIMARY KEY (id),
  CONSTRAINT media_uploader_id_fkey FOREIGN KEY (uploader_id) REFERENCES auth.users(id)
);
CREATE TABLE public.ad_placements (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  ad_id uuid NOT NULL,
  issue text NOT NULL,
  position integer NOT NULL DEFAULT 0,
  published boolean NOT NULL DEFAULT false,
  placed_by uuid DEFAULT auth.uid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT ad_placements_pkey PRIMARY KEY (id),
  CONSTRAINT ad_placements_ad_id_fkey FOREIGN KEY (ad_id) REFERENCES public.ads(id),
  CONSTRAINT ad_placements_issue_fkey FOREIGN KEY (issue) REFERENCES public.papers(issue),
  CONSTRAINT ad_placements_placed_by_fkey FOREIGN KEY (placed_by) REFERENCES auth.users(id)
);
CREATE TABLE public.styles (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  owner_id uuid NOT NULL DEFAULT auth.uid(),
  name text NOT NULL,
  def jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT styles_pkey PRIMARY KEY (id),
  CONSTRAINT styles_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES auth.users(id)
);
CREATE TABLE public.regiments (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text NOT NULL UNIQUE,
  created_by uuid DEFAULT auth.uid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT regiments_pkey PRIMARY KEY (id),
  CONSTRAINT regiments_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id)
);
```
