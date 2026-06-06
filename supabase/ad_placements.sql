-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — ad placements (an editor running a réclame in their edition)
--  Run once in the Supabase SQL Editor. Safe to re-run.
--
--  Mirrors `placements` (see pool.sql): writing ≠ layout. An `ad` is the
--  advertiser's réclame (content, owned by them, approved by an editor). An
--  `ad_placement` is an editor dropping that ad into their edition at a chosen
--  order + publish state. One ad can run in several papers. Ads have no
--  `weight` (they're not lead/major/minor/brief) — only `position`.
-- ════════════════════════════════════════════════════════════════════════

create table if not exists public.ad_placements (
  id          uuid primary key default gen_random_uuid(),
  ad_id       uuid not null references public.ads(id) on delete cascade,
  issue       text not null references public.papers(issue) on delete cascade,
  position    integer not null default 0,
  published   boolean not null default false,
  placed_by   uuid references auth.users(id) on delete set null default auth.uid(),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (ad_id, issue)
);
create index if not exists ad_placements_issue_idx
  on public.ad_placements (issue, published, position);

drop trigger if exists trg_ad_placements_updated on public.ad_placements;
create trigger trg_ad_placements_updated before update on public.ad_placements
  for each row execute function public.touch_updated_at();

alter table public.ad_placements enable row level security;
drop policy if exists "adpl read pub"  on public.ad_placements;
drop policy if exists "adpl read auth" on public.ad_placements;
drop policy if exists "adpl insert"    on public.ad_placements;
drop policy if exists "adpl update"    on public.ad_placements;
drop policy if exists "adpl delete"    on public.ad_placements;
create policy "adpl read pub"  on public.ad_placements for select to anon using (published = true);
create policy "adpl read auth" on public.ad_placements for select to authenticated using (true);
-- only the managing editor(s) of the edition place / order / publish ads
create policy "adpl insert" on public.ad_placements for insert to authenticated with check (public.manages_issue(issue));
create policy "adpl update" on public.ad_placements for update to authenticated using (public.manages_issue(issue)) with check (public.manages_issue(issue));
create policy "adpl delete" on public.ad_placements for delete to authenticated using (public.manages_issue(issue));

alter publication supabase_realtime add table public.ad_placements;
-- ════════════════════════════════════════════════════════════════════════
