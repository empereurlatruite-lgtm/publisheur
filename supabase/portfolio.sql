-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — illustrator portfolio  [Phase ④]
--  Run once in the Supabase SQL Editor. Safe to re-run.
--  Public gallery; only illustrators/editors upload; owner/editor delete.
-- ════════════════════════════════════════════════════════════════════════

create table if not exists public.images (
  id            uuid primary key default gen_random_uuid(),
  uploader_id   uuid references auth.users(id) on delete set null default auth.uid(),
  uploader_name text not null default '',
  url           text not null,
  caption       text not null default '',
  clan          text not null default '',
  created_at    timestamptz not null default now()
);
create index if not exists images_created_idx on public.images (created_at desc);

alter table public.images enable row level security;
drop policy if exists "images read"   on public.images;
drop policy if exists "images insert" on public.images;
drop policy if exists "images delete" on public.images;

-- anyone can browse the portfolio (it's a public gallery)
create policy "images read" on public.images
  for select to anon, authenticated using (true);
-- only illustrators / editors add images, as themselves
create policy "images insert" on public.images
  for insert to authenticated
  with check (uploader_id = auth.uid() and public.my_role() in ('illustrator','editor'));
-- uploader removes own; editors remove any
create policy "images delete" on public.images
  for delete to authenticated using (uploader_id = auth.uid() or public.is_editor());

alter publication supabase_realtime add table public.images;
-- ════════════════════════════════════════════════════════════════════════
