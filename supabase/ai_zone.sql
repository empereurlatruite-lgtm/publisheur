-- ── ai_zone ──────────────────────────────────────────────────────────────────
-- Per-edition switch for how "✦ Rédigé par IA" chronicles are laid out:
--   false (default) → the chronicle stays in the normal well and just carries the
--                     "✦ Rédigé par IA" transparency badge (a label).
--   true            → AI chronicles are pulled into a separate right-hand
--                     "Rédigé par l'IA" sidebar (the two-zone front layout).
-- The badge shows either way; this only controls the layout split. Default false
-- so an AI flag never reshuffles the page unless the editor opts in.

alter table public.papers add column if not exists ai_zone boolean not null default false;
