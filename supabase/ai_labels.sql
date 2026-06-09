-- ── ai_labels ────────────────────────────────────────────────────────────────
-- Transparency: an editor can flag a chronicle as AI-TRANSLATED. (AI-WRITTEN is
-- already conveyed by the source = "IA" sentinel — paper.html renders the
-- "✦ Rédigé par IA" badge and routes it to the AI zone.) "Translated by AI" is
-- orthogonal — a régiment chronicle may also be an AI translation — so it gets
-- its own boolean. paper.html shows a "✦ Traduit par IA" badge when set.
-- Defaults false → existing chronicles are unaffected.

alter table public.articles add column if not exists ai_translated boolean not null default false;
