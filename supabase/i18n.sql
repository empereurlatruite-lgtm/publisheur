-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — internationalisation (multilingual content + open writing)
--  Run once in the Supabase SQL Editor, AFTER all the other migrations
--  (…→ ad_placements → media → i18n).  Safe to re-run.
--
--  What it does:
--   • gives chronicles / ads / papers a `lang` (content language) code;
--   • gives each profile a content `preferred_lang` (kiosque filter) and a
--     `ui_lang` (interface language);
--   • opens chronicle writing to ANY signed-in user (editors still publish).
-- ════════════════════════════════════════════════════════════════════════

-- ── Content language on the things people read ──────────────────────────
-- Default 'fr' so every existing row stays French until edited. Codes match
-- the curated LANGS list in web/daihbi.js (fr,en,de,es,it,pl,ru,pt,nl,other).
alter table public.articles add column if not exists lang text not null default 'fr';
alter table public.ads      add column if not exists lang text not null default 'fr';
alter table public.papers   add column if not exists lang text not null default 'fr';

create index if not exists articles_lang_idx on public.articles (lang);

-- ── Reader / writer preferences on the profile ──────────────────────────
--   preferred_lang : '' = "all languages" (kiosque shows everything)
--   ui_lang        : '' = auto-detect from the browser
alter table public.profiles add column if not exists preferred_lang text not null default '';
alter table public.profiles add column if not exists ui_lang        text not null default '';

-- ── Open chronicle writing to any signed-in user ────────────────────────
-- Previously "art insert" (supabase/roles.sql) required role in
-- (writer,illustrator,editor). Now any authenticated user may create their
-- OWN chronicle. The editor publish gate is UNCHANGED: "art author update"
-- still forbids non-editors from setting published=true, so editors remain
-- in control of what actually runs in a paper.
drop policy if exists "art insert" on public.articles;
create policy "art insert" on public.articles
  for insert to authenticated
  with check (author_id = auth.uid());

-- ── Open réclame (ad) writing to any signed-in user ─────────────────────
-- Previously "ads insert" (supabase/ads.sql) required role in (annonceur,editor).
-- Now any authenticated user may create their OWN ad. The editor APPROVAL gate
-- is UNCHANGED: "ads author update" still forbids advertisers from self-setting
-- approved=true, so editors still moderate what actually runs in a paper.
drop policy if exists "ads insert" on public.ads;
create policy "ads insert" on public.ads
  for insert to authenticated
  with check (advertiser_id = auth.uid());

-- ── Let users save their own language preferences ───────────────────────
-- Re-create the self-update policy defensively so preferred_lang / ui_lang
-- are writable by their owner (role still can't be self-escalated).
drop policy if exists "profiles self update" on public.profiles;
create policy "profiles self update" on public.profiles
  for update to authenticated using (id = auth.uid())
  with check (id = auth.uid() and role in ('reader','writer','illustrator','annonceur'));

-- ════════════════════════════════════════════════════════════════════════
--  After running this: nothing else to configure — the frontend reads the
--  new columns directly. New chronicles/ads default to 'fr' unless the
--  author picks another language in the composer.
-- ════════════════════════════════════════════════════════════════════════
