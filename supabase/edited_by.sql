-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — edit attribution (who edited each version)
--  Run once in the Supabase SQL Editor. Safe to re-run.
-- ════════════════════════════════════════════════════════════════════════

alter table public.articles          add column if not exists last_edited_by uuid references auth.users(id) on delete set null;
alter table public.article_revisions add column if not exists edited_by      uuid;

-- stamp the real logged-in user on every insert/update (client can't fake it)
create or replace function public.set_article_editor()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  -- only stamp when a real user is logged in (so SQL-editor backfills/admin
  -- writes don't wipe the attribution to null)
  if auth.uid() is not null then
    new.last_edited_by := auth.uid();
  end if;
  return new;
end $$;
drop trigger if exists trg_article_editor on public.articles;
create trigger trg_article_editor before insert or update on public.articles
  for each row execute function public.set_article_editor();

-- snapshot now also records WHO made the version being archived
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
      (OLD.id, OLD.issue, OLD.kicker, OLD.headline, OLD.subhead, OLD.byline, OLD.body, OLD.weight,
       OLD.image_url, OLD.published, OLD.status, OLD.author_id, OLD.last_edited_by, OLD.updated_at);
  end if;
  return NEW;
end $$;

-- backfill: existing articles' last editor defaults to their author
update public.articles set last_edited_by = author_id where last_edited_by is null;
-- ════════════════════════════════════════════════════════════════════════
