-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — reader comments ("Courrier des lecteurs")  [Phase ③]
--  Run once in the Supabase SQL Editor. Safe to re-run.
--  Reading is anonymous; posting requires a logged-in account (any role).
-- ════════════════════════════════════════════════════════════════════════

create table if not exists public.comments (
  id          uuid primary key default gen_random_uuid(),
  issue       text not null,
  article_id  uuid references public.articles(id) on delete cascade,  -- optional (future per-article)
  author_id   uuid references auth.users(id) on delete set null default auth.uid(),
  author_name text not null default '',
  body        text not null check (char_length(body) between 1 and 2000),
  created_at  timestamptz not null default now()
);
create index if not exists comments_issue_idx on public.comments (issue, created_at);

alter table public.comments enable row level security;
drop policy if exists "comments read"   on public.comments;
drop policy if exists "comments insert" on public.comments;
drop policy if exists "comments delete" on public.comments;

-- anyone can READ comments (they accompany the public paper)
create policy "comments read" on public.comments
  for select to anon, authenticated using (true);
-- only a logged-in user can POST, and only as themselves
create policy "comments insert" on public.comments
  for insert to authenticated with check (author_id = auth.uid());
-- a user removes their own comment; editors can remove any (moderation)
create policy "comments delete" on public.comments
  for delete to authenticated using (author_id = auth.uid() or public.is_editor());

-- live updates so a new comment appears for everyone reading
alter publication supabase_realtime add table public.comments;
-- ════════════════════════════════════════════════════════════════════════
