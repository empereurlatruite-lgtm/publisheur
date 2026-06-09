-- ── columns ─────────────────────────────────────────────────────────────────
-- Editor-controlled column layout. Three layout knobs, all defaulting to 0 =
-- "auto" so existing editions render exactly as before until an editor opts in:
--
--   papers.grid_cols   how many columns the front-page "well" has.
--                      0 = auto (the responsive 3→4 default); >0 = fixed count.
--   placements.col_span how many of those columns a placed chronicle spans.
--                      0 = auto by weight (major = 2, everything else = 1).
--   placements.img_cols the story photo's width in columns (snaps to the grid).
--                      0 = auto (image = full story width). When img_cols <
--                      col_span the photo floats and the text wraps around it;
--                      when ≥ col_span it is a full-width banner.
--
-- These are LAYOUT decisions (the rédacteur en chef's call), so they live on
-- papers/placements — never on the chronicle. No RLS change: the existing
-- "papers update" / "placements" policies already gate writes to managing
-- editors. paper.html reads the three values and lays out the grid accordingly.

alter table public.papers      add column if not exists grid_cols smallint not null default 0;
alter table public.placements  add column if not exists col_span  smallint not null default 0;
alter table public.placements  add column if not exists img_cols  smallint not null default 0;
