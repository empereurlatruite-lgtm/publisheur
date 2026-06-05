-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — article revision history & rollback
--  Run once in the Supabase SQL Editor. Safe to re-run.
--  Every meaningful UPDATE to an article snapshots the PRIOR version.
-- ════════════════════════════════════════════════════════════════════════

create table if not exists public.article_revisions (
  id          uuid primary key default gen_random_uuid(),
  article_id  uuid references public.articles(id) on delete cascade,
  issue       text not null default '',
  kicker      text, headline text, subhead text, byline text,
  body        text, weight text, image_url text,
  published   boolean, status text,
  author_id   uuid,
  created_at  timestamptz not null default now()   -- when that prior version was last saved
);
create index if not exists artrev_idx on public.article_revisions (article_id, created_at desc);

-- snapshot the OLD row whenever a content/status field actually changes
create or replace function public.snapshot_article()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if (OLD.headline  is distinct from NEW.headline)  or (OLD.body    is distinct from NEW.body)
  or (OLD.subhead   is distinct from NEW.subhead)   or (OLD.kicker  is distinct from NEW.kicker)
  or (OLD.byline    is distinct from NEW.byline)    or (OLD.image_url is distinct from NEW.image_url)
  or (OLD.weight    is distinct from NEW.weight)    or (OLD.published is distinct from NEW.published)
  or (OLD.status    is distinct from NEW.status) then
    insert into public.article_revisions
      (article_id, issue, kicker, headline, subhead, byline, body, weight, image_url, published, status, author_id, created_at)
    values
      (OLD.id, OLD.issue, OLD.kicker, OLD.headline, OLD.subhead, OLD.byline, OLD.body, OLD.weight,
       OLD.image_url, OLD.published, OLD.status, OLD.author_id, OLD.updated_at);
  end if;
  return NEW;
end $$;
drop trigger if exists trg_article_revision on public.articles;
create trigger trg_article_revision before update on public.articles
  for each row execute function public.snapshot_article();

-- ── RLS ─────────────────────────────────────────────────────────────────
alter table public.article_revisions enable row level security;
drop policy if exists "rev read"   on public.article_revisions;
drop policy if exists "rev delete" on public.article_revisions;
-- the newsroom can read revisions (no anon — they're internal drafts/history)
create policy "rev read" on public.article_revisions
  for select to authenticated using (true);
-- managing editors / the author may prune history
create policy "rev delete" on public.article_revisions
  for delete to authenticated using (public.manages_issue(issue) or author_id = auth.uid());
-- (no INSERT policy: only the security-definer trigger writes revisions)
-- ════════════════════════════════════════════════════════════════════════
