# Publisheur

> *« Le 120 est bon marché, le moral est précieux. »*

**Publisheur** est une plateforme de presse collaborative pour la **presse Warden
francophone** de *Foxhole* — une rédaction partagée où les joueurs de plusieurs
régiments écrivent des articles ensemble pendant que la **mise en page se fait
toute seule**.

On écrit dans le navigateur → les articles sont stockés dans **Supabase** →
Publisheur les met en page sur une vraie une et exporte un **PDF prêt à
imprimer, des images de pages et une édition web** via **Scribus**. Pas de Canva,
pas de bagarre avec les zones de texte, pas de mise en page cassée après
compression.

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

## Comment ça marche — la rédaction

Deux types de contributeurs partagent une seule plateforme :

- **Journalistes** — écrivent, éditent et sélectionnent les articles, règlent
  l'importance de chaque sujet et publient l'édition.
- **Reporters** — des membres d'un régiment qui envoient des reportages de
  terrain depuis leur propre unité : une opération, un soldat héroïque, un combat
  marquant. Les journalistes reprennent ces dépêches pour remplir le journal.

Chaque régiment peut garder **son propre titre** (son édition) *et* alimenter un
**journal Warden commun** — les mêmes articles peuvent servir au journal d'un
régiment comme au journal partagé. *Le Petit Daihbi* (Journal du Front · 2ᵉ REI)
est l'édition de référence livrée dans ce dépôt.

## Charte éditoriale

Un journal partagé ne tient que si tout le monde a confiance dans le ton. Les
règles de base :

- **Apolitique** — pas de politique du monde réel.
- **Pro-Warden** — on soutient l'effort de guerre, tous les régiments sont les
  bienvenus.
- **Pas d'attaques gratuites**, pas de règlements de comptes entre unités.
- **Pas de point Godwin.**

## Ce qui fonctionne aujourd'hui

- **Rédaction dans le navigateur** (`web/editor.html`) — connexion par lien magique
  par e-mail, écriture/édition d'articles, réordonnancement, aperçu en direct,
  synchronisation en temps réel entre collaborateurs.
- **Mise en page automatique** — l'**importance** d'un sujet (`lead` · `major` ·
  `minor` · `brief`) commande la typographie : `lead` est une une pleine largeur,
  sur 3 colonnes avec lettrine ; le reste s'écoule automatiquement dans un bloc
  sur 5 colonnes, sur autant de pages A3 que nécessaire.
- **Trois sorties** — édition web (`paper.html`), PDF/PNG rapide via le navigateur,
  et un **PDF prêt à imprimer + images de pages** depuis le publieur Scribus.
- **Plusieurs éditions** — changez la valeur `ISSUE` pour produire des journaux /
  titres distincts depuis la même rédaction.
- **War-wire Foxhole** — des sujets de guerre générés automatiquement (hex le plus
  sanglant, dépêches de secteur, titres de pertes) fusionnés au moment de la
  publication.

## Feuille de route — la vision plus large

Idées des régiments fondateurs, pas encore réalisées :

- **Rôles & salons des reporters** — des permissions distinctes journaliste/reporter,
  chaque régiment avec son propre flux d'arrivée (aujourd'hui, tout utilisateur
  connecté est un collaborateur à part égale).
- **Reporters assignés à des OP** — couvrir une opération précise en direct.
- **Publicités de fabricants** — des emplacements sponsorisés/payants dans la mise
  en page pour les fabricants en jeu.
- **Classement F1** — collecter les captures de stats `F1` de chacun et compiler un
  classement automatiquement (piste : un modèle **Qwen3** local qui fait la
  lecture + le décompte).

---

## Installation

```
web/        Site statique (GitHub Pages) : éditeur + journal + accueil
  index.html    Page d'accueil
  editor.html   Rédaction — écrire/gérer les articles (connexion e-mail)
  paper.html    Le journal mis en page (vue web, impression PDF, PNG)
  daihbi.js     Couche partagée de données + auth Supabase
  config.js     ← votre URL Supabase + clé anon vont ici
supabase/
  schema.sql    À exécuter une fois dans l'éditeur SQL de Supabase (tables, RLS, stockage)
publish/        Publieur Scribus (PDF/PNG prêt à imprimer)
.github/workflows/pages.yml      Déploie automatiquement web/ sur GitHub Pages
.github/workflows/publish.yml    Lance le publieur Scribus dans la CI
```

### 1. Configurer Supabase (backend)

1. Créez un projet sur [supabase.com](https://supabase.com).
2. **SQL Editor → New query →** collez `supabase/schema.sql` → **Run**.
3. **Authentication → Providers →** activez **Email** (le lien magique est le plus
   simple).
4. **Authentication → URL Configuration →** ajoutez votre URL GitHub Pages
   (ex. `https://USER.github.io/publisheur/`) comme URL de redirection.
5. **Settings → API →** copiez l'**URL du projet** et la **clé publique anon** dans
   `web/config.js`.

> La clé anon peut être committée sans risque — elle est publique par conception.
> C'est le Row-Level Security (dans `schema.sql`) qui protège les données. Ne
> mettez jamais la clé `service_role` dans `config.js`.

### 2. Déployer le site (frontend)

Poussez sur GitHub, puis **Settings → Pages → Source : GitHub Actions**. Le
workflow `pages.yml` publie `web/` à chaque push sur `main`. Les collaborateurs
n'ont qu'à visiter l'URL et se connecter avec leur e-mail.

**Pour lancer en local à la place :**
```bash
cd web && python3 -m http.server 8200   # → http://127.0.0.1:8200
```

### 3. Écrire & publier

- **Écrire :** ouvrez `/editor.html`, connectez-vous, ajoutez des articles.
  Choisissez une **importance** par article — `lead` (bandeau de une) · `major`
  (large) · `minor` (colonne) · `brief` (brève) — qui pilote la mise en page
  automatique. Les changements se synchronisent en direct entre collaborateurs.
- **Lire / PDF rapide :** `/paper.html` → **Imprimer / PDF** (navigateur) ou **PNG**.
- **Publication prête à imprimer :** le publieur Scribus fait couler tout le contenu
  dans une vraie mise en page Scribus et exporte un PDF prêt à imprimer + des
  images de pages.

  ```bash
  cd publish && ./publish.sh            # → out/issue.pdf + out/page-*.png
  ./publish.sh special-1                # un numéro nommé
  ```
  Nécessite `scribus`, `poppler-utils`, `xvfb`. Trois étapes :
  `build_issue.py` (rassemble les articles → `out/issue.json`) → `layout.py`
  (Scribus Scripter, lancé sans interface via `xvfb-run scribus -g -ns -py`) →
  `pdftoppm` (PNG).

  **Source :** définissez `SUPABASE_URL` + `SUPABASE_KEY` pour tirer du cloud ;
  sinon il bascule sur le `articles.db` local. Le **war-wire** Foxhole
  (`../../data-collection/foxhole_war.db`) est fusionné sauf avec `--no-wire`.

  **En CI :** `.github/workflows/publish.yml` lance le même publieur à la demande
  (Actions → « Publish issue ») et téléverse le PDF/PNG comme artefact. Ajoutez
  `SUPABASE_URL` / `SUPABASE_KEY` comme secrets du dépôt. (La CI n'a pas de
  `foxhole_war.db`, elle publie donc uniquement les articles Supabase.)

---
---

# Publisheur (English)

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
