-- ════════════════════════════════════════════════════════════════════════
--  PUBLISHEUR — per-edition paper theme (full visual skin)  [Phase ⑭]
--  Run once in the Supabase SQL Editor, after `papers`. Safe to re-run.
--
--  A *theme* is the whole-paper skin (palette + typography + photo treatment
--  + texture) chosen by the édition's rédacteur en chef. The set of theme
--  keys lives in web/themes.js (classic | fujimoto | noir | gazette); this
--  column just stores which one the edition publishes. Readers can still
--  preview other styles locally via the 🎨 picker — the DB value is the
--  published default everyone sees.
--
--  No new RLS needed: editing a paper row is already gated to its owner /
--  co-éditeurs by the papers policies (owns_issue / manages_issue).
-- ════════════════════════════════════════════════════════════════════════

alter table public.papers
  add column if not exists theme text not null default 'classic';
