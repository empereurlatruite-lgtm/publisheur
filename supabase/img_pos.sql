-- ── img_pos ──────────────────────────────────────────────────────────────────
-- Word/Docs-style image placement for a placed chronicle's photo:
--   'top'   (default) → banner across the story's columns (snapped to img_cols)
--   'left'  → image floats left, text wraps around it
--   'right' → image floats right, text wraps around it
-- Pairs with placements.col_span (story width in columns) and img_cols (image
-- width in columns) from columns.sql. paper.html renders accordingly.

alter table public.placements add column if not exists img_pos text not null default 'top';
