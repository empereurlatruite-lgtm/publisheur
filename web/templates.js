// ── Publisheur — layout templates (fixed-grid front-page blueprints) ───────
// A *template* is the structural counterpart to a theme: where a theme is the
// visual skin (themes.js), a template is the FIXED GRID + CONTAINERS the editor
// fills. Adopt one on an edition and the front page opens as a scaffold of empty
// "＋" slots; the editor drops pooled chronicles into those fixed cells.
//
// These are the BUILT-IN starters (bare keys, e.g. "front-classic"). Editors can
// also author + save their own in the template creator; those live in the
// `layout_templates` table and are referenced as "tmpl:<uuid>" (see daihbi.js
// Templates). A paper points at whichever via papers.template ('' = none).
//
// `def` shape — a fixed grid of `cols` columns + ordered containers:
//   cols                grid column count (the page's fixed width)
//   containers[]        the "group layout" — each owns N empty slots:
//     id                stable id (for the creator / slot addressing)
//     name              container heading shown on the board scaffold
//     kind              lead | major | minor | brief → the weight a filled slot gets
//     col, span         grid position (1-based start column, columns wide)
//     row               band index; containers sharing a row sit side by side
//     slots             how many ＋ cells this container holds
//     perRow            slots tiled per line inside the container (default span)
//     image             true → slots prefer a photo (the "main image" lead)
// Slots are flattened across containers (row-major) into a 0-based index that a
// placement records in placements.slot.

window.DAIHBI_TEMPLATES = [
  {
    key: "front-classic",
    name: "Une classique",
    note: "1 à la une avec image principale · 3 majeurs · 2 articles · 4 brèves.",
    def: {
      cols: 6,
      containers: [
        { id: "une",      name: "À la une",  kind: "lead",  col: 1, span: 6, row: 1, slots: 1, perRow: 1, image: true },
        { id: "majeurs",  name: "Majeurs",   kind: "major", col: 1, span: 4, row: 2, slots: 3, perRow: 1 },
        { id: "articles", name: "Articles",  kind: "minor", col: 5, span: 2, row: 2, slots: 2, perRow: 1 },
        { id: "breves",   name: "Brèves",    kind: "brief", col: 1, span: 6, row: 3, slots: 4, perRow: 4 },
      ],
    },
  },
  {
    key: "front-photo",
    name: "Une photo",
    note: "Grande image en tête, une manchette, puis une bande d’articles.",
    def: {
      cols: 6,
      containers: [
        { id: "une",      name: "À la une",  kind: "lead",  col: 1, span: 6, row: 1, slots: 1, perRow: 1, image: true },
        { id: "articles", name: "Articles",  kind: "minor", col: 1, span: 6, row: 2, slots: 3, perRow: 3 },
        { id: "breves",   name: "Brèves",    kind: "brief", col: 1, span: 6, row: 3, slots: 4, perRow: 4 },
      ],
    },
  },
  {
    key: "front-dummy",
    name: "Une (dummy complet)",
    note: "Le dummy classique : une + portrait (mugshot) + citation en exergue + majeurs + caricature + photos.",
    def: {
      cols: 6,
      containers: [
        { id: "une",     name: "À la une",   kind: "lead",    col: 1, span: 4, row: 1, slots: 1, perRow: 1, image: true },
        { id: "mug",     name: "Portrait",   kind: "mugshot", col: 5, span: 2, row: 1, slots: 1, perRow: 1 },
        { id: "exergue", name: "Exergue",    kind: "quote",   col: 5, span: 2, row: 2, slots: 1, perRow: 1 },
        { id: "majeurs", name: "Majeurs",    kind: "major",   col: 1, span: 4, row: 2, slots: 2, perRow: 1 },
        { id: "carto",   name: "Caricature", kind: "cartoon", col: 1, span: 3, row: 3, slots: 1, perRow: 1 },
        { id: "photos",  name: "Photos",     kind: "photo",   col: 4, span: 3, row: 3, slots: 2, perRow: 1 },
      ],
    },
  },
  {
    key: "front-expedition",
    name: "Une — Expédition",
    note: "Maquette peinte : une héroïque + exergue, portrait d'expéditionnaire, deux majeurs, caricature et photos — toute la grammaire du dummy.",
    def: {
      cols: 6,
      containers: [
        // full-width hero banner up top
        { id: "une",     name: "À la une",   kind: "lead",    col: 1, span: 6, row: 1, slots: 1, perRow: 1, image: true },
        // a dramatic full-width pull-quote band (no tall-narrow gap)
        { id: "exergue", name: "Exergue",    kind: "quote",   col: 1, span: 6, row: 2, slots: 1, perRow: 1 },
        // two half-width major stories across the full width
        { id: "majeurs", name: "Majeurs",    kind: "major",   col: 1, span: 6, row: 3, slots: 2, perRow: 2 },
        // a tight row of three equal cells: portrait + two photos
        { id: "mug",     name: "Portrait",   kind: "mugshot", col: 1, span: 2, row: 4, slots: 1, perRow: 1 },
        { id: "photoA",  name: "Photo",      kind: "photo",   col: 3, span: 2, row: 4, slots: 1, perRow: 1 },
        { id: "photoB",  name: "Photo",      kind: "photo",   col: 5, span: 2, row: 4, slots: 1, perRow: 1 },
        // full-width illustration band (the parade art is landscape → fills it)
        { id: "carto",   name: "Caricature", kind: "cartoon", col: 1, span: 6, row: 5, slots: 1, perRow: 1 },
      ],
    },
  },
  {
    key: "front-dense",
    name: "Une dense",
    note: "Beaucoup de sujets : 1 une, 4 majeurs en deux colonnes, 6 brèves.",
    def: {
      cols: 6,
      containers: [
        { id: "une",     name: "À la une", kind: "lead",  col: 1, span: 6, row: 1, slots: 1, perRow: 1, image: true },
        { id: "majeurs", name: "Majeurs",  kind: "major", col: 1, span: 6, row: 2, slots: 4, perRow: 2 },
        { id: "breves",  name: "Brèves",   kind: "brief", col: 1, span: 6, row: 3, slots: 6, perRow: 3 },
      ],
    },
  },
];
