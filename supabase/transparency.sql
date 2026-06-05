-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — provenance / transparency on a chronicle
--  Run once in the Supabase SQL Editor. Safe to re-run.
--
--  Papers are SHARED and an article can run in several of them, so attribution
--  lives on the chronicle: `source` = the régiment it comes from (e.g. "501e"),
--  or "IA" when the text was AI-generated — shown as a badge for transparency.
-- ════════════════════════════════════════════════════════════════════════

alter table public.articles
  add column if not exists source text not null default '';

-- Governed by the existing "art author update" policy (author_id = auth.uid()).
-- ════════════════════════════════════════════════════════════════════════
