-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — media assets + provenance  [Phase ⑤]
--  Run once in the Supabase SQL Editor, AFTER portfolio.sql. Safe to re-run.
--  Every uploaded image (article photo, avatar, ad, portfolio) is re-encoded
--  to WebP client-side, then recorded here with who made it + its dimensions,
--  byte size and type. Files themselves live in the public "media" Storage
--  bucket; this table is the searchable provenance ledger.
-- ════════════════════════════════════════════════════════════════════════

create table if not exists public.media (
  id            uuid primary key default gen_random_uuid(),
  uploader_id   uuid references auth.users(id) on delete set null default auth.uid(),
  uploader_name text not null default '',          -- illustrator / propagandist
  url           text not null,
  path          text not null default '',           -- object path inside the bucket
  folder        text not null default '',           -- article photos | avatars | ads | portfolio
  mime          text not null default '',           -- normalised to image/webp
  bytes         integer not null default 0,         -- size of the stored file
  width         integer not null default 0,         -- pixels after downscale
  height        integer not null default 0,
  created_at    timestamptz not null default now()
);
create index if not exists media_uploader_idx on public.media (uploader_id, created_at desc);
create index if not exists media_created_idx  on public.media (created_at desc);

alter table public.media enable row level security;
drop policy if exists "media read"   on public.media;
drop policy if exists "media insert" on public.media;
drop policy if exists "media delete" on public.media;

-- the gallery / paper are public, so the ledger is readable by all
create policy "media read" on public.media
  for select to anon, authenticated using (true);
-- any signed-in contributor records their own uploads, as themselves
create policy "media insert" on public.media
  for insert to authenticated
  with check (uploader_id = auth.uid());
-- uploader removes own rows; editors remove any
create policy "media delete" on public.media
  for delete to authenticated using (uploader_id = auth.uid() or public.is_editor());

-- Carry the same provenance on the portfolio gallery rows so the grid can show
-- size / type without a join. (add column if not exists → safe on existing data)
alter table public.images add column if not exists mime   text    not null default '';
alter table public.images add column if not exists bytes  integer not null default 0;
alter table public.images add column if not exists width  integer not null default 0;
alter table public.images add column if not exists height integer not null default 0;
-- ════════════════════════════════════════════════════════════════════════
