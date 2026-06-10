-- ── img_crop_tool ────────────────────────────────────────────────────────────
-- Interactive image crop tool (board's slide-up image panel). On top of the
-- aspect ratio from img_crop.sql, an editor can pick a FOCAL POINT and ZOOM so
-- the right part of a photo stays in frame when it's cropped/bannered.
--   placements.img_focus  → CSS object-position, e.g. "50% 35%" ('' = centre)
--   placements.img_zoom   → scale factor, 1 = none (e.g. 1.4 = zoomed 40% in)
-- Both default to neutral, so every existing edition renders unchanged until an
-- editor actually uses the tool. (The lead's img_pos="top" now means a full-width
-- banner above the text — editors pick "Droite"/"Gauche" to keep a wrapped float.)
alter table public.placements add column if not exists img_focus text not null default '';
alter table public.placements add column if not exists img_zoom  real not null default 1;
