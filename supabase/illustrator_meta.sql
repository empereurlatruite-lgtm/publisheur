-- ── illustrator_meta ─────────────────────────────────────────────────────────
-- Structured metadata for portfolio images, powering the illustrateur board's
-- **add-image modal** and the **nav-bar filters** (historical / fan art / IA /
-- officiel …). `tags` is a free multi-label set so an image can be e.g. both
-- {fanart, ai}. `source` = where it came from (a URL/credit), `license` = reuse
-- terms. The régiment filter reuses the existing `clan` column.
alter table public.images add column if not exists tags    text[] not null default '{}';
alter table public.images add column if not exists source  text   not null default '';
alter table public.images add column if not exists license text   not null default '';

-- Backfill the images scraped so far so the filters light up immediately.
update public.images set tags = array['official']   where (tags = '{}' or tags is null)
  and uploader_name in ('Atelier Foxhole — Officiel','Foxhole — Concept Art');
update public.images set tags = array['historical'] where (tags = '{}' or tags is null)
  and caption ilike '%WW1%';
update public.images set tags = array['fanart']     where (tags = '{}' or tags is null)
  and caption ilike '%fan art%';
-- Carry the WW1 captions' license into the license column (text after the last comma).
update public.images set license = btrim(split_part(caption, ',', -1))
  where license = '' and caption ilike '%WW1,%';
