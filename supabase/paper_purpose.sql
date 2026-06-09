-- ── paper_purpose ────────────────────────────────────────────────────────────
-- A short "what is this paper about" summary, set in Gérer le journal and shown
-- on the kiosque card so readers understand each edition's purpose at a glance.
-- (Language uses the existing papers.lang; the 🔄 Republier freshness bump reuses
-- placements.updated_at, so no extra columns are needed for those.)

alter table public.papers add column if not exists purpose text not null default '';
