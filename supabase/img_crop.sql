-- ── img_crop ─────────────────────────────────────────────────────────────────
-- Word/Docs-style "crop to fill": instead of the photo's natural proportions,
-- crop it (object-fit: cover) to a chosen aspect ratio so blocks line up cleanly.
--   '' (default) → natural aspect (no crop)
--   '16x9' · '3x2' · '4x3' · '1x1' · '3x4' → crop to that ratio
-- Pairs with img_pos / img_cols / col_span; paper.html applies it on the photo.

alter table public.placements add column if not exists img_crop text not null default '';
