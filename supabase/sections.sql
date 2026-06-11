-- ── sections ─────────────────────────────────────────────────────────────────
-- Editor-defined RUBRIQUES (newspaper sections) per edition: "Front Ouest",
-- "Tech & mises à jour", "Nouvelles du régiment"… The rédacteur en chef creates,
-- renames, reorders and deletes them on the board; each placed chronicle can be
-- assigned to one. paper.html renders the lead hero on top, then each section as a
-- titled block with its own balanced column grid (unsectioned stories stay in the
-- default well, headerless — so editions with NO sections render exactly as before).
--
-- Sections are LAYOUT (the editor's call), so they live alongside placements and are
-- gated by the same manages_issue() helper (papers.sql). Public read so anonymous
-- readers can render the section headings. section_id ON DELETE SET NULL → deleting
-- a section just un-sections its stories (they fall back to the default well).

create table if not exists public.sections (
  id          uuid primary key default gen_random_uuid(),
  issue       text not null references public.papers(issue) on delete cascade,
  name        text not null default '',
  position    smallint not null default 0,
  created_by  uuid default auth.uid() references auth.users(id),
  created_at  timestamptz not null default now()
);
create index if not exists sections_issue_idx on public.sections (issue, position);

alter table public.sections enable row level security;
drop policy if exists "sections read"   on public.sections;
drop policy if exists "sections insert" on public.sections;
drop policy if exists "sections update" on public.sections;
drop policy if exists "sections delete" on public.sections;
-- public read: the rendered paper (incl. anon) needs section names + order
create policy "sections read"   on public.sections for select using (true);
create policy "sections insert" on public.sections for insert to authenticated with check (public.manages_issue(issue));
create policy "sections update" on public.sections for update to authenticated using (public.manages_issue(issue)) with check (public.manages_issue(issue));
create policy "sections delete" on public.sections for delete to authenticated using (public.manages_issue(issue));

-- which section a placed chronicle belongs to (null = default/unsectioned well)
alter table public.placements
  add column if not exists section_id uuid references public.sections(id) on delete set null;
