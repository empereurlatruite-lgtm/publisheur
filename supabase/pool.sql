-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — pool of chronicles + placements (writing ≠ layout)
--  Run once in the Supabase SQL Editor. Safe to re-run.
--
--  Model: an `article` is a chronicle (TEXT, by a writer). A `placement` is an
--  editor running that chronicle in their edition with a layout (weight, order,
--  photo override, published). One chronicle can run in several papers.
-- ════════════════════════════════════════════════════════════════════════

-- ── Placements (an editor's layout decision) ────────────────────────────
create table if not exists public.placements (
  id          uuid primary key default gen_random_uuid(),
  article_id  uuid not null references public.articles(id) on delete cascade,
  issue       text not null references public.papers(issue) on delete cascade,
  weight      text not null default 'minor' check (weight in ('lead','major','minor','brief')),
  position    integer not null default 0,
  image_url   text not null default '',        -- per-paper photo override ('' → article's suggested)
  published   boolean not null default false,
  placed_by   uuid references auth.users(id) on delete set null default auth.uid(),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (article_id, issue)
);
create index if not exists placements_issue_idx on public.placements (issue, published, weight, position);

drop trigger if exists trg_placements_updated on public.placements;
create trigger trg_placements_updated before update on public.placements
  for each row execute function public.touch_updated_at();

alter table public.placements enable row level security;
drop policy if exists "pl read pub"  on public.placements;
drop policy if exists "pl read auth" on public.placements;
drop policy if exists "pl insert"    on public.placements;
drop policy if exists "pl update"    on public.placements;
drop policy if exists "pl delete"    on public.placements;
create policy "pl read pub"  on public.placements for select to anon using (published = true);
create policy "pl read auth" on public.placements for select to authenticated using (true);
-- only the managing editor(s) of the edition place / lay out / publish
create policy "pl insert" on public.placements for insert to authenticated with check (public.manages_issue(issue));
create policy "pl update" on public.placements for update to authenticated using (public.manages_issue(issue)) with check (public.manages_issue(issue));
create policy "pl delete" on public.placements for delete to authenticated using (public.manages_issue(issue));

-- ── Migrate existing articles → placements (carry their current layout) ──
insert into public.placements (article_id, issue, weight, position, published, placed_by)
select a.id, a.issue, a.weight, a.position, a.published, a.author_id
from public.articles a
where a.issue is not null and a.issue <> ''
  and exists (select 1 from public.papers p where p.issue = a.issue)
on conflict (article_id, issue) do nothing;

-- ── Articles become pool chronicles: status = draft | submitted ─────────
--    (publish is now a per-placement decision). Order matters: drop the old
--    status check BEFORE rewriting values, then re-add the narrower one.
alter table public.articles drop constraint if exists articles_status_check;
update public.articles set status = case when coalesce(status,'') = 'draft' then 'draft' else 'submitted' end;
alter table public.articles alter column status set default 'draft';
alter table public.articles add constraint articles_status_check check (status in ('draft','submitted'));
-- chronicles are no longer bound to one paper
alter table public.articles alter column issue drop not null;
alter table public.articles alter column issue set default null;
alter table public.articles alter column published set default false;

-- ── Re-scope ARTICLES RLS to the pool model (layout perms live on placements)
drop policy if exists "art public read"   on public.articles;
drop policy if exists "art auth read"     on public.articles;
drop policy if exists "art insert"        on public.articles;
drop policy if exists "art author update" on public.articles;
drop policy if exists "art editor update" on public.articles;
drop policy if exists "art delete"        on public.articles;
-- anon: a chronicle is public if it's published in at least one paper
create policy "art public read" on public.articles for select to anon
  using (exists (select 1 from public.placements pl where pl.article_id = articles.id and pl.published));
-- the newsroom can read all chronicles (writers see their own, editors browse the pool)
create policy "art auth read" on public.articles for select to authenticated using (true);
-- writers / illustrators / editors create their OWN chronicles
create policy "art insert" on public.articles for insert to authenticated
  with check (author_id = auth.uid() and public.my_role() in ('writer','illustrator','editor'));
-- only the AUTHOR edits the text (editors lay out, they don't edit copy)
create policy "art author update" on public.articles for update to authenticated
  using (author_id = auth.uid()) with check (author_id = auth.uid());
-- author deletes own; editors may delete (moderation/cleanup)
create policy "art delete" on public.articles for delete to authenticated
  using (author_id = auth.uid() or public.is_editor());

alter publication supabase_realtime add table public.placements;
-- ════════════════════════════════════════════════════════════════════════
