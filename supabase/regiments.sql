-- ── regiments ───────────────────────────────────────────────────────────────
-- A shared, user-extensible vocabulary of régiments/clans. The base list ships
-- in web/papers.js (window.DAIHBI_CLANS); this table holds the ones contributors
-- add at runtime. Daihbi.Regiments.list() merges defaults + these rows (deduped),
-- so a régiment added once shows up in every picker (chronicle source, journal
-- régiment, profile…).
--
-- Read is public (the list populates pickers seen by everyone). Insert is open to
-- any signed-in user (any contributor can tag their régiment). No update/delete:
-- a régiment is shared vocabulary that other rows may reference by name.

create table if not exists public.regiments (
  id         uuid primary key default gen_random_uuid(),
  name       text not null unique,
  created_by uuid references auth.users(id) on delete set null default auth.uid(),
  created_at timestamptz not null default now()
);

alter table public.regiments enable row level security;

drop policy if exists "regiments read" on public.regiments;
create policy "regiments read" on public.regiments
  for select using (true);

drop policy if exists "regiments insert" on public.regiments;
create policy "regiments insert" on public.regiments
  for insert with check (auth.uid() is not null);
