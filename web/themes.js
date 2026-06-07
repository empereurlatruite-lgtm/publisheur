// ── Publisheur — paper themes (full visual skins) ──────────────────────────
// A *theme* restyles the whole rendered paper: colour palette, typography,
// photo treatment and texture. It is independent from the per-edition
// `plate-*` masthead identity (in papers.js) — the masthead layers on top.
//
// Pick a theme three ways, in order of priority:
//   1. URL          paper.html?issue=current&theme=fujimoto   (shareable)
//   2. the toolbar 🎨 picker on paper.html (remembered per edition, locally)
//   3. a per-edition default: set `theme:"fujimoto"` on a paper in papers.js
// …falling back to "classic" (the original warm-newsprint Daihbi look).
//
// To ADD a theme:
//   1. add an entry below (key, label, a short note, and the paper swatch),
//   2. add a matching `.sheet.theme-<key>{ … }` block in paper.html's <style>
//      overriding the CSS role variables (--ink/--paper/--accent/--font-*/…).
// The `swatch` here is only used to colour the picker option; the real look
// lives in the CSS. `key:"classic"` intentionally has no CSS (it is :root).

window.DAIHBI_THEMES = {
  classic: {
    label: "Daihbi classique",
    note:  "Encre sépia sur papier journal chaud — le style d’origine.",
    swatch: "#f5efe1",
  },
  fujimoto: {
    label: "Fujimoto · Look Back",
    note:  "Papier recyclé crème, encre charbon, terracotta fanée, trame "
         + "demi-teinte — l’atmosphère de Look Back / Chainsaw Man.",
    swatch: "#EADFC9",
  },
  noir: {
    label: "Noir d’encre",
    note:  "Tabloïd moderne : noir franc sur blanc, accent rouge, titres "
         + "condensés, photos en niveaux de gris.",
    swatch: "#ffffff",
  },
  gazette: {
    label: "Gazette (gris froid)",
    note:  "Broadsheet posé : ardoise sur blanc cassé, accent sarcelle, "
         + "Playfair sur Lora.",
    swatch: "#f3f5f7",
  },
  brasil: {
    label: "Brasil · Verde-Amarela",
    note:  "Tabloïd sportif tropical : vert jungle & or sur papier crème, "
         + "manchettes en capitales (Anton), photos vives — esprit « É PENTA ! ».",
    swatch: "#009c3b",
  },
};
