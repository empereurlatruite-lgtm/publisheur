-- ── styles ────────────────────────────────────────────────────────────────
-- Reusable visual skins authored by editors: a palette + fonts + photo
-- treatment, stored as data so a custom style can be created at runtime (the
-- built-in themes in web/themes.js need matching CSS in paper.html; custom ones
-- are applied as inline CSS variables instead).
--
-- A paper points at a custom style via papers.theme = 'style:<id>'. Built-in
-- themes keep their bare keys ('classic', 'noir', …). No change to `papers`.
--
-- `def` (jsonb) shape — all optional, paper.html applies what's present:
--   {
--     "paper":"#…","ink":"#…","accent":"#…","rule":"#…","muted":"#…",
--     "fontHead":"\"Oswald\",sans-serif", "fontBody":"\"PT Serif\",serif",
--     "photoFilter":"grayscale(1) contrast(1.1)"
--   }

create table if not exists public.styles (
  id         uuid primary key default gen_random_uuid(),
  owner_id   uuid not null references auth.users(id) on delete cascade default auth.uid(),
  name       text not null,
  def        jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.styles enable row level security;

-- Public read: anonymous readers render papers that may use a custom style.
drop policy if exists "styles read" on public.styles;
create policy "styles read" on public.styles
  for select using (true);

-- Owner-scoped writes.
drop policy if exists "styles insert" on public.styles;
create policy "styles insert" on public.styles
  for insert with check (owner_id = auth.uid());

drop policy if exists "styles update" on public.styles;
create policy "styles update" on public.styles
  for update using (owner_id = auth.uid()) with check (owner_id = auth.uid());

drop policy if exists "styles delete" on public.styles;
create policy "styles delete" on public.styles
  for delete using (owner_id = auth.uid());
