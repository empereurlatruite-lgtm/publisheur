-- ── dummy_layout ──────────────────────────────────────────────────────────────
-- Turns the fixed-grid layout template (templates.sql) into a proper newspaper
-- "DUMMY" by adding non-story element types the editor can place in a cell:
-- mugshot, pull-quote ("left-out quote"), editorial cartoon, standalone photo.
-- The schematic dummy look (labels + font annotations + greeking) is a PLANNING
-- view only (paper.html in board/ALL mode); the public reader + print stay the
-- finished render.
--
-- Two columns on placements:
--   text → pull-quote text, or a mugshot/photo caption (editor layout content,
--          like image_url/col_span — NOT the author's chronicle body).
--   elem → the element type: '' = ordinary story/image (derive from slot/weight,
--          today's behaviour) | mugshot | quote | cartoon | photo.
--
-- Why `elem` is durable (not derived from placements.slot): switching/clearing an
-- edition's template runs resetSlots() → slot = -1, and editing a saved template
-- can re-point slot indices at different cells. Storing the element type on the
-- placement keeps a pull-quote a pull-quote even when it's detached from its cell.
--
-- LOOSE-WELL RULE (paper.html renderTemplateBody): a placement that is unslotted
-- (slot = -1) or overflow is layout furniture with no host — `quote` and
-- `mugshot` are DROPPED from the public render (meaningless out of layout);
-- `photo`/`cartoon` are self-contained images and fall back to the image-filler
-- render. The dummy/board view still shows everything.
--
-- PRINT POLICY (publish/build_issue.py): article-null / elem != '' placements are
-- SKIPPED from the Scribus story flow (they'd otherwise print as blank "Untitled"
-- stories — a pre-existing image-filler bug). Faithful print rendering of the new
-- elements is deferred follow-up.
--
-- RLS unchanged: placement writes are already gated by manages_issue(); the public
-- read policy already exposes every placement column, so text/elem render for anon.
-- Degrades gracefully: until this runs, inserts simply omit the columns and the
-- render defaults elem/text to ''.

alter table public.placements
  add column if not exists text text not null default '';

alter table public.placements
  add column if not exists elem text not null default ''
    check (elem in ('', 'mugshot', 'quote', 'cartoon', 'photo'));
