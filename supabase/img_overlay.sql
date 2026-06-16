-- ── img_overlay ──────────────────────────────────────────────────────────────
-- Editor-typed text laid OVER a placement's photo (magazine caption / movie-
-- poster title), distinct from the author CREDIT that sits below the image. It is
-- per-placement layout (the editor's layer, not the chronicle), set on the board's
-- slide-up image panel; rendered in paper.html and the Scribus print PDF.
--   placements.img_overlay        → the overlay text ('' = none, nothing renders)
--   placements.img_overlay_style  → 'band'  (caption band + dark scrim, small caps)
--                                 | 'cover' (big display title, poster style)
--   placements.img_overlay_pos    → 'bottom' | 'center' | 'top' — anchor inside the
--                                    image (where the band/title sits)
-- All neutral by default, so every existing edition renders unchanged until an
-- editor types overlay text on a photo.
alter table public.placements add column if not exists img_overlay       text not null default '';
alter table public.placements add column if not exists img_overlay_style text not null default 'band'
  check (img_overlay_style in ('band','cover'));
alter table public.placements add column if not exists img_overlay_pos   text not null default 'bottom'
  check (img_overlay_pos in ('bottom','center','top'));
