-- ── layout templates ──────────────────────────────────────────────────────
-- Reusable FIXED-GRID layout blueprints authored by editors. Where `styles`
-- captures the visual *skin* (palette/fonts/photo), a template captures the
-- *structure*: a fixed column grid + a set of CONTAINERS (the "group layout"),
-- each container owning N empty SLOTS. When an edition adopts a template the
-- front page opens as a scaffold of blank "＋" boxes — the editor clicks a ＋ to
-- drop a chronicle from the pool into that fixed cell. (writing ≠ layout: the
-- template is the editor's structural call, like placements/sections.)
--
-- A paper points at a template via papers.template — either a built-in key from
-- web/templates.js (e.g. 'front-classic') or 'tmpl:<uuid>' for a saved one.
-- '' (default) = no template → today's auto-flow well (nothing changes).
--
-- `def` (jsonb) shape — a fixed grid of `cols` columns + ordered containers:
--   {
--     "cols": 6,
--     "containers": [
--       { "id":"c1", "name":"À la une", "kind":"lead",  "col":1, "span":6,
--         "row":1, "slots":1, "perRow":1, "image":true },
--       { "id":"c2", "name":"Majeurs",  "kind":"major", "col":1, "span":4,
--         "row":2, "slots":3, "perRow":3 },
--       { "id":"c3", "name":"Articles", "kind":"minor", "col":5, "span":2,
--         "row":2, "slots":2, "perRow":1 },
--       { "id":"c4", "name":"Brèves",   "kind":"brief", "col":1, "span":6,
--         "row":3, "slots":4, "perRow":4 }
--     ]
--   }
-- kind → the placement weight a filled slot gets; col/span = grid position;
-- containers sharing a `row` sit side by side; slots tile `perRow` per line.

create table if not exists public.layout_templates (
  id         uuid primary key default gen_random_uuid(),
  owner_id   uuid not null references auth.users(id) on delete cascade default auth.uid(),
  name       text not null default '',
  def        jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.layout_templates enable row level security;

-- Public read: anonymous readers render papers that use a saved template.
drop policy if exists "tmpl read" on public.layout_templates;
create policy "tmpl read" on public.layout_templates
  for select using (true);

-- Owner-scoped writes (mirrors styles).
drop policy if exists "tmpl insert" on public.layout_templates;
create policy "tmpl insert" on public.layout_templates
  for insert with check (owner_id = auth.uid());

drop policy if exists "tmpl update" on public.layout_templates;
create policy "tmpl update" on public.layout_templates
  for update using (owner_id = auth.uid()) with check (owner_id = auth.uid());

drop policy if exists "tmpl delete" on public.layout_templates;
create policy "tmpl delete" on public.layout_templates
  for delete using (owner_id = auth.uid());

-- Which template an edition uses. Free text (built-in key | 'tmpl:<uuid>' | '')
-- so a built-in needs no DB row — same convention as papers.theme / styles.
alter table public.papers
  add column if not exists template text not null default '';

-- Which container-slot (flattened, 0-based) a placement fills. -1 = unslotted /
-- free placement (today's behaviour). Lets the renderer know which fixed cells
-- are still empty (→ show a ＋) vs filled.
alter table public.placements
  add column if not exists slot smallint not null default -1;
