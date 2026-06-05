// ── Publisheur — editions / regiment papers ────────────────────────────
// One deployment, many titles. Add your regiment's paper here; pick it with
// ?issue=<key> in the URL. Loaded by both editor.html and paper.html.
//
//   name        masthead text
//   tagline     line under the masthead (optional)
//   plate       masthead style: plate-fraktur | plate-anton | plate-echo
//   ear         three small items in the top bar [left, middle, right] (HTML ok)
//   slogans     footer slogan bar items (HTML ok); [] → plain colophon
//   emblemLeft  URL of a crest shown left of the nameplate (full colour, optional)
//   emblemRight URL of a crest shown right of the nameplate (optional)
//
// To give a paper its own crest: upload a transparent PNG to the Storage
// "media" bucket (or via the editor), then paste its public URL into
// emblemLeft / emblemRight here. The shared Warden shield is below.
// Régiments / clans offered at signup (free list — add yours here).
window.DAIHBI_CLANS = ["2e REI","501e","8e","79e","30e","La Bleusaille","les Frogz","1re armée Jeunesse Warden","Indépendant","Autre"];

const WARDEN_SHIELD = "https://atnmzlaiglmkykzryjar.supabase.co/storage/v1/object/public/media/emblems/warden-shield.png";
window.DAIHBI_PAPERS = {
  "current": {
    name: "Le Petit Daihbi",
    tagline: "Journal Quotidien du Front — « Tout pour le Régiment »",
    plate: "plate-fraktur",
    ear: ["Édition du Front", "Prix : 5 centimes", "2<sup>e</sup> REI · Daihbi"],
    slogans: [],
    emblemRight: WARDEN_SHIELD,
  },
  "horizon-bleu": {
    name: "L’Horizon Bleu",
    tagline: "Sous notre bannière nous écrivons l’Histoire",
    plate: "plate-anton",
    ear: ["Front de l’Est", "501<sup>e</sup> Régiment", "Warden"],
    slogans: ["Vive les Wardens", "Vive la 501<sup>e</sup>", "Vive la France"],
    emblemRight: WARDEN_SHIELD,
  },
  "echo-du-front": {
    name: "L’Écho du Front",
    tagline: "Journal indépendant Warden — Témoigner, informer, tenir",
    plate: "plate-echo",
    ear: ["Numéro 002", "Édition du 4 juin 2026", "Distribution aux forces & citoyens"],
    slogans: ["Tenir la ligne", "Protéger nos foyers", "Pour Callahan !"],
    emblemRight: WARDEN_SHIELD,
  },
};
