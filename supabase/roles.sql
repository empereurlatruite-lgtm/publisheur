-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — roles & profiles (Phase 1)
--  Run once in the Supabase SQL Editor. Safe to re-run.
-- ════════════════════════════════════════════════════════════════════════

-- ── Profiles: one row per user, carries role / régiment / avatar / name ──
create table if not exists public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default '',
  role         text not null default 'reader'
                 check (role in ('reader','writer','illustrator','editor','annonceur')),
  clan         text not null default '',
  avatar_url   text not null default '',
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

drop trigger if exists trg_profiles_updated on public.profiles;
create trigger trg_profiles_updated before update on public.profiles
  for each row execute function public.touch_updated_at();

-- ── Helpers (security definer so policies can read the caller's role) ────
create or replace function public.my_role()
returns text language sql security definer stable set search_path = public as $$
  select coalesce((select role from public.profiles where id = auth.uid()), 'reader')
$$;
create or replace function public.is_editor()
returns boolean language sql security definer stable set search_path = public as $$
  select exists (select 1 from public.profiles where id = auth.uid() and role = 'editor')
$$;

-- ── Auto-create a profile on signup, reading role/clan/name from metadata ─
--    'editor' can NEVER be self-assigned at signup → clamped to reader.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
declare v_role text;
begin
  v_role := coalesce(nullif(new.raw_user_meta_data->>'role',''), 'reader');
  if v_role not in ('reader','writer','illustrator','annonceur') then v_role := 'reader'; end if;
  insert into public.profiles (id, display_name, role, clan)
  values (new.id,
          coalesce(new.raw_user_meta_data->>'display_name',''),
          v_role,
          coalesce(new.raw_user_meta_data->>'clan',''))
  on conflict (id) do nothing;
  return new;
end $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- backfill profiles for users that already exist
insert into public.profiles (id, display_name, role)
select u.id, coalesce(u.raw_user_meta_data->>'display_name',''), 'reader'
from auth.users u on conflict (id) do nothing;
-- the existing reporter account becomes the first editor (so publishing works)
update public.profiles set role = 'editor'
where id in (select id from auth.users where email = 'reporter@publisheur.test');

-- ── Profiles RLS ────────────────────────────────────────────────────────
alter table public.profiles enable row level security;
drop policy if exists "profiles read"         on public.profiles;
drop policy if exists "profiles self update"  on public.profiles;
drop policy if exists "profiles editor update" on public.profiles;
create policy "profiles read" on public.profiles
  for select to anon, authenticated using (true);
-- a user edits their own profile but cannot make themselves an editor
create policy "profiles self update" on public.profiles
  for update to authenticated using (id = auth.uid())
  with check (id = auth.uid() and role in ('reader','writer','illustrator','annonceur'));
-- editors can edit anyone (incl. granting/revoking editor)
create policy "profiles editor update" on public.profiles
  for update to authenticated using (public.is_editor()) with check (public.is_editor());

-- ── Article workflow status (keeps `published` as the public-read gate) ──
alter table public.articles add column if not exists status text not null default 'published'
  check (status in ('draft','review','published'));

-- ── Replace the old "shared newsroom" article policies with role-based ───
drop policy if exists "collab read"     on public.articles;
drop policy if exists "collab insert"   on public.articles;
drop policy if exists "collab update"   on public.articles;
drop policy if exists "collab delete"   on public.articles;
drop policy if exists "public read pub" on public.articles;
drop policy if exists "art public read" on public.articles;
drop policy if exists "art auth read"   on public.articles;
drop policy if exists "art insert"      on public.articles;
drop policy if exists "art author update" on public.articles;
drop policy if exists "art editor update" on public.articles;
drop policy if exists "art delete"      on public.articles;

create policy "art public read" on public.articles
  for select to anon using (published = true);
create policy "art auth read" on public.articles
  for select to authenticated using (true);
-- writers / illustrators / editors create their OWN articles
create policy "art insert" on public.articles
  for insert to authenticated
  with check (author_id = auth.uid() and public.my_role() in ('writer','illustrator','editor'));
-- authors edit their own; non-editors may NOT publish (published must stay false)
create policy "art author update" on public.articles
  for update to authenticated using (author_id = auth.uid())
  with check (author_id = auth.uid() and (public.is_editor() or published = false));
-- editors edit / publish anything
create policy "art editor update" on public.articles
  for update to authenticated using (public.is_editor()) with check (public.is_editor());
-- authors delete their own; editors delete anything
create policy "art delete" on public.articles
  for delete to authenticated using (author_id = auth.uid() or public.is_editor());

-- avatars live in the same public 'media' bucket (policies already allow it)
-- ════════════════════════════════════════════════════════════════════════
