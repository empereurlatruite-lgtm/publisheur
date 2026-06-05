-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — réclames / ad studio  [Phase ②]
--  Run once in the Supabase SQL Editor. Safe to re-run.
--  Annonceurs create ads → an editor approves → approved ads show in the paper.
-- ════════════════════════════════════════════════════════════════════════

create table if not exists public.ads (
  id              uuid primary key default gen_random_uuid(),
  advertiser_id   uuid references auth.users(id) on delete set null default auth.uid(),
  advertiser_name text not null default '',
  title           text not null default '',
  body            text not null default '',
  category        text not null default 'fabricant'   -- recrutement|troc|parodie|createur|fabricant
                    check (category in ('recrutement','troc','parodie','createur','fabricant')),
  maker           text not null default '',          -- in-game manufacturer / sponsor
  link            text not null default '',
  image_url       text not null default '',
  issue           text not null default 'all',        -- target edition, or 'all'
  status          text not null default 'draft'
                    check (status in ('draft','review','approved','rejected')),
  approved        boolean not null default false,      -- public-read gate
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
create index if not exists ads_issue_idx on public.ads (issue, approved);
-- if the table already existed, make sure the category column is present
alter table public.ads add column if not exists category text not null default 'fabricant';

drop trigger if exists trg_ads_updated on public.ads;
create trigger trg_ads_updated before update on public.ads
  for each row execute function public.touch_updated_at();

alter table public.ads enable row level security;
drop policy if exists "ads public read"   on public.ads;
drop policy if exists "ads auth read"      on public.ads;
drop policy if exists "ads insert"         on public.ads;
drop policy if exists "ads author update"  on public.ads;
drop policy if exists "ads editor update"  on public.ads;
drop policy if exists "ads delete"         on public.ads;

-- the public sees only APPROVED ads (they're shown in the paper)
create policy "ads public read" on public.ads
  for select to anon using (approved = true);
create policy "ads auth read" on public.ads
  for select to authenticated using (true);
-- annonceurs / editors create their OWN ads
create policy "ads insert" on public.ads
  for insert to authenticated
  with check (advertiser_id = auth.uid() and public.my_role() in ('annonceur','editor'));
-- advertiser edits own but may NOT self-approve (approved stays false)
create policy "ads author update" on public.ads
  for update to authenticated using (advertiser_id = auth.uid())
  with check (advertiser_id = auth.uid() and (public.is_editor() or approved = false));
-- editors approve / edit any
create policy "ads editor update" on public.ads
  for update to authenticated using (public.is_editor()) with check (public.is_editor());
-- advertiser deletes own; editors delete any
create policy "ads delete" on public.ads
  for delete to authenticated using (advertiser_id = auth.uid() or public.is_editor());

alter publication supabase_realtime add table public.ads;
-- ════════════════════════════════════════════════════════════════════════
