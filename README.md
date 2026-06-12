# Publisheur

> *« Le 120 est bon marché, le moral est précieux. »*

**Publisheur** est une plateforme de presse collaborative pour la **presse Warden
francophone** de *Foxhole* — une rédaction partagée où les rédacteurs de plusieurs
régiments **écrivent le texte** pendant que le **rédacteur en chef décide de la mise
en page**, et où le moteur fait **couler le texte tout seul** sur une vraie une.

On écrit dans le navigateur → les chroniques vont dans un **pool commun** sur
**Supabase** → chaque rédacteur en chef pioche dedans, compose son journal, et
Publisheur exporte une **édition web, un PDF prêt à imprimer et des images de
pages** via **Scribus**. Pas de Canva, pas de bagarre avec les zones de texte, pas
de mise en page cassée après compression.

## Pourquoi ce projet

Dans la francophonie Warden, il existe déjà plusieurs journaux — *L'Écho du
Front*, *L'Horizon Bleu*, *Le Petit Daihbi*, et d'autres — chacun porté par une
ou deux personnes. L'écriture, c'est la partie plaisante. **C'est la mise en page
qui tue tout :** faire la mise en page à la main, régiment après régiment, numéro
après numéro, c'est trop de travail pour trop peu de bras, et les bonnes éditions
meurent au bout de deux numéros.

Publisheur inverse la tendance : un régiment peut documenter son effort de guerre
— soldats héroïques, opérations, les hex les plus sanglants — sans que personne
ne s'épuise sur la mise en page. Plus de contributeurs, de plus de régiments,
c'est de meilleures informations, la reconnaissance de la part de chacun dans la
guerre, et un vrai gain de moral pour tout le front.

## Comment ça marche — l'écriture ≠ la mise en page

Publisheur sépare les deux métiers d'une vraie rédaction :

- **Rédacteur (chroniqueur)** — écrit une **chronique** : un texte (surtitre, titre,
  chapô, signature, corps) + une **photo suggérée** facultative. Il la **soumet au
  pool** commun. Il ne s'occupe **pas** de la mise en page.
- **Rédacteur en chef (éditeur)** — pioche dans le pool, **place** les chroniques
  qu'il veut dans son édition, et décide la **mise en page** sur un pupitre : la
  **une**, l'importance de chaque sujet (`une` · `majeur` · `mineur` · `brève`),
  l'ordre, la photo — puis **publie**.
- **Illustrateur** — alimente un **portfolio** d'images que les rédacteurs en chef
  placent dans leurs articles.
- **Lecteur** — lit **sans compte** ; commente avec un compte (Courrier des lecteurs).
- **Annonceur** — crée des **réclames** (recrutement, troc, parodie, créateur,
  fabricant) qu'un éditeur valide avant parution.

Le point clé : une **même chronique peut paraître dans plusieurs journaux**, mise
en page différemment dans chacun. On écrit une fois ; chaque rédaction choisit ce
qu'elle reprend et comment. Chaque régiment garde **son propre titre** (bandeau,
emblèmes, slogans) tout en puisant dans le **pool Warden commun**. *Le Petit
Daihbi* (Journal du Front · 2ᵉ REI) est l'édition de référence livrée dans ce dépôt.

## Charte éditoriale

Un journal partagé ne tient que si tout le monde a confiance dans le ton. Les
règles de base :

- **Apolitique** — pas de politique du monde réel.
- **Pro-Warden** — on soutient l'effort de guerre, tous les régiments sont les
  bienvenus.
- **Pas d'attaques gratuites**, pas de règlements de comptes entre unités.
- **Pas de point Godwin.**

## Ce qui fonctionne aujourd'hui

- **Rédaction dans le navigateur** (`web/editor.html`, « Mes chroniques ») —
  connexion par e-mail/mot de passe, brouillon → **Soumettre au pool**, photo
  suggérée, **historique des révisions** avec restauration, synchro temps réel.
- **Pupitre de mise en page** (`web/board.html`) — le **pool** à gauche → *Ajouter
  à la une* ; au centre les chroniques placées, groupées **LA UNE · MAJEURS ·
  MINEURS · BRÈVES** (régler l'importance, réordonner, choisir la photo, publier,
  retirer) ; **aperçu en direct** de la une à droite.
- **Mise en page automatique** — une fois l'importance fixée par l'éditeur, le
  moteur compose la page : la `une` est un bandeau pleine largeur sur 3 colonnes
  avec lettrine ; le reste s'écoule dans un bloc sur 5 colonnes, sur autant de
  pages A3 que nécessaire.
- **Plusieurs éditions** — chaque journal a son **titre, bandeau, emblèmes et
  slogans** (table `papers`), créés et gérés dans l'app (**Mes journaux**).
- **Rôles & social** — 5 rôles (lecteur / rédacteur / illustrateur / éditeur /
  annonceur), **Courrier des lecteurs** (lecture anonyme, commentaire connecté),
  **portfolio** des illustrateurs, **studio des réclames** validé par les éditeurs.
- **Quatre sorties** — édition web (`paper.html`), **feuilletage page à page**
  (`flip.html`, un livre animé des images de pages — sans PDF côté lecteur),
  PDF/PNG rapide via le navigateur, et un **PDF prêt à imprimer** depuis Scribus
  (bouton **🖨 PDF imprimable** → GitHub Action → déposé dans le stockage Supabase ;
  la même Action publie aussi les images de pages + un `manifest.json` pour le feuilletage).
- **War-wire Foxhole** — des sujets de guerre générés automatiquement (hex le plus
  sanglant, dépêches de secteur, titres de pertes) fusionnés à la publication Scribus.

## Feuille de route

Déjà réalisé : rôles & permissions, éditions multiples par régiment, pool de
chroniques + pupitre de mise en page, studio des réclames, export Scribus déclenché
depuis l'app. Reste à faire (idées des régiments fondateurs) :

- **Reporters assignés à des OP** — couvrir une opération précise en direct.
- **Glisser-déposer** dans le pupitre de mise en page (aujourd'hui : boutons ▲▼).
- **Réclames de fabricants** — emplacements sponsorisés/payants dans la mise en page.
- **Classement F1** — collecter les captures de stats `F1` de chacun et compiler un
  classement automatiquement (piste : un modèle **Qwen3** local pour la lecture +
  le décompte).

---

## Installation

```
web/        Site statique (GitHub Pages / Cloudflare Pages)
  index.html    Kiosque — feuilleter et filtrer les éditions
  editor.html   Rédaction — « Mes chroniques » (écrire) + « Mes journaux » (éditeurs)
  board.html    Mise en page — le pupitre du rédacteur en chef (pool → une)
  paper.html    Le journal mis en page (web, impression PDF, PNG)
  flip.html     Feuilletage page à page (livre animé des images de pages, sans PDF)
  illustrateurs.html  Tableau des illustrateurs (portfolio + validation des images)
  ads.html      Studio des réclames (annonceurs + validation éditeur)
  daihbi.js     Couche partagée Supabase (auth, Chronicles, Placements, Papers…)
  papers.js     Éditions de repli (fallback)
  config.js     ← votre URL Supabase + clé anon vont ici
  functions/api/export.js   Cloudflare Pages Function — déclenche l'export Scribus
supabase/     Migrations SQL — à coller dans l'éditeur SQL de Supabase, dans l'ordre :
  schema.sql · roles.sql · comments.sql · portfolio.sql · ads.sql ·
  papers.sql · revisions.sql · edited_by.sql · pool.sql ·
  transparency.sql · authors.sql · ad_placements.sql · media.sql ·
  i18n.sql · theme.sql · styles.sql · regiments.sql · columns.sql ·
  chronicle_edit.sql · ai_labels.sql · paper_purpose.sql · ai_zone.sql ·
  image_moderation.sql · img_pos.sql · img_crop.sql ·
  img_crop_tool.sql · illustrator_meta.sql · sections.sql · image_fill.sql ·
  templates.sql · dummy_layout.sql
publish/      Publieur Scribus (PDF/PNG prêt à imprimer, depuis les placements)
.github/workflows/  pages.yml (déploie web/ sur GitHub Pages) · publish.yml (Scribus en CI)
```

### 1. Configurer Supabase (backend)

1. Créez un projet sur [supabase.com](https://supabase.com).
2. **SQL Editor → New query →** collez chaque fichier de `supabase/` **dans
   l'ordre** ci-dessus (`schema.sql` d’abord, `dummy_layout.sql` en dernier) → **Run**.
3. **Authentication → Providers →** activez **Email** (mot de passe ou lien magique).
4. **Authentication → URL Configuration →** réglez **Site URL** sur l'URL publique
   et ajoutez-la en redirection (sinon les liens magiques retombent sur localhost).
5. **Settings → API →** copiez l'**URL du projet** et la **clé publique anon** dans
   `web/config.js`.

> La clé anon peut être committée sans risque — elle est publique par conception.
> C'est le Row-Level Security (dans les migrations) qui protège les données. Ne
> mettez jamais la clé `service_role` dans `config.js`.

### 2. Déployer le site (frontend)

**GitHub Pages :** poussez sur GitHub, puis **Settings → Pages → Source : GitHub
Actions**. Le workflow `pages.yml` publie `web/` à chaque push sur `main`.

**Cloudflare Pages** (pour les Pages Functions comme `/api/export`) :
```bash
rsync -a --exclude _devlogin.html web/ /tmp/deploy   # n'expose jamais le devlogin
cd /tmp/deploy && npx wrangler pages deploy . --project-name publisheur --branch main
```
> Déployez **depuis l'intérieur** du dossier (`wrangler pages deploy .`), sinon
> `functions/` est servi comme fichiers statiques et `/api/export` renvoie 405.

**En local :**
```bash
cd web && python3 -m http.server 8200   # → http://127.0.0.1:8200
```

### 3. Écrire, mettre en page & publier

- **Écrire (rédacteur) :** `/editor.html` → **Mes chroniques** → écrivez le texte
  + une photo suggérée → **Soumettre au pool**. Vous ne choisissez pas la mise en
  page : c'est le rôle de l'éditeur.
- **Mettre en page (éditeur) :** `/editor.html` → **Mes journaux** → *Mettre en
  page* → le pupitre `board.html` : tirez des chroniques du pool, réglez
  l'importance et l'ordre, ajoutez les photos, puis **Publier**.
- **Lire / PDF rapide :** `/paper.html` → **Imprimer / PDF** (navigateur) ou **PNG**.
- **Feuilleter :** `/flip.html?issue=…` (ou le bouton **📖 Feuilleter** dans la une
  et sur les cartes du kiosque) → un livre page à page des images de pages. Il faut
  d'abord avoir lancé l'export Scribus une fois pour générer les pages de l'édition.
- **Publication prête à imprimer :** le bouton **🖨 PDF imprimable** lance le
  publieur Scribus via une GitHub Action et dépose le PDF dans le stockage Supabase.
  En local :

  ```bash
  cd publish && ./publish.sh            # → out/issue.pdf + out/page-*.png
  ./publish.sh horizon-bleu             # un numéro nommé
  ```
  Nécessite `scribus`, `poppler-utils`, `xvfb`. Trois étapes : `build_issue.py`
  (rassemble les **placements publiés + chroniques** → `out/issue.json`) →
  `layout.py` (Scribus headless via `xvfb-run scribus -g -ns -py`) → `pdftoppm` (PNG).
  Définissez `SUPABASE_URL` + `SUPABASE_KEY` pour tirer du cloud.

---
---

# Publisheur (English)

> *« Le 120 est bon marché, le moral est précieux. »*
> **120mm is cheap, morale is expensive.**

**Publisheur** is a collaborative newspaper platform for the **francophone Warden
press** of *Foxhole* — a shared newsroom where writers from many regiments **write
the text** while the **editor-in-chief decides the layout**, and the engine
**flows the text automatically** onto a real front page.

Write in the browser → chronicles land in a shared **pool** on **Supabase** → each
editor-in-chief draws from it, composes their paper, and Publisheur exports a **web
edition, a print-grade PDF, and page images** via **Scribus**. No Canva, no fighting
with text boxes, no broken mise en page after compression.

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

## How it works — writing ≠ layout

Publisheur splits the two jobs of a real newsroom:

- **Writer (chronicler)** — writes a **chronicle**: the text (kicker, headline,
  deck, byline, body) + an optional **suggested photo**, then **submits it to the
  shared pool**. They do **not** do layout.
- **Editor-in-chief** — browses the pool, **places** the chronicles they want into
  their edition, and decides the **layout** on a board: the **front page**, each
  story's prominence (`lead` · `major` · `minor` · `brief`), order, and photo —
  then **publishes**.
- **Illustrator** — feeds a **portfolio** of images that editors place in stories.
- **Reader** — reads **without an account**; comments with one (letters page).
- **Advertiser** — creates **ads** (recruiting, trading, parody, content-creator,
  manufacturer) that an editor approves before they run.

The key idea: **one chronicle can run in several papers**, laid out differently in
each. Write it once; each newsroom chooses what to pick up and how. Every regiment
keeps **its own title** (banner, emblems, slogans) while drawing from the **common
Warden pool**. *Le Petit Daihbi* (Journal du Front · 2ᵉ REI) is the reference
edition shipped in this repo.

## Editorial charter

A shared paper only works if everyone trusts the tone. The ground rules:

- **Apolitique** — no real-world politics.
- **Pro-Warden** — we support the war effort, all regiments welcome.
- **No gratuitous attacks**, no settling scores between units.
- **No point Godwin.**

## What works today

- **Browser newsroom** (`web/editor.html`, "Mes chroniques") — email/password login,
  draft → **submit to the pool**, suggested photo, **revision history** with restore,
  real-time sync.
- **Mise-en-page board** (`web/board.html`) — the **pool** on the left → *add to the
  front page*; placed chronicles in the centre, grouped **LA UNE · MAJEURS · MINEURS
  · BRÈVES** (set prominence, reorder, pick the photo, publish, remove); **live
  preview** on the right.
- **Auto-layout** — once the editor sets prominence, the engine composes the page:
  `lead` is a full-width, drop-capped 3-column hero; the rest auto-flows through a
  5-column well across as many A3 pages as needed.
- **Multiple editions** — every paper has its own **title, banner, emblems and
  slogans** (`papers` table), created and managed in-app ("Mes journaux").
- **Roles & social** — 5 roles (reader / writer / illustrator / editor / advertiser),
  **letters page** (anon read, signed-in comment), illustrator **portfolio**,
  **ad studio** approved by editors.
- **Four outputs** — web edition (`paper.html`), a **page-by-page flipbook**
  (`flip.html`, an animated book of the page images — no PDF on the reader's side),
  quick browser PDF/PNG, and a **print-grade PDF** from Scribus (the **🖨 PDF
  imprimable** button → GitHub Action → dropped in Supabase Storage; the same Action
  also publishes the page images + a `manifest.json` for the flipbook).
- **Foxhole war-wire** — auto-generated war stories (bloodiest hex, sector
  dispatches, casualty headlines) merged in at Scribus publish time.

## Roadmap

Already built: roles & permissions, per-regiment multiple editions, the chronicle
pool + mise-en-page board, the ad studio, Scribus export triggered from the app.
Still to do (ideas from the founding regiments):

- **Reporters assigned to OPs** — cover a specific operation as it happens.
- **Drag-and-drop** in the layout board (today: ▲▼ buttons).
- **Manufacturer ads** — paid/sponsor slots in the layout for in-game makers.
- **F1 leaderboard** — collect everyone's `F1` stat screenshots and compile a
  ranking automatically (candidate: a local **Qwen3** model doing the read + tally).

---

## Setup

```
web/        Static site (GitHub Pages / Cloudflare Pages)
  index.html    Kiosque — browse & filter editions
  editor.html   Newsroom — "Mes chroniques" (write) + "Mes journaux" (editors)
  board.html    Mise-en-page — the editor-in-chief's board (pool → front page)
  paper.html    The laid-out paper (web view, print-to-PDF, PNG)
  flip.html     Page-by-page flipbook (animated book of the page images, no PDF)
  illustrateurs.html  Illustrators' board (portfolio + image approval)
  ads.html      Ad studio (advertisers + editor approval)
  daihbi.js     Shared Supabase layer (auth, Chronicles, Placements, Papers…)
  papers.js     Fallback editions
  config.js     ← your Supabase URL + anon key go here
  functions/api/export.js   Cloudflare Pages Function — triggers the Scribus export
supabase/     SQL migrations — paste into the Supabase SQL editor, in order:
  schema.sql · roles.sql · comments.sql · portfolio.sql · ads.sql ·
  papers.sql · revisions.sql · edited_by.sql · pool.sql ·
  transparency.sql · authors.sql · ad_placements.sql · media.sql ·
  i18n.sql · theme.sql · styles.sql · regiments.sql · columns.sql ·
  chronicle_edit.sql · ai_labels.sql · paper_purpose.sql · ai_zone.sql ·
  image_moderation.sql · img_pos.sql · img_crop.sql ·
  img_crop_tool.sql · illustrator_meta.sql · sections.sql · image_fill.sql ·
  templates.sql · dummy_layout.sql
publish/      Scribus publisher (print-grade PDF/PNG, from placements)
  legacy/     Dormant offline/war-wire fallback (pre-Supabase prototype) — see its README
.github/workflows/  pages.yml (deploy web/ to GitHub Pages) · publish.yml (Scribus in CI)
```

### 1. Set up Supabase (backend)

1. Create a project at [supabase.com](https://supabase.com).
2. **SQL Editor → New query →** paste each file in `supabase/` **in the order**
   above (`schema.sql` first, `dummy_layout.sql` last) → **Run**.
3. **Authentication → Providers →** enable **Email** (password or magic-link).
4. **Authentication → URL Configuration →** set **Site URL** to your public URL and
   add it as a redirect (otherwise magic links bounce to localhost).
5. **Settings → API →** copy the **Project URL** and **anon public key** into
   `web/config.js`.

> The anon key is safe to commit — it's public by design. Row-Level Security (in the
> migrations) protects the data. Never put the `service_role` key in `config.js`.

### 2. Deploy the site (frontend)

**GitHub Pages:** push to GitHub, then **Settings → Pages → Source: GitHub
Actions**. The `pages.yml` workflow publishes `web/` on every push to `main`.

**Cloudflare Pages** (for Pages Functions like `/api/export`):
```bash
rsync -a --exclude _devlogin.html web/ /tmp/deploy   # never publish the devlogin
cd /tmp/deploy && npx wrangler pages deploy . --project-name publisheur --branch main
```
> Deploy from **inside** the folder (`wrangler pages deploy .`), or `functions/`
> ships as static files and `/api/export` returns 405.

**Run locally:**
```bash
cd web && python3 -m http.server 8200   # → http://127.0.0.1:8200
```

### 3. Write, lay out & publish

- **Write (writer):** `/editor.html` → **Mes chroniques** → write the text + a
  suggested photo → **submit to the pool**. You don't choose the layout — that's the
  editor's job.
- **Lay out (editor):** `/editor.html` → **Mes journaux** → *Mettre en page* → the
  `board.html` board: pull chronicles from the pool, set prominence and order, add
  photos, then **Publish**.
- **Read / quick PDF:** `/paper.html` → **Print / PDF** (browser) or **PNG**.
- **Flip through:** `/flip.html?issue=…` (or the **📖 Feuilleter** button on the
  front page and the kiosque cards) → a page-by-page book of the page images. Run
  the Scribus export once first to generate the edition's pages.
- **Print-grade publish:** the **🖨 PDF imprimable** button runs the Scribus
  publisher via a GitHub Action and drops the PDF in Supabase Storage. Locally:

  ```bash
  cd publish && ./publish.sh            # → out/issue.pdf + out/page-*.png
  ./publish.sh horizon-bleu             # a named issue
  ```
  Needs `scribus`, `poppler-utils`, `xvfb`. Three steps: `build_issue.py` (gather
  **published placements + chronicles** → `out/issue.json`) → `layout.py` (Scribus
  headless via `xvfb-run scribus -g -ns -py`) → `pdftoppm` (PNG). Set `SUPABASE_URL`
  + `SUPABASE_KEY` to pull from the cloud.

---

## Database schema (reference snapshot)

A snapshot of the live `public` schema, for orientation. The **source of truth** is
the migration files in `supabase/` (applied in the order listed above) — this dump
is **context only**: table order and constraints below are **not** valid for direct
execution. Regenerate from Supabase when the schema changes.

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
  tags text[] NOT NULL DEFAULT '{}'::text[],   -- illustrator_meta.sql: type labels (historical/fanart/ai/official)
  source text NOT NULL DEFAULT ''::text,       -- illustrator_meta.sql: origin URL/credit
  license text NOT NULL DEFAULT ''::text,      -- illustrator_meta.sql: reuse terms
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
  article_id uuid,                       -- nullable since image_fill.sql (image-only filler placements)
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
  img_focus text NOT NULL DEFAULT ''::text,   -- img_crop_tool.sql: CSS object-position
  img_zoom real NOT NULL DEFAULT 1,           -- img_crop_tool.sql: focal-zoom scale
  section_id uuid,                            -- sections.sql: editor rubrique (null = default well)
  CONSTRAINT placements_pkey PRIMARY KEY (id),
  CONSTRAINT placements_article_id_fkey FOREIGN KEY (article_id) REFERENCES public.articles(id),
  CONSTRAINT placements_issue_fkey FOREIGN KEY (issue) REFERENCES public.papers(issue),
  CONSTRAINT placements_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.sections(id),
  CONSTRAINT placements_placed_by_fkey FOREIGN KEY (placed_by) REFERENCES auth.users(id)
);
CREATE TABLE public.sections (
  id uuid NOT NULL DEFAULT gen_random_uuid(),
  issue text NOT NULL,
  name text NOT NULL DEFAULT ''::text,
  position smallint NOT NULL DEFAULT 0,
  created_by uuid DEFAULT auth.uid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT sections_pkey PRIMARY KEY (id),
  CONSTRAINT sections_issue_fkey FOREIGN KEY (issue) REFERENCES public.papers(issue),
  CONSTRAINT sections_created_by_fkey FOREIGN KEY (created_by) REFERENCES auth.users(id)
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
