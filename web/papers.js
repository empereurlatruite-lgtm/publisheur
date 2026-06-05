// ── Publisheur — editions / regiment papers ────────────────────────────
// One deployment, many titles. Add your regiment's paper here; pick it with
// ?issue=<key> in the URL. Loaded by both editor.html and paper.html.
//
//   name     masthead text
//   tagline  line under the masthead (optional)
//   plate    masthead style: plate-fraktur | plate-anton | plate-echo
//   ear      three small items in the top bar [left, middle, right] (HTML ok)
//   slogans  footer slogan bar items (HTML ok); [] → plain colophon
window.DAIHBI_PAPERS = {
  "current": {
    name: "Le Petit Daihbi",
    tagline: "Journal Quotidien du Front — « Tout pour le Régiment »",
    plate: "plate-fraktur",
    ear: ["Édition du Front", "Prix : 5 centimes", "2<sup>e</sup> REI · Daihbi"],
    slogans: [],
  },
  "horizon-bleu": {
    name: "L’Horizon Bleu",
    tagline: "Sous notre bannière nous écrivons l’Histoire",
    plate: "plate-anton",
    ear: ["Front de l’Ouest", "501<sup>e</sup> Régiment", "Warden"],
    slogans: ["Vive les Wardens", "Vive la 501<sup>e</sup>", "Vive la France"],
  },
  "echo-du-front": {
    name: "L’Écho du Front",
    tagline: "Journal indépendant Warden — Témoigner, informer, tenir",
    plate: "plate-echo",
    ear: ["Numéro 002", "Édition du 4 juin 2026", "Distribution aux forces & citoyens"],
    slogans: ["Tenir la ligne", "Protéger nos foyers", "Pour Callahan !"],
  },
};
