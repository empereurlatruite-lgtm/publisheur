-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — author identity on a chronicle (engraved portrait + name)
--  Run once in the Supabase SQL Editor. Safe to re-run.
--
--  `byline` already holds the author's NAME. This adds the author's avatar so a
--  chronicle carries its correspondent's face into every paper that runs it.
-- ════════════════════════════════════════════════════════════════════════

alter table public.articles
  add column if not exists author_avatar text not null default '';

-- No RLS change: the existing "art author update" policy (author_id = auth.uid())
-- already governs who can set it.
-- ════════════════════════════════════════════════════════════════════════
