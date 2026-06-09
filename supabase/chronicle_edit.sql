-- ── chronicle_edit ───────────────────────────────────────────────────────────
-- Lets a rédacteur en chef edit a chronicle's TEXT in place from the board
-- (double-click → edit modal), not just lay it out. Two changes:
--
-- 1) RLS: besides the author (kept from pool.sql), a managing editor may update
--    a chronicle that is PLACED in one of the editions they own/co-edit. The
--    pool chronicle's own articles.issue is null (placements carry the issue),
--    so the check joins placements rather than using manages_issue(articles.issue).
--    Every edit is still stamped (last_edited_by, via set_article_editor) and the
--    prior version is archived to article_revisions — authorship/audit preserved.
--
-- 2) Fix the revision-snapshot crash on pool chronicles: snapshot_article()
--    copied OLD.issue into article_revisions.issue (NOT NULL); for a pooled
--    chronicle issue is null, so ANY update threw. Coalesce it to ''.

-- ── 1. managing editors may edit chronicles placed in their editions ─────────
drop policy if exists "art editor update" on public.articles;
create policy "art editor update" on public.articles
  for update to authenticated
  using (exists (select 1 from public.placements pl
                 where pl.article_id = articles.id and public.manages_issue(pl.issue)))
  with check (exists (select 1 from public.placements pl
                 where pl.article_id = articles.id and public.manages_issue(pl.issue)));

-- ── 2. snapshot trigger: tolerate a null issue (pool chronicles) ─────────────
create or replace function public.snapshot_article()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if (OLD.headline  is distinct from NEW.headline)  or (OLD.body    is distinct from NEW.body)
  or (OLD.subhead   is distinct from NEW.subhead)   or (OLD.kicker  is distinct from NEW.kicker)
  or (OLD.byline    is distinct from NEW.byline)    or (OLD.image_url is distinct from NEW.image_url)
  or (OLD.weight    is distinct from NEW.weight)    or (OLD.published is distinct from NEW.published)
  or (OLD.status    is distinct from NEW.status) then
    insert into public.article_revisions
      (article_id, issue, kicker, headline, subhead, byline, body, weight, image_url, published, status, author_id, edited_by, created_at)
    values
      (OLD.id, coalesce(OLD.issue, ''), OLD.kicker, OLD.headline, OLD.subhead, OLD.byline, OLD.body, OLD.weight,
       OLD.image_url, OLD.published, OLD.status, OLD.author_id, OLD.last_edited_by, OLD.updated_at);
  end if;
  return NEW;
end $$;
