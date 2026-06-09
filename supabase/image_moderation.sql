-- ── image_moderation ─────────────────────────────────────────────────────────
-- Two rights, granted to specific users via SQL (editors keep both implicitly):
--   profiles.can_upload   → may put images in the public "media" bucket / portfolio
--   profiles.can_moderate → may approve pending images so readers can see them
-- Uploaded images start unapproved; the public (and ordinary signed-in users) only
-- see APPROVED images. Owners see their own pending ones; moderators see all.
--
-- Grant rights, e.g.:
--   update public.profiles set can_upload = true               where id = '…';
--   update public.profiles set can_upload = true, can_moderate = true where id = '…';
-- (Find a user's id in Supabase → Authentication → Users.)

alter table public.profiles add column if not exists can_upload   boolean not null default false;
alter table public.profiles add column if not exists can_moderate boolean not null default false;
alter table public.images   add column if not exists approved boolean not null default false;
alter table public.media    add column if not exists approved boolean not null default false;

-- editors keep the rights; specific users are granted them via the flags above.
create or replace function public.can_upload() returns boolean
  language sql security definer stable set search_path = public as $$
  select public.is_editor() or coalesce((select can_upload from public.profiles where id = auth.uid()), false)
$$;
create or replace function public.can_moderate() returns boolean
  language sql security definer stable set search_path = public as $$
  select public.is_editor() or coalesce((select can_moderate from public.profiles where id = auth.uid()), false)
$$;

-- ── images (portfolio gallery) ───────────────────────────────────────────────
drop policy if exists "images read"      on public.images;
drop policy if exists "images read anon" on public.images;
drop policy if exists "images read auth" on public.images;
drop policy if exists "images insert"    on public.images;
drop policy if exists "images update"    on public.images;
drop policy if exists "images delete"    on public.images;
create policy "images read anon" on public.images for select to anon
  using (approved = true);
create policy "images read auth" on public.images for select to authenticated
  using (approved = true or uploader_id = auth.uid() or public.can_moderate());
create policy "images insert" on public.images for insert to authenticated
  with check (uploader_id = auth.uid() and public.can_upload());
create policy "images moderate" on public.images for update to authenticated
  using (public.can_moderate()) with check (public.can_moderate());
create policy "images delete" on public.images for delete to authenticated
  using (uploader_id = auth.uid() or public.can_moderate());

-- ── media ledger (chronicle / ad / avatar uploads) ───────────────────────────
drop policy if exists "media read"      on public.media;
drop policy if exists "media read anon" on public.media;
drop policy if exists "media read auth" on public.media;
drop policy if exists "media insert"    on public.media;
drop policy if exists "media update"    on public.media;
drop policy if exists "media delete"    on public.media;
create policy "media read anon" on public.media for select to anon
  using (approved = true);
create policy "media read auth" on public.media for select to authenticated
  using (approved = true or uploader_id = auth.uid() or public.can_moderate());
create policy "media insert" on public.media for insert to authenticated
  with check (uploader_id = auth.uid() and public.can_upload());
create policy "media moderate" on public.media for update to authenticated
  using (public.can_moderate()) with check (public.can_moderate());
create policy "media delete" on public.media for delete to authenticated
  using (uploader_id = auth.uid() or public.can_moderate());

-- ── Storage: only can_upload users may write bytes to the public media bucket ──
-- Replaces the open "media auth write" policy from schema.sql (the only insert
-- gate for the bucket), so a non-uploader can't push bytes even via the raw API.
drop policy if exists "media auth write" on storage.objects;
create policy "media auth write" on storage.objects for insert to authenticated
  with check (bucket_id = 'media' and public.can_upload());
