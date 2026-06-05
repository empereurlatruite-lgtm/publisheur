-- ════════════════════════════════════════════════════════════════════════
--  LE PETIT DAIHBI — Supabase schema
--  Run this in the Supabase SQL Editor (Dashboard → SQL → New query → Run).
--  Safe to re-run: everything is `if not exists` / `or replace`.
-- ════════════════════════════════════════════════════════════════════════

-- ── Articles ────────────────────────────────────────────────────────────
create table if not exists public.articles (
    id          uuid primary key default gen_random_uuid(),
    issue       text        not null default 'current',   -- edition the article belongs to
    kicker      text        not null default '',
    headline    text        not null default 'Untitled',
    subhead     text        not null default '',
    byline      text        not null default '',
    body        text        not null default '',
    weight      text        not null default 'minor'
                  check (weight in ('lead','major','minor','brief')),
    image_url   text        not null default '',
    published   boolean     not null default true,
    position    integer     not null default 0,
    author_id   uuid        references auth.users (id) on delete set null default auth.uid(),
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create index if not exists articles_issue_idx     on public.articles (issue);
create index if not exists articles_order_idx      on public.articles (weight, position);

-- keep updated_at fresh
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end $$;

drop trigger if exists trg_articles_updated on public.articles;
create trigger trg_articles_updated
    before update on public.articles
    for each row execute function public.touch_updated_at();

-- ── Row Level Security ──────────────────────────────────────────────────
-- Model: a shared newsroom. Any signed-in collaborator can read & edit every
-- article. The public (anonymous) can read only PUBLISHED articles, so the
-- live paper / preview works without a login.
alter table public.articles enable row level security;

drop policy if exists "collab read"       on public.articles;
drop policy if exists "collab insert"     on public.articles;
drop policy if exists "collab update"     on public.articles;
drop policy if exists "collab delete"     on public.articles;
drop policy if exists "public read pub"   on public.articles;

create policy "collab read"   on public.articles
    for select to authenticated using (true);

create policy "collab insert" on public.articles
    for insert to authenticated with check (auth.uid() = author_id or author_id is null);

create policy "collab update" on public.articles
    for update to authenticated using (true) with check (true);

create policy "collab delete" on public.articles
    for delete to authenticated using (true);

create policy "public read pub" on public.articles
    for select to anon using (published = true);

-- ── Storage bucket: images + exported issues ────────────────────────────
insert into storage.buckets (id, name, public)
values ('media', 'media', true)
on conflict (id) do nothing;

drop policy if exists "media public read" on storage.objects;
drop policy if exists "media auth write"  on storage.objects;
drop policy if exists "media auth update" on storage.objects;

create policy "media public read" on storage.objects
    for select to anon using (bucket_id = 'media');

create policy "media auth write"  on storage.objects
    for insert to authenticated with check (bucket_id = 'media');

create policy "media auth update" on storage.objects
    for update to authenticated using (bucket_id = 'media');

-- ── Realtime (optional): live updates between collaborators ─────────────
-- Lets every editor see changes appear without refreshing.
alter publication supabase_realtime add table public.articles;

-- ════════════════════════════════════════════════════════════════════════
--  After running this:
--   • Authentication → Providers → enable "Email" (magic link is easiest).
--   • Authentication → URL Configuration → add your GitHub Pages URL.
--   • Settings → API → copy the Project URL + anon public key into
--     web/config.js (see that file).
-- ════════════════════════════════════════════════════════════════════════
