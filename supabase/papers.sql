-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — journaux en base + portée des éditeurs  [Phase ⑤]
--  Run once in the Supabase SQL Editor. Safe to re-run.
--  Editions live in the DB; the creator owns the journal and may add
--  co-éditeurs. An editor can only edit/publish articles of papers they manage.
-- ════════════════════════════════════════════════════════════════════════

-- ── Papers (editions) ───────────────────────────────────────────────────
create table if not exists public.papers (
  issue        text primary key,
  name         text not null default '',
  tagline      text not null default '',
  plate        text not null default 'plate-fraktur',
  ear          jsonb not null default '["","",""]'::jsonb,
  slogans      jsonb not null default '[]'::jsonb,
  emblem_left  text not null default '',
  emblem_right text not null default '',
  clan         text not null default '',
  owner_id     uuid references auth.users(id) on delete set null default auth.uid(),
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
drop trigger if exists trg_papers_updated on public.papers;
create trigger trg_papers_updated before update on public.papers
  for each row execute function public.touch_updated_at();

-- ── Who edits which paper (owner + co-éditeurs) ─────────────────────────
create table if not exists public.paper_editors (
  issue     text not null references public.papers(issue) on delete cascade,
  editor_id uuid not null references auth.users(id) on delete cascade,
  primary key (issue, editor_id)
);

-- the owner is automatically a managing editor of their paper
create or replace function public.add_owner_editor()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.owner_id is not null then
    insert into public.paper_editors (issue, editor_id)
    values (new.issue, new.owner_id) on conflict do nothing;
  end if;
  return new;
end $$;
drop trigger if exists trg_papers_owner_editor on public.papers;
create trigger trg_papers_owner_editor after insert on public.papers
  for each row execute function public.add_owner_editor();

-- does the caller manage this edition? (owner or co-éditeur)
create or replace function public.manages_issue(p_issue text)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.paper_editors where issue = p_issue and editor_id = auth.uid())
$$;
-- is the caller the owner of this edition?
create or replace function public.owns_issue(p_issue text)
returns boolean language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.papers where issue = p_issue and owner_id = auth.uid())
$$;

-- ── RLS: papers ─────────────────────────────────────────────────────────
alter table public.papers enable row level security;
drop policy if exists "papers read"   on public.papers;
drop policy if exists "papers insert" on public.papers;
drop policy if exists "papers update" on public.papers;
drop policy if exists "papers delete" on public.papers;
create policy "papers read" on public.papers
  for select to anon, authenticated using (true);                       -- public (mastheads)
create policy "papers insert" on public.papers                          -- editors create journals
  for insert to authenticated with check (owner_id = auth.uid() and public.my_role() = 'editor');
create policy "papers update" on public.papers                          -- owner or co-éditeur edits
  for update to authenticated using (owner_id = auth.uid() or public.manages_issue(issue))
  with check (owner_id = auth.uid() or public.manages_issue(issue));
create policy "papers delete" on public.papers
  for delete to authenticated using (owner_id = auth.uid());

-- ── RLS: paper_editors (only the owner manages the roster) ──────────────
alter table public.paper_editors enable row level security;
drop policy if exists "pe read"   on public.paper_editors;
drop policy if exists "pe insert" on public.paper_editors;
drop policy if exists "pe delete" on public.paper_editors;
create policy "pe read" on public.paper_editors
  for select to anon, authenticated using (true);
create policy "pe insert" on public.paper_editors
  for insert to authenticated with check (public.owns_issue(issue));
create policy "pe delete" on public.paper_editors
  for delete to authenticated using (public.owns_issue(issue));

-- ── Re-scope article editor permissions: global → per-paper ─────────────
drop policy if exists "art author update" on public.articles;
drop policy if exists "art editor update" on public.articles;
drop policy if exists "art delete"        on public.articles;
-- authors edit own; may publish only if they manage the paper
create policy "art author update" on public.articles
  for update to authenticated using (author_id = auth.uid())
  with check (author_id = auth.uid() and (public.manages_issue(issue) or published = false));
-- managing editors edit/publish anything in THEIR paper(s)
create policy "art editor update" on public.articles
  for update to authenticated using (public.manages_issue(issue))
  with check (public.manages_issue(issue));
-- authors delete own; managing editors delete in their paper
create policy "art delete" on public.articles
  for delete to authenticated using (author_id = auth.uid() or public.manages_issue(issue));

-- ── Seed the three existing editions (owner = the reporter/editor) ──────
insert into public.papers (issue, name, tagline, plate, ear, slogans, emblem_left, emblem_right, clan, owner_id)
values
 ('current', 'Le Petit Daihbi', 'Journal Quotidien du Front — « Tout pour le Régiment »', 'plate-fraktur',
   '["Édition du Front","Prix : 5 centimes","2<sup>e</sup> REI · Daihbi"]'::jsonb, '[]'::jsonb, '', '', '2e REI',
   (select id from auth.users where email = 'reporter@publisheur.test')),
 ('horizon-bleu', 'L''Horizon Bleu', 'Sous notre bannière nous écrivons l''Histoire', 'plate-anton',
   '["Front de l''Est","501<sup>e</sup> Régiment","Warden"]'::jsonb,
   '["Vive les Wardens","Vive la 501<sup>e</sup>","Vive la France"]'::jsonb, '',
   'https://atnmzlaiglmkykzryjar.supabase.co/storage/v1/object/public/media/emblems/warden-shield.png', '501e',
   (select id from auth.users where email = 'reporter@publisheur.test')),
 ('echo-du-front', 'L''Écho du Front', 'Journal indépendant Warden — Témoigner, informer, tenir', 'plate-echo',
   '["Numéro 002","Édition du 4 juin 2026","Distribution aux forces & citoyens"]'::jsonb,
   '["Tenir la ligne","Protéger nos foyers","Pour Callahan !"]'::jsonb, '', '', '8e',
   (select id from auth.users where email = 'reporter@publisheur.test'))
on conflict (issue) do nothing;

alter publication supabase_realtime add table public.papers;
-- ════════════════════════════════════════════════════════════════════════
