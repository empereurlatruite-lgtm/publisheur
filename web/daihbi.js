// ── Publisheur — shared Supabase data + auth layer ─────────────────────
// Loaded by both editor.html and paper.html. Requires config.js and the
// @supabase/supabase-js UMD bundle to be loaded first.
//
// Wrapped in an IIFE so its internals (Auth, Articles, esc, md, …) stay
// private — only `window.Daihbi` is exposed. Without this, these top-level
// `const`s would become globals and collide with the pages' inline
// `const { Auth, Articles } = window.Daihbi` (SyntaxError: already declared).
(function () {
const CFG = window.DAIHBI_CONFIG || {};
// Edition can be chosen per-URL (?issue=horizon-bleu) so one deployment serves
// many regiments' papers; falls back to config.js, then "current".
const ISSUE =
  new URLSearchParams(location.search).get("issue") || CFG.ISSUE || "current";

const _configured =
  CFG.SUPABASE_URL && !CFG.SUPABASE_URL.includes("YOUR-PROJECT") &&
  CFG.SUPABASE_ANON_KEY && !CFG.SUPABASE_ANON_KEY.includes("YOUR-ANON");

// `supabase` is the global from the UMD bundle; createClient lives on it.
const db = _configured
  ? window.supabase.createClient(CFG.SUPABASE_URL, CFG.SUPABASE_ANON_KEY)
  : null;

const WEIGHTS = ["lead", "major", "minor", "brief"];
const WRANK = Object.fromEntries(WEIGHTS.map((w, i) => [w, i]));

// Canonical redirect for auth emails: use the configured public origin (so a
// signup done on localhost still mails a prod link), keeping the current page's
// path so the user lands back where they started. Falls back to the live page
// only when SITE_URL is unset (pure local dev).
function authRedirect() {
  const base = String(CFG.SITE_URL || "").replace(/\/+$/, "");
  return base
    ? base + location.pathname + location.search
    : location.href.split("#")[0];
}

// ── I18n: interface language + multilingual content helpers ─────────────
// The platform is no longer French-only. `I18n` drives the *UI chrome*
// (translatable strings, a language switcher, locale-aware dates) while
// `LANGS` is the curated set of *content* languages an author can tag a
// chronicle / ad / paper with. Pages register their own chrome strings via
// I18n.register({fr:{…}, en:{…}}) then call I18n.apply().
//
// Content languages (code → endonym label → BCP-47 locale). Endonyms are shown
// untranslated, the convention for language pickers.
const LANGS = [
  { code: "fr", label: "Français",     locale: "fr-FR" },
  { code: "en", label: "English",      locale: "en-US" },
  { code: "de", label: "Deutsch",      locale: "de-DE" },
  { code: "es", label: "Español",      locale: "es-ES" },
  { code: "it", label: "Italiano",     locale: "it-IT" },
  { code: "pl", label: "Polski",       locale: "pl-PL" },
  { code: "ru", label: "Русский",      locale: "ru-RU" },
  { code: "pt", label: "Português",    locale: "pt-PT" },
  { code: "nl", label: "Nederlands",   locale: "nl-NL" },
  { code: "other", label: "Autre / Other", locale: "en-US" },
];
// Interface (chrome) languages we currently ship dictionaries for.
const UI_LANGS = ["fr", "en"];

// Shared chrome strings. Page-specific keys are merged in per page.
const STRINGS = {
  fr: {
    "nav.login": "Se connecter", "nav.profile": "Mon profil",
    "nav.logout": "Se déconnecter", "nav.langLabel": "Langue de l’interface",
    "kiosk.allLangs": "Toutes les langues",
    "role.reader": "Lecteur", "role.writer": "Chroniqueur",
    "role.illustrator": "Illustrateur / Propagandiste",
    "role.editor": "Rédacteur en chef", "role.annonceur": "Annonceur",
    "status.draft": "Brouillon", "status.submitted": "Soumise au pool",
    "status.review": "Soumise au pool", "status.published": "Soumise au pool",
    "adstatus.draft": "Brouillon", "adstatus.review": "En attente",
    "adstatus.approved": "Approuvée", "adstatus.rejected": "Refusée",
    "weight.lead": "La Une", "weight.major": "Majeurs",
    "weight.minor": "Mineurs", "weight.brief": "Brèves",
    "adcat.recrutement": "Recrutement", "adcat.troc": "Troc",
    "adcat.parodie": "Parodie", "adcat.createur": "Créateur",
    "adcat.fabricant": "Fabricant",
    "err.notImage": "Ce fichier n’est pas une image.",
    "err.tooHeavy": "Image trop lourde (max 15 Mo).",
    "err.unreadable": "Image illisible ou corrompue.",
    "err.noDims": "Dimensions d’image introuvables.",
    "err.convert": "Conversion de l’image impossible.",
    "err.sendFail": "Échec de l’envoi.", "err.generic": "Échec.",
    "chronicle.untitled": "Sans titre",
    "comment.loginToComment": "Connectez-vous pour commenter.",
    "auth.close": "Fermer", "auth.emailPh": "vous@exemple.com",
    "auth.expiredTitle": "Lien expiré",
    "auth.expiredDesc": "Ce lien n’est plus valide — il a expiré ou a déjà été utilisé. Entrez votre adresse pour en recevoir un nouveau.",
    "auth.resend": "Renvoyer le lien", "auth.invalidEmail": "Adresse e-mail invalide.",
    "auth.sending": "Envoi…", "auth.newLinkSent": "Nouveau lien envoyé — vérifiez votre boîte mail.",
    "auth.forgotTitle": "Mot de passe oublié",
    "auth.forgotDesc": "Entrez votre adresse ; nous vous enverrons un lien pour réinitialiser votre mot de passe.",
    "auth.sendLink": "Envoyer le lien", "auth.linkSent": "Lien envoyé — vérifiez votre boîte mail.",
    "auth.linkHint": "Pensez à regarder vos spams. Le lien expire après environ 1 h ; ouvrez-le sur cet appareil.",
    "auth.recoveryTitle": "Nouveau mot de passe",
    "auth.recoveryDesc": "Choisissez un nouveau mot de passe pour votre compte.",
    "auth.newPwPh": "Nouveau mot de passe", "auth.confirmPwPh": "Confirmez le mot de passe",
    "auth.update": "Mettre à jour", "auth.min8": "8 caractères minimum.",
    "auth.pwMismatch": "Les mots de passe ne correspondent pas.", "auth.updating": "Mise à jour…",
    "auth.pwUpdated": "Mot de passe mis à jour ✓", "auth.updateFail": "Échec de la mise à jour.",
    "auth.signin": "Se connecter", "auth.signup": "Créer un compte",
    "auth.pwPh": "mot de passe", "auth.createMyAccount": "Créer mon compte",
    "auth.haveAccount": "Vous avez déjà un compte ? Choisissez « Se connecter ».",
    "auth.magicLink": "Recevoir un lien par e-mail", "auth.forgotQ": "Mot de passe oublié ?",
    "auth.pwTooShort": "Mot de passe trop court (6 caractères min.).",
    "auth.creating": "Création…", "auth.connecting": "Connexion…",
    "auth.accountCreated": "Compte créé ✓",
    "auth.accountCreatedConfirm": "Compte créé — vérifiez votre e-mail pour confirmer.",
    "auth.connected": "Connecté ✓", "auth.enterEmailFirst": "Entrez d’abord votre adresse.",
    "auth.sendingLink": "Envoi du lien…",
  },
  en: {
    "nav.login": "Sign in", "nav.profile": "My profile",
    "nav.logout": "Sign out", "nav.langLabel": "Interface language",
    "kiosk.allLangs": "All languages",
    "role.reader": "Reader", "role.writer": "Columnist",
    "role.illustrator": "Illustrator / Propagandist",
    "role.editor": "Editor-in-chief", "role.annonceur": "Advertiser",
    "status.draft": "Draft", "status.submitted": "Submitted to the pool",
    "status.review": "Submitted to the pool", "status.published": "Submitted to the pool",
    "adstatus.draft": "Draft", "adstatus.review": "Pending",
    "adstatus.approved": "Approved", "adstatus.rejected": "Rejected",
    "weight.lead": "Front page", "weight.major": "Major",
    "weight.minor": "Minor", "weight.brief": "Briefs",
    "adcat.recrutement": "Recruitment", "adcat.troc": "Barter",
    "adcat.parodie": "Parody", "adcat.createur": "Creator",
    "adcat.fabricant": "Manufacturer",
    "err.notImage": "This file is not an image.",
    "err.tooHeavy": "Image too large (max 15 MB).",
    "err.unreadable": "Unreadable or corrupted image.",
    "err.noDims": "Could not read the image dimensions.",
    "err.convert": "Could not convert the image.",
    "err.sendFail": "Sending failed.", "err.generic": "Something went wrong.",
    "chronicle.untitled": "Untitled",
    "comment.loginToComment": "Sign in to comment.",
    "auth.close": "Close", "auth.emailPh": "you@example.com",
    "auth.expiredTitle": "Link expired",
    "auth.expiredDesc": "This link is no longer valid — it has expired or was already used. Enter your address to get a new one.",
    "auth.resend": "Resend link", "auth.invalidEmail": "Invalid email address.",
    "auth.sending": "Sending…", "auth.newLinkSent": "New link sent — check your inbox.",
    "auth.forgotTitle": "Forgot password",
    "auth.forgotDesc": "Enter your address; we’ll send you a link to reset your password.",
    "auth.sendLink": "Send link", "auth.linkSent": "Link sent — check your inbox.",
    "auth.linkHint": "Check your spam folder too. The link expires after about 1 h; open it on this device.",
    "auth.recoveryTitle": "New password",
    "auth.recoveryDesc": "Choose a new password for your account.",
    "auth.newPwPh": "New password", "auth.confirmPwPh": "Confirm password",
    "auth.update": "Update", "auth.min8": "8 characters minimum.",
    "auth.pwMismatch": "Passwords do not match.", "auth.updating": "Updating…",
    "auth.pwUpdated": "Password updated ✓", "auth.updateFail": "Update failed.",
    "auth.signin": "Sign in", "auth.signup": "Create account",
    "auth.pwPh": "password", "auth.createMyAccount": "Create my account",
    "auth.haveAccount": "Already have an account? Choose “Sign in”.",
    "auth.magicLink": "Get a link by email", "auth.forgotQ": "Forgot password?",
    "auth.pwTooShort": "Password too short (6 characters min.).",
    "auth.creating": "Creating…", "auth.connecting": "Signing in…",
    "auth.accountCreated": "Account created ✓",
    "auth.accountCreatedConfirm": "Account created — check your email to confirm.",
    "auth.connected": "Signed in ✓", "auth.enterEmailFirst": "Enter your address first.",
    "auth.sendingLink": "Sending link…",
  },
};

// Default interface language is French (this is the Warden francophone press).
// An explicit choice — the user's saved switcher pick (localStorage) or, for a
// signed-in user, their profile.ui_lang (see adoptProfile) — overrides it.
const DEFAULT_UI = "fr";
let _ui = (() => {
  try { const s = localStorage.getItem("daihbi_ui_lang"); if (s && UI_LANGS.includes(s)) return s; } catch (e) {}
  return DEFAULT_UI;
})();

function _labelOf(code) { const l = LANGS.find(x => x.code === code); return l ? l.label : code; }

const I18n = {
  LANGS, UI_LANGS,
  lang() { return _ui; },
  localeFor(code) { const l = LANGS.find(x => x.code === code); return l ? l.locale : "en-US"; },
  langLabel(code) { return _labelOf(code); },
  /** Look up a chrome string for the current UI language (FR fallback, then key). */
  t(key, vars) {
    const d = STRINGS[_ui] || {};
    let s = (key in d) ? d[key] : (STRINGS.fr || {})[key];
    if (s == null) s = key;
    if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? vars[k] : m));
    return s;
  },
  /** Merge page-specific strings: register({fr:{…}, en:{…}}). */
  register(dict) {
    for (const L of Object.keys(dict || {})) STRINGS[L] = Object.assign(STRINGS[L] || {}, dict[L]);
    return this;
  },
  /** Translate a DOM subtree via data-i18n[/-html/-ph/-title/-aria] attributes. */
  apply(root) {
    root = root || document;
    const set = (attr, fn) => root.querySelectorAll("[" + attr + "]").forEach(el => {
      const v = I18n.t(el.getAttribute(attr)); if (v != null) fn(el, v);
    });
    set("data-i18n",       (el, v) => { el.textContent = v; });
    set("data-i18n-html",  (el, v) => { el.innerHTML = v; });
    set("data-i18n-ph",    (el, v) => { el.setAttribute("placeholder", v); });
    set("data-i18n-title", (el, v) => { el.setAttribute("title", v); });
    set("data-i18n-aria",  (el, v) => { el.setAttribute("aria-label", v); });
    if (root === document || root === document.documentElement)
      document.documentElement.lang = _ui;
    return this;
  },
  /** Switch the interface language (persists to localStorage + profile). */
  set(code) {
    if (!UI_LANGS.includes(code) || code === _ui) return this;
    _ui = code;
    try { localStorage.setItem("daihbi_ui_lang", code); } catch (e) {}
    Promise.resolve().then(() => Profiles.update({ ui_lang: code })).catch(() => {});
    I18n.apply(document);
    document.dispatchEvent(new CustomEvent("daihbi:langchange", { detail: { lang: code } }));
    return this;
  },
  /** Adopt a signed-in user's saved ui_lang — unless they made an explicit local choice. */
  adoptProfile(p) {
    let chosen = null; try { chosen = localStorage.getItem("daihbi_ui_lang"); } catch (e) {}
    if (chosen) return this;
    if (p && p.ui_lang && UI_LANGS.includes(p.ui_lang) && p.ui_lang !== _ui) {
      _ui = p.ui_lang; I18n.apply(document);
      document.dispatchEvent(new CustomEvent("daihbi:langchange", { detail: { lang: _ui } }));
    }
    return this;
  },
  /** Locale-aware date / datetime, optionally in a specific CONTENT language. */
  fmtDate(d, opts, localeCode) {
    try { return new Date(d).toLocaleDateString(I18n.localeFor(localeCode || _ui),
      opts || { weekday: "long", year: "numeric", month: "long", day: "numeric" }); }
    catch (e) { return ""; }
  },
  fmtDateTime(d, opts, localeCode) {
    try { return opts
      ? new Date(d).toLocaleString(I18n.localeFor(localeCode || _ui), opts)
      : new Date(d).toLocaleString(I18n.localeFor(localeCode || _ui)); }
    catch (e) { return ""; }
  },
  /** <option> markup for a content-language <select>. */
  contentOptionsHTML(selected, includeAll) {
    const all = includeAll
      ? `<option value=""${!selected ? " selected" : ""}>${esc(I18n.t("kiosk.allLangs"))}</option>` : "";
    return all + LANGS.map(l =>
      `<option value="${l.code}"${l.code === selected ? " selected" : ""}>${esc(l.label)}</option>`).join("");
  },
  /** The interface-language switcher <select> (used in the masthead). */
  switcherHTML() {
    const opts = UI_LANGS.map(c =>
      `<option value="${c}"${c === _ui ? " selected" : ""}>${esc(_labelOf(c))}</option>`).join("");
    return `<select class="navlang" aria-label="${esc(I18n.t("nav.langLabel"))}" title="${esc(I18n.t("nav.langLabel"))}">${opts}</select>`;
  },
  bindSwitcher(scope) {
    const sel = (scope || document).querySelector(".navlang");
    if (sel) sel.addEventListener("change", e => I18n.set(e.target.value));
  },
};

// Reader/writer content-language preference (kiosque filter, composer default).
// Profile is the source of truth when signed in; localStorage covers guests and
// gives an instant default before the async profile resolves.
const Prefs = {
  contentLangLocal() { try { return localStorage.getItem("daihbi_pref_lang") || ""; } catch (e) { return ""; } },
  async contentLang() {
    try {
      const u = await Auth.user();
      if (u) { const p = await Profiles.me(); if (p && p.preferred_lang) return p.preferred_lang; }
    } catch (e) {}
    return Prefs.contentLangLocal();
  },
  async setContentLang(code) {
    try { localStorage.setItem("daihbi_pref_lang", code || ""); } catch (e) {}
    try { await Profiles.update({ preferred_lang: code || "" }); } catch (e) {}
  },
};

// ── Auth ────────────────────────────────────────────────────────────────
const Auth = {
  configured: () => !!db,
  async session() {
    if (!db) return null;
    const { data } = await db.auth.getSession();
    return data.session;
  },
  async user() {
    return (await this.session())?.user || null;
  },
  async signIn(email) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { error } = await db.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: authRedirect() },
    });
    if (error) throw error;
  },
  async signInPassword(email, password) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { error } = await db.auth.signInWithPassword({ email, password });
    if (error) throw error;
  },
  async signUp(email, password, meta) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { data, error } = await db.auth.signUp({
      email, password,
      options: { emailRedirectTo: authRedirect(), data: meta || {} },
    });
    if (error) throw error;
    return data; // data.session is non-null when email auto-confirm is on
  },
  /** Send a password-recovery email. The link returns to `redirectTo`
   *  (defaults to editor.html) where the recovery session lets the user
   *  set a new password via updatePassword(). */
  async resetPassword(email, redirectTo) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    // Recovery always lands on editor.html (which hosts the "new password"
    // screen). Prefer the configured public origin so the mailed link is the
    // allow-listed prod one even when reset is requested from localhost.
    const base = String(CFG.SITE_URL || "").replace(/\/+$/, "");
    const dflt = base ? base + "/editor.html" : new URL("editor.html", location.href).href;
    const { error } = await db.auth.resetPasswordForEmail(email, {
      redirectTo: redirectTo || dflt,
    });
    if (error) throw error;
  },
  /** Set a new password for the currently-authenticated (or recovery) session. */
  async updatePassword(password) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { error } = await db.auth.updateUser({ password });
    if (error) throw error;
  },
  async signOut() {
    if (db) await db.auth.signOut();
  },
  onChange(cb) {
    if (db) db.auth.onAuthStateChange((event, session) => cb(session, event));
  },
  /** Re-send a magic sign-in link (used when a previous link expired). */
  async resendLink(email) {
    return this.signIn(email);
  },
};

// ── Chronicles ─ articles = the writer's TEXT (a chronicle), not bound to a paper
const Chronicles = {
  /** The current user's own chronicles (writer's "Mes chroniques"). */
  async listMine() {
    if (!db) return [];
    const { data: { user } } = await db.auth.getUser();
    if (!user) return [];
    const { data, error } = await db.from("articles").select("*")
      .eq("author_id", user.id).order("updated_at", { ascending: false });
    if (error) throw error;
    return data || [];
  },
  /** The shared pool: submitted chronicles for editors to browse. */
  async listPool(q) {
    if (!db) return [];
    const { data, error } = await db.from("articles").select("*")
      .eq("status", "submitted").order("updated_at", { ascending: false }).limit(300);
    if (error) throw error;
    let rows = data || [];
    if (q) { const s = q.toLowerCase();
      rows = rows.filter(a => ((a.headline||"")+" "+(a.byline||"")+" "+(a.kicker||"")).toLowerCase().includes(s)); }
    return rows;
  },
  async get(id) {
    const { data, error } = await db.from("articles").select("*").eq("id", id).single();
    if (error) throw error;
    return data;
  },
  async create(fields) {
    const { data: { user } } = await db.auth.getUser();
    const row = { kicker:"", headline:I18n.t("chronicle.untitled"), subhead:"", byline:"", body:"",
      image_url:"", lang:"fr", status:"draft", author_id: user?.id || null, ...fields };
    const { data, error } = await db.from("articles").insert(row).select().single();
    if (error) throw error;
    return data;
  },
  async update(id, fields) {
    const { data, error } = await db.from("articles").update(fields).eq("id", id).select().single();
    if (error) throw error;
    return data;
  },
  async remove(id) { const { error } = await db.from("articles").delete().eq("id", id); if (error) throw error; },
  async submit(id) { return this.update(id, { status: "submitted" }); },
  async toDraft(id) { return this.update(id, { status: "draft" }); },
  subscribe(cb) {
    if (!db) return;
    db.channel("chronicles").on("postgres_changes",
      { event: "*", schema: "public", table: "articles" }, () => cb()).subscribe();
  },
};

// ── Placements ─ an editor runs a chronicle in their edition (the LAYOUT) ────
const Placements = {
  /** Set of article ids that are placed in ANY edition (for the "never used"
   *  pool filter). RLS: authenticated read is unrestricted. */
  async usedArticleIds() {
    if (!db) return new Set();
    const { data, error } = await db.from("placements").select("article_id");
    if (error) throw error;
    return new Set((data || []).map((r) => r.article_id));
  },
  /** Board view: every placement in the edition + its joined chronicle. */
  async forIssue(issue) {
    if (!db) return [];
    const { data, error } = await db.from("placements")
      .select("*, article:articles(*)").eq("issue", issue);
    if (error) throw error;
    return data || [];
  },
  /** Public render: published placements + chronicle, sorted by weight+position. */
  async publishedForIssue(issue) {
    if (!db) return [];
    const { data, error } = await db.from("placements")
      .select("*, article:articles(*)").eq("issue", issue).eq("published", true);
    if (error) throw error;
    return (data || []).sort((a, b) =>
      (WRANK[a.weight] ?? 9) - (WRANK[b.weight] ?? 9) || (a.position||0) - (b.position||0));
  },
  async add(articleId, issue) {
    const { data: { user } } = await db.auth.getUser();
    const { data, error } = await db.from("placements")
      .insert({ article_id: articleId, issue, weight: "minor", position: 0, published: false, placed_by: user?.id || null })
      .select("*, article:articles(*)").single();
    if (error) throw error;
    return data;
  },
  async update(id, fields) {
    const { data, error } = await db.from("placements").update(fields).eq("id", id).select("*, article:articles(*)").single();
    if (error) throw error;
    return data;
  },
  async remove(id) { const { error } = await db.from("placements").delete().eq("id", id); if (error) throw error; },
  subscribe(issue, cb) {
    if (!db) return;
    db.channel("placements-" + issue).on("postgres_changes",
      { event: "*", schema: "public", table: "placements" }, () => cb()).subscribe();
  },
};

// ── AdPlacements ─ an editor runs an approved réclame in their edition ───────
// Mirrors Placements (writing ≠ layout): an `ad` is the advertiser's content;
// an `ad_placement` is an editor dropping it into an edition at a chosen order.
// Ads have no weight — only `position`.
const AdPlacements = {
  /** Board view: every ad placement in the edition + its joined ad. */
  async forIssue(issue) {
    if (!db) return [];
    const { data, error } = await db.from("ad_placements")
      .select("*, ad:ads(*)").eq("issue", issue);
    if (error) throw error;
    return data || [];
  },
  /** Public render: published ad placements + ad, sorted by position. */
  async publishedForIssue(issue) {
    if (!db) return [];
    const { data, error } = await db.from("ad_placements")
      .select("*, ad:ads(*)").eq("issue", issue).eq("published", true);
    if (error) throw error;
    return (data || []).sort((a, b) => (a.position||0) - (b.position||0));
  },
  async add(adId, issue) {
    const { data: { user } } = await db.auth.getUser();
    const { data, error } = await db.from("ad_placements")
      .insert({ ad_id: adId, issue, position: 0, published: false, placed_by: user?.id || null })
      .select("*, ad:ads(*)").single();
    if (error) throw error;
    return data;
  },
  async update(id, fields) {
    const { data, error } = await db.from("ad_placements").update(fields).eq("id", id).select("*, ad:ads(*)").single();
    if (error) throw error;
    return data;
  },
  async remove(id) { const { error } = await db.from("ad_placements").delete().eq("id", id); if (error) throw error; },
  subscribe(issue, cb) {
    if (!db) return;
    db.channel("ad-placements-" + issue).on("postgres_changes",
      { event: "*", schema: "public", table: "ad_placements" }, () => cb()).subscribe();
  },
};

// ── Media: upload images (article photos, avatars, portfolio) to Storage ────
// Every image is re-encoded client-side through a canvas before upload. This
// (a) strips EXIF/GPS and neutralises any payload smuggled in the file — the
// "safe" part — and (b) normalises everyone's photo to one web format (WebP),
// downscaled to a sane size. The re-encode also yields the width/height/bytes/
// mime we record as provenance. upload() returns that metadata, not just a URL.
function decodeImage(file) {
  // createImageBitmap is fast but not everywhere / for every format → <img> fallback.
  if (window.createImageBitmap) {
    return createImageBitmap(file).catch(() => decodeViaImg(file));
  }
  return decodeViaImg(file);
}
function decodeViaImg(file) {
  return new Promise((res, rej) => {
    const img = new Image();
    const u = URL.createObjectURL(file);
    img.onload = () => { res(img); URL.revokeObjectURL(u); };
    img.onerror = () => { URL.revokeObjectURL(u); rej(new Error(I18n.t("err.unreadable"))); };
    img.src = u;
  });
}
const Media = {
  MAX_EDGE: 2200,        // longest side after downscale (px)
  QUALITY: 0.9,          // WebP quality

  /** Re-encode + downscale a File to a safe WebP blob; returns {blob,width,height,bytes,mime}. */
  async sanitize(file) {
    if (!file || !file.type || !file.type.startsWith("image/"))
      throw new Error(I18n.t("err.notImage"));
    if (file.size > 15 * 1024 * 1024)
      throw new Error(I18n.t("err.tooHeavy"));
    const src = await decodeImage(file);
    const sw = src.width || src.naturalWidth, sh = src.height || src.naturalHeight;
    if (!sw || !sh) throw new Error(I18n.t("err.noDims"));
    const scale = Math.min(1, this.MAX_EDGE / Math.max(sw, sh));
    const w = Math.max(1, Math.round(sw * scale)), h = Math.max(1, Math.round(sh * scale));
    const canvas = document.createElement("canvas");
    canvas.width = w; canvas.height = h;
    canvas.getContext("2d").drawImage(src, 0, 0, w, h);
    if (src.close) src.close(); // free the ImageBitmap
    const blob = await new Promise((res, rej) =>
      canvas.toBlob(b => b ? res(b) : rej(new Error(I18n.t("err.convert"))), "image/webp", this.QUALITY));
    return { blob, width: w, height: h, bytes: blob.size, mime: "image/webp" };
  },

  /** Sanitise + upload into <folder>/, record provenance, return {url,width,height,bytes,mime}. */
  async upload(file, folder) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const meta = await this.sanitize(file);
    const path = `${folder || ISSUE}/${Date.now()}-${Math.random().toString(36).slice(2, 8)}.webp`;
    const { error } = await db.storage.from("media").upload(path, meta.blob, {
      cacheControl: "31536000", upsert: false, contentType: meta.mime,
    });
    if (error) throw error;
    const url = db.storage.from("media").getPublicUrl(path).data.publicUrl;
    // Record the asset + who made it / how big. Best-effort: a missing `media`
    // table (migration not yet run) must never block the actual upload.
    try {
      const { data: { user } } = await db.auth.getUser();
      let uploader_name = (user && user.email) || "";
      if (user) {
        const { data: prof } = await db.from("profiles").select("display_name").eq("id", user.id).maybeSingle();
        if (prof && prof.display_name) uploader_name = prof.display_name;
      }
      await db.from("media").insert({
        url, path, folder: folder || ISSUE, uploader_name,
        mime: meta.mime, bytes: meta.bytes, width: meta.width, height: meta.height,
      });
    } catch (e) { /* provenance is non-critical — keep the URL */ }
    return { url, width: meta.width, height: meta.height, bytes: meta.bytes, mime: meta.mime };
  },
};

// ── Profiles: role / régiment / avatar / display name ───────────────────────
const Profiles = {
  /** The current user's profile (or a reader default if none yet). */
  async me() {
    if (!db) return null;
    const { data: { user } } = await db.auth.getUser();
    if (!user) return null;
    const { data } = await db.from("profiles").select("*").eq("id", user.id).maybeSingle();
    return data || { id: user.id, role: "reader", display_name: "", clan: "", avatar_url: "" };
  },
  async update(fields) {
    const { data: { user } } = await db.auth.getUser();
    const { data, error } = await db.from("profiles").update(fields).eq("id", user.id).select().single();
    if (error) throw error;
    return data;
  },
  async get(id) {
    if (!db || !id) return null;
    const { data } = await db.from("profiles").select("*").eq("id", id).maybeSingle();
    return data;
  },
  /** All profiles (for editor pickers). */
  async all() {
    if (!db) return [];
    const { data } = await db.from("profiles").select("id,display_name,role,clan");
    return data || [];
  },
};

// ── NavUser: the shared account control in the header (avatar + logout, or
//    an obvious "Se connecter" button when signed out). Used by every page. ─
const NavUser = {
  /**
   * Render the account control into `el`.
   * opts: { profile, email, role, roleLabel, onLogout, onAvatar, onLogin, loginHref }
   *   - signed in  → a clickable avatar (like most apps) opening a dropdown with
   *                  name + role + « Mon profil » (if onAvatar) + « Se déconnecter »
   *   - signed out → a "Se connecter" button (onLogin opens a dialog, else links to loginHref)
   */
  render(el, opts = {}) {
    if (!el) return;
    const { profile, email, role, roleLabel, onLogout, onAvatar, onLogin, loginHref } = opts;
    const signedIn = !!(profile || email);
    if (!signedIn) {
      el.className = "navuser";
      if (onLogin) {
        el.innerHTML = I18n.switcherHTML() + `<button class="navlogin">👤 <span data-i18n="nav.login">${esc(I18n.t("nav.login"))}</span></button>`;
        el.querySelector(".navlogin").addEventListener("click", onLogin);
      } else {
        el.innerHTML = I18n.switcherHTML() + `<a class="navlogin" href="${esc(loginHref || "editor.html")}">👤 <span data-i18n="nav.login">${esc(I18n.t("nav.login"))}</span></a>`;
      }
      I18n.bindSwitcher(el);
      return;
    }
    const name = (profile && profile.display_name) || email || "";
    const av = profile && profile.avatar_url;
    const initials = ((name || "?").trim().match(/\p{L}\p{N}*/gu) || ["?"])
      .slice(0, 2).map(s => s[0]).join("").toUpperCase() || "?";
    const face = (cls) => av
      ? `<span class="navavatar ${cls}"><img src="${esc(av)}" alt=""></span>`
      : `<span class="navavatar navavatar-ph ${cls}">${esc(initials)}</span>`;
    const label = roleLabel ? roleLabel(role) : role;
    const badge = label ? `<span class="rolebadge">${esc(label)}</span>` : "";
    el.className = "navuser signedin";
    el.innerHTML =
      I18n.switcherHTML() +
      `<button class="navtrigger" aria-haspopup="menu" aria-expanded="false" title="${esc(name)}">` +
        `${face("")}<span class="navcaret">▾</span>` +
      `</button>` +
      `<div class="navmenu" role="menu" hidden>` +
        `<div class="navmenu-head">${face("navavatar-lg")}` +
          `<div class="navmenu-id"><span class="navmenu-name">${esc(name)}</span>${badge}</div>` +
        `</div>` +
        (onAvatar ? `<button class="navmenu-item" role="menuitem" data-act="profile">👤 <span data-i18n="nav.profile">${esc(I18n.t("nav.profile"))}</span></button>` : "") +
        `<button class="navmenu-item navmenu-logout" role="menuitem" data-act="logout">⎋ <span data-i18n="nav.logout">${esc(I18n.t("nav.logout"))}</span></button>` +
      `</div>`;
    I18n.bindSwitcher(el);
    const trigger = el.querySelector(".navtrigger");
    const menu = el.querySelector(".navmenu");
    const setOpen = (open) => {
      menu.hidden = !open;
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
      el.classList.toggle("open", open);
      if (open) {
        const onDoc = (e) => { if (!el.contains(e.target)) { setOpen(false); document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); } };
        const onKey = (e) => { if (e.key === "Escape") { setOpen(false); document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); trigger.focus(); } };
        document.addEventListener("mousedown", onDoc);
        document.addEventListener("keydown", onKey);
      }
    };
    trigger.addEventListener("click", () => setOpen(menu.hidden));
    menu.addEventListener("click", (e) => {
      const item = e.target.closest(".navmenu-item"); if (!item) return;
      setOpen(false);
      if (item.dataset.act === "profile" && onAvatar) onAvatar();
      if (item.dataset.act === "logout" && onLogout) onLogout();
    });
  },
};

// ── Papers: editions in the DB (creator owns it, scoped editors) ────────────
function _rowToPaper(r) {
  return {
    issue: r.issue, name: r.name, tagline: r.tagline, plate: r.plate || "plate-fraktur",
    theme: r.theme || "classic", lang: r.lang || "fr",
    ear: Array.isArray(r.ear) ? r.ear : ["", "", ""],
    slogans: Array.isArray(r.slogans) ? r.slogans : [],
    emblemLeft: r.emblem_left || "", emblemRight: r.emblem_right || "",
    clan: r.clan || "", owner_id: r.owner_id,
    gridCols: r.grid_cols || 0,   // 0 = auto well column count (see columns.sql)
    purpose: r.purpose || "",     // kiosque "what's this paper about" (paper_purpose.sql)
    aiZone: !!r.ai_zone,          // true → AI chronicles get a separate sidebar (ai_zone.sql)
  };
}
const Papers = {
  /** Merged edition map: papers.js defaults overlaid by DB rows (DB wins). */
  async map() {
    const base = Object.assign({}, window.DAIHBI_PAPERS || {});
    if (!db) return base;
    try {
      const { data } = await db.from("papers").select("*");
      (data || []).forEach((r) => { base[r.issue] = _rowToPaper(r); });
    } catch (e) { /* fall back to papers.js */ }
    return base;
  },
  async list() {
    const { data, error } = await db.from("papers").select("*").order("created_at");
    if (error) throw error;
    return (data || []).map(_rowToPaper);
  },
  /** Issues the current user manages (owner or co-éditeur). */
  async myManaged() {
    const { data: { user } } = await db.auth.getUser();
    if (!user) return [];
    const { data } = await db.from("paper_editors").select("issue").eq("editor_id", user.id);
    return (data || []).map((x) => x.issue);
  },
  async create(p) {
    const { data: { user } } = await db.auth.getUser();
    const row = { issue: p.issue, name: p.name || "", tagline: p.tagline || "", plate: p.plate || "plate-fraktur",
      theme: p.theme || "classic", grid_cols: p.gridCols || 0, purpose: p.purpose || "", lang: p.lang || "fr", ai_zone: !!p.aiZone,
      ear: p.ear || ["", "", ""], slogans: p.slogans || [], emblem_left: p.emblemLeft || "",
      emblem_right: p.emblemRight || "", clan: p.clan || "", owner_id: user.id };
    const { data, error } = await db.from("papers").insert(row).select().single();
    if (error) throw error;
    return _rowToPaper(data);
  },
  async update(issue, f) {
    const m = { name:"name", tagline:"tagline", plate:"plate", theme:"theme", ear:"ear", slogans:"slogans",
      emblemLeft:"emblem_left", emblemRight:"emblem_right", clan:"clan", gridCols:"grid_cols",
      purpose:"purpose", lang:"lang", aiZone:"ai_zone" };
    const row = {}; Object.keys(f).forEach((k) => { if (m[k]) row[m[k]] = f[k]; });
    const { data, error } = await db.from("papers").update(row).eq("issue", issue).select().single();
    if (error) throw error;
    return _rowToPaper(data);
  },
  async remove(issue) { const { error } = await db.from("papers").delete().eq("issue", issue); if (error) throw error; },
  /** Re-announce an edition: bump its published placements so the kiosque (which
   *  ranks by the newest placement's updated_at) re-flags it "fresh" and floats
   *  it to the top. RLS: placements update = manages_issue (owner / co-éditeur). */
  async republish(issue) {
    const { error } = await db.from("placements")
      .update({ updated_at: new Date().toISOString() }).eq("issue", issue).eq("published", true);
    if (error) throw error;
  },
  async editors(issue) {
    const { data } = await db.from("paper_editors").select("editor_id").eq("issue", issue);
    return (data || []).map((x) => x.editor_id);
  },
  async addEditor(issue, editorId) { const { error } = await db.from("paper_editors").insert({ issue, editor_id: editorId }); if (error) throw error; },
  async removeEditor(issue, editorId) { const { error } = await db.from("paper_editors").delete().eq("issue", issue).eq("editor_id", editorId); if (error) throw error; },
};

// ── Revisions: prior versions of an article (history + rollback) ────────────
const Revisions = {
  async list(articleId) {
    if (!db || !articleId) return [];
    const { data, error } = await db.from("article_revisions").select("*")
      .eq("article_id", articleId).order("created_at", { ascending: false });
    if (error) throw error;
    return data || [];
  },
};

// ── Comments: reader "Courrier des lecteurs" (read anon, post = logged in) ───
const Comments = {
  async list(issue) {
    if (!db) return [];
    const { data, error } = await db.from("comments").select("*")
      .eq("issue", issue).order("created_at", { ascending: true });
    if (error) throw error;
    return data || [];
  },
  async add(issue, body, authorName) {
    if (!db) throw new Error("Supabase not configured.");
    const { data: { user } } = await db.auth.getUser();
    if (!user) throw new Error(I18n.t("comment.loginToComment"));
    const { data, error } = await db.from("comments")
      .insert({ issue, body, author_name: authorName || "", author_id: user.id })
      .select().single();
    if (error) throw error;
    return data;
  },
  async remove(id) {
    const { error } = await db.from("comments").delete().eq("id", id);
    if (error) throw error;
  },
  subscribe(issue, cb) {
    if (!db) return;
    db.channel("comments-" + issue)
      .on("postgres_changes", { event: "*", schema: "public", table: "comments" }, () => cb())
      .subscribe();
  },
};

// ── Portfolio: illustrators' shared image gallery ───────────────────────────
const Portfolio = {
  async list() {
    if (!db) return [];
    const { data, error } = await db.from("images").select("*").order("created_at", { ascending: false });
    if (error) throw error;
    return data || [];
  },
  async add({ url, caption, clan, uploader_name, mime, bytes, width, height }) {
    const { data: { user } } = await db.auth.getUser();
    const { data, error } = await db.from("images")
      .insert({ url, caption: caption || "", clan: clan || "", uploader_name: uploader_name || "", uploader_id: user.id,
                mime: mime || "", bytes: bytes || 0, width: width || 0, height: height || 0 })
      .select().single();
    if (error) throw error;
    return data;
  },
  async remove(id) {
    const { error } = await db.from("images").delete().eq("id", id);
    if (error) throw error;
  },
  /** Pending (unapproved) uploads — visible to moderators (image_moderation.sql). */
  async listPending() {
    if (!db) return [];
    const { data, error } = await db.from("images").select("*").eq("approved", false).order("created_at", { ascending: false });
    if (error) throw error;
    return data || [];
  },
  /** Moderator approves a pending image so the public can see it. */
  async approve(id) {
    const { error } = await db.from("images").update({ approved: true }).eq("id", id);
    if (error) throw error;
  },
};

// ── Ads: réclames (annonceur creates → editor approves → shown in paper) ─────
const Ads = {
  /** Approved ads targeting this edition (or 'all') — public. */
  async listApproved(issue) {
    if (!db) return [];
    const { data, error } = await db.from("ads").select("*")
      .eq("approved", true).in("issue", [issue, "all"]);
    if (error) throw error;
    return data || [];
  },
  /** The current advertiser's own ads. */
  async listMine() {
    if (!db) return [];
    const { data: { user } } = await db.auth.getUser();
    if (!user) return [];
    const { data, error } = await db.from("ads").select("*")
      .eq("advertiser_id", user.id).order("created_at", { ascending: false });
    if (error) throw error;
    return data || [];
  },
  /** All ads (editor moderation). */
  async listAll() {
    const { data, error } = await db.from("ads").select("*").order("created_at", { ascending: false });
    if (error) throw error;
    return data || [];
  },
  async create(fields) {
    const { data: { user } } = await db.auth.getUser();
    const row = { advertiser_id: user.id, issue: "all", lang: "fr", status: "draft", approved: false, ...fields };
    const { data, error } = await db.from("ads").insert(row).select().single();
    if (error) throw error;
    return data;
  },
  async update(id, fields) {
    const { data, error } = await db.from("ads").update(fields).eq("id", id).select().single();
    if (error) throw error;
    return data;
  },
  async remove(id) {
    const { error } = await db.from("ads").delete().eq("id", id);
    if (error) throw error;
  },
};

// ── Render helpers (shared by the paper page) ─────────────────────────────
const esc = (s) =>
  (s || "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

function md(text) {
  if (!text) return "";
  return text
    .split(/\n\s*\n/)
    .map((p) => {
      const h = esc(p.trim())
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.+?)\*/g, "<em>$1</em>")
        .replace(/\n/g, "<br>");
      return h ? `<p>${h}</p>` : "";
    })
    .join("");
}

// ── Auth-result modal ─────────────────────────────────────────────────────
// Self-injecting and page-agnostic: every page that loads daihbi.js gets it for
// free. Handles the *landing* of auth emails — which Supabase signals via the
// URL hash / auth events, not via our own code:
//   • expired or already-used magic / confirm links  (#error_code=otp_expired …)
//   • password-recovery links                         (PASSWORD_RECOVERY event)
// and exposes openForgot() so any login screen can offer a "mot de passe oublié".
const AuthModal = (function () {
  let injected = false, root = null;

  const CSS = `
  .dam-overlay{position:fixed;inset:0;z-index:9000;background:rgba(20,18,16,.82);
    display:flex;align-items:center;justify-content:center;padding:1.2rem;
    font-family:system-ui,sans-serif}
  .dam-card{position:relative;background:#211f1c;color:#f3ead6;border:1px solid #5a534a;
    border-radius:14px;max-width:460px;width:100%;padding:1.8rem 1.8rem 1.5rem;text-align:center}
  .dam-card h2{font-family:"Playfair Display",Georgia,serif;font-size:1.7rem;margin:.1rem 0 .55rem}
  .dam-card p{opacity:.9;line-height:1.5;margin:0 auto 1.1rem;max-width:40ch;font-size:.92rem}
  .dam-x{position:absolute;top:.7rem;right:.85rem;background:none;border:none;color:#bdb3a1;
    font-size:1.1rem;cursor:pointer;line-height:1}
  .dam-card input{width:100%;font:inherit;background:#2c2924;color:#f3ead6;border:1px solid #555;
    border-radius:8px;padding:.6rem .7rem;margin:.3rem 0}
  .dam-card .dam-btn{width:100%;font:inherit;font-weight:700;background:#7a1f1a;color:#fff;border:none;
    border-radius:8px;padding:.7rem;margin-top:.6rem;cursor:pointer}
  .dam-card .dam-btn:hover{filter:brightness(1.12)}
  .dam-card .dam-btn:disabled{opacity:.6;cursor:default}
  .dam-msg{min-height:1.2rem;margin-top:.7rem;font-size:.85rem}
  .dam-msg.ok{color:#9bd49b} .dam-msg.err{color:#e8b9b2}
  .dam-icon{font-size:2.1rem;margin-bottom:.2rem}
  .dam-tabs{display:flex;gap:.4rem;margin:.2rem 0 .5rem}
  .dam-tab{flex:1;font:inherit;background:#2c2924;color:#cdc4b2;border:1px solid #5a534a;
    border-radius:8px;padding:.5rem;cursor:pointer}
  .dam-tab.on{background:#7a1f1a;color:#fff;border-color:#7a1f1a}
  .dam-alt{font-size:.82rem;margin:.85rem 0 0}
  .dam-alt a{color:#e8b9b2}`;

  function inject() {
    if (injected) return;
    injected = true;
    const style = document.createElement("style");
    style.textContent = CSS;
    document.head.appendChild(style);
    root = document.createElement("div");
    root.className = "dam-overlay";
    root.style.display = "none";
    root.innerHTML =
      `<div class="dam-card" role="dialog" aria-modal="true">
         <button class="dam-x" aria-label="${esc(I18n.t("auth.close"))}">✕</button>
         <div class="dam-body"></div>
       </div>`;
    document.body.appendChild(root);
    root.querySelector(".dam-x").addEventListener("click", close);
    root.addEventListener("click", e => { if (e.target === root) close(); });
  }
  function open(html) { inject(); root.querySelector(".dam-body").innerHTML = html; root.style.display = "flex"; return root.querySelector(".dam-body"); }
  function close() { if (root) root.style.display = "none"; }

  // Drop the auth params from the URL so a refresh doesn't re-trigger the modal.
  function scrubUrl() {
    try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
  }
  const validEmail = v => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test((v || "").trim());

  // « Lien expiré » — offer to mail a fresh sign-in link.
  function openExpired(description) {
    const b = open(
      `<div class="dam-icon">⏳</div>
       <h2>${esc(I18n.t("auth.expiredTitle"))}</h2>
       <p>${esc(I18n.t("auth.expiredDesc"))}</p>
       <input type="email" id="dam-email" placeholder="${esc(I18n.t("auth.emailPh"))}" autocomplete="email">
       <button class="dam-btn" id="dam-go">${esc(I18n.t("auth.resend"))}</button>
       <div class="dam-msg" id="dam-msg"></div>`);
    const msg = b.querySelector("#dam-msg"), inp = b.querySelector("#dam-email"), btn = b.querySelector("#dam-go");
    inp.focus();
    btn.addEventListener("click", async () => {
      if (!validEmail(inp.value)) { msg.className = "dam-msg err"; msg.textContent = I18n.t("auth.invalidEmail"); return; }
      btn.disabled = true; msg.className = "dam-msg"; msg.textContent = I18n.t("auth.sending");
      try { await Auth.resendLink(inp.value.trim()); msg.className = "dam-msg ok"; msg.textContent = I18n.t("auth.newLinkSent"); }
      catch (e) { msg.className = "dam-msg err"; msg.textContent = e.message || I18n.t("err.sendFail"); btn.disabled = false; }
    });
  }

  // « Mot de passe oublié » — user-triggered, mails a reset link.
  function openForgot(prefill) {
    const b = open(
      `<div class="dam-icon">🔑</div>
       <h2>${esc(I18n.t("auth.forgotTitle"))}</h2>
       <p>${esc(I18n.t("auth.forgotDesc"))}</p>
       <input type="email" id="dam-email" placeholder="${esc(I18n.t("auth.emailPh"))}" autocomplete="email" value="${esc(prefill || "")}">
       <button class="dam-btn" id="dam-go">${esc(I18n.t("auth.sendLink"))}</button>
       <div class="dam-msg" id="dam-msg"></div>`);
    const msg = b.querySelector("#dam-msg"), inp = b.querySelector("#dam-email"), btn = b.querySelector("#dam-go");
    inp.focus();
    btn.addEventListener("click", async () => {
      if (!validEmail(inp.value)) { msg.className = "dam-msg err"; msg.textContent = I18n.t("auth.invalidEmail"); return; }
      btn.disabled = true; msg.className = "dam-msg"; msg.textContent = I18n.t("auth.sending");
      try {
        await Auth.resetPassword(inp.value.trim());
        msg.className = "dam-msg ok";
        msg.innerHTML = esc(I18n.t("auth.linkSent")) +
          `<br><span style="opacity:.85;font-size:.92em">${esc(I18n.t("auth.linkHint"))}</span>`;
      }
      catch (e) { msg.className = "dam-msg err"; msg.textContent = e.message || I18n.t("err.sendFail"); btn.disabled = false; }
    });
  }

  // « Nouveau mot de passe » — shown after landing from a recovery link.
  function openRecovery() {
    const b = open(
      `<div class="dam-icon">🔒</div>
       <h2>${esc(I18n.t("auth.recoveryTitle"))}</h2>
       <p>${esc(I18n.t("auth.recoveryDesc"))}</p>
       <input type="password" id="dam-pw"  placeholder="${esc(I18n.t("auth.newPwPh"))}" autocomplete="new-password">
       <input type="password" id="dam-pw2" placeholder="${esc(I18n.t("auth.confirmPwPh"))}" autocomplete="new-password">
       <button class="dam-btn" id="dam-go">${esc(I18n.t("auth.update"))}</button>
       <div class="dam-msg" id="dam-msg"></div>`);
    const msg = b.querySelector("#dam-msg"), pw = b.querySelector("#dam-pw"), pw2 = b.querySelector("#dam-pw2"), btn = b.querySelector("#dam-go");
    pw.focus();
    btn.addEventListener("click", async () => {
      if ((pw.value || "").length < 8) { msg.className = "dam-msg err"; msg.textContent = I18n.t("auth.min8"); return; }
      if (pw.value !== pw2.value)     { msg.className = "dam-msg err"; msg.textContent = I18n.t("auth.pwMismatch"); return; }
      btn.disabled = true; msg.className = "dam-msg"; msg.textContent = I18n.t("auth.updating");
      try {
        await Auth.updatePassword(pw.value);
        msg.className = "dam-msg ok"; msg.textContent = I18n.t("auth.pwUpdated");
        scrubUrl();
        setTimeout(close, 1400);
      } catch (e) { msg.className = "dam-msg err"; msg.textContent = e.message || I18n.t("auth.updateFail"); btn.disabled = false; }
    });
  }

  // « Se connecter / Créer un compte » — inline login, no page navigation.
  // opts: { onSuccess, mode:'signin'|'signup', prefill, meta }
  function openLogin(opts = {}) {
    let mode = opts.mode === "signup" ? "signup" : "signin";
    const onSuccess = opts.onSuccess || (() => location.reload());
    function paint() {
      const isSignup = mode === "signup";
      const b = open(
        `<div class="dam-icon">${isSignup ? "📝" : "🔑"}</div>
         <h2>${esc(isSignup ? I18n.t("auth.signup") : I18n.t("auth.signin"))}</h2>
         <div class="dam-tabs">
           <button class="dam-tab ${isSignup ? "" : "on"}" data-m="signin">${esc(I18n.t("auth.signin"))}</button>
           <button class="dam-tab ${isSignup ? "on" : ""}" data-m="signup">${esc(I18n.t("auth.signup"))}</button>
         </div>
         <input type="email" id="dam-email" placeholder="${esc(I18n.t("auth.emailPh"))}" autocomplete="email" value="${esc(opts.prefill || "")}">
         <input type="password" id="dam-pw" placeholder="${esc(I18n.t("auth.pwPh"))}" autocomplete="${isSignup ? "new-password" : "current-password"}">
         <button class="dam-btn" id="dam-go">${esc(isSignup ? I18n.t("auth.createMyAccount") : I18n.t("auth.signin"))}</button>
         <div class="dam-msg" id="dam-msg"></div>
         <p class="dam-alt">${isSignup ? esc(I18n.t("auth.haveAccount"))
           : `<a href="#" id="dam-magic">${esc(I18n.t("auth.magicLink"))}</a> · <a href="#" id="dam-forgot">${esc(I18n.t("auth.forgotQ"))}</a>`}</p>`);
      const msg = b.querySelector("#dam-msg"), email = b.querySelector("#dam-email"),
            pw = b.querySelector("#dam-pw"), go = b.querySelector("#dam-go");
      b.querySelectorAll(".dam-tab").forEach(t => t.addEventListener("click", () => { mode = t.dataset.m; paint(); }));
      email.focus();
      const submit = async () => {
        if (!validEmail(email.value)) { msg.className = "dam-msg err"; msg.textContent = I18n.t("auth.invalidEmail"); return; }
        if ((pw.value || "").length < 6) { msg.className = "dam-msg err"; msg.textContent = I18n.t("auth.pwTooShort"); return; }
        go.disabled = true; msg.className = "dam-msg"; msg.textContent = isSignup ? I18n.t("auth.creating") : I18n.t("auth.connecting");
        try {
          if (isSignup) {
            const data = await Auth.signUp(email.value.trim(), pw.value, opts.meta || {});
            if (data && data.session) { msg.className = "dam-msg ok"; msg.textContent = I18n.t("auth.accountCreated"); setTimeout(onSuccess, 700); }
            else { msg.className = "dam-msg ok"; msg.textContent = I18n.t("auth.accountCreatedConfirm"); go.disabled = false; }
          } else {
            await Auth.signInPassword(email.value.trim(), pw.value);
            msg.className = "dam-msg ok"; msg.textContent = I18n.t("auth.connected"); setTimeout(onSuccess, 500);
          }
        } catch (e) { msg.className = "dam-msg err"; msg.textContent = e.message || I18n.t("err.generic"); go.disabled = false; }
      };
      go.addEventListener("click", submit);
      [email, pw].forEach(i => i.addEventListener("keydown", e => { if (e.key === "Enter") submit(); }));
      const magic = b.querySelector("#dam-magic");
      if (magic) magic.addEventListener("click", async e => {
        e.preventDefault();
        if (!validEmail(email.value)) { msg.className = "dam-msg err"; msg.textContent = I18n.t("auth.enterEmailFirst"); return; }
        go.disabled = true; msg.className = "dam-msg"; msg.textContent = I18n.t("auth.sendingLink");
        try { await Auth.signIn(email.value.trim()); msg.className = "dam-msg ok"; msg.textContent = I18n.t("auth.linkSent"); }
        catch (err) { msg.className = "dam-msg err"; msg.textContent = err.message || I18n.t("err.generic"); go.disabled = false; }
      });
      const forgot = b.querySelector("#dam-forgot");
      if (forgot) forgot.addEventListener("click", e => { e.preventDefault(); openForgot(email.value.trim()); });
    }
    paint();
  }

  // Auto-react to whatever Supabase put in the URL / fired on this page.
  function init() {
    if (!db) return;
    // Recovery links funnel to editor.html (see Auth.resetPassword), which owns
    // the "new password" screen — so no global recovery modal is wired here.
    // Errors are left in the URL hash (no event) — e.g. #error_code=otp_expired.
    const h = new URLSearchParams((location.hash || "").replace(/^#/, ""));
    if (h.get("error") || h.get("error_code")) {
      const desc = (h.get("error_description") || "").replace(/\+/g, " ");
      scrubUrl();
      openExpired(desc);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();

  return { openLogin, openForgot, openExpired, openRecovery, close };
})();

// ── Styles: reusable visual skins (palette + fonts + photo) authored by
//    editors. Stored in the `styles` table — owner-scoped writes, public read so
//    anonymous readers can render a paper that uses a custom style. A paper
//    references one via papers.theme = "style:<id>"; built-in themes (themes.js)
//    keep bare keys. `def` is applied as inline CSS variables by paper.html.
function _rowToStyle(r) {
  return { id: r.id, name: r.name || "", def: r.def || {}, owner_id: r.owner_id };
}
const Styles = {
  key(id) { return "style:" + id; },                 // papers.theme value for a custom style
  isCustom(theme) { return typeof theme === "string" && theme.indexOf("style:") === 0; },
  idOf(theme) { return Styles.isCustom(theme) ? theme.slice(6) : null; },
  async list() {
    if (!db) return [];
    const { data, error } = await db.from("styles").select("*").order("created_at", { ascending: true });
    if (error) throw error;
    return (data || []).map(_rowToStyle);
  },
  async get(id) {
    if (!db) return null;
    const { data, error } = await db.from("styles").select("*").eq("id", id).maybeSingle();
    if (error) throw error;
    return data ? _rowToStyle(data) : null;
  },
  async create({ name, def }) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { data, error } = await db.from("styles").insert({ name, def: def || {} }).select().single();
    if (error) throw error;
    return _rowToStyle(data);
  },
  async update(id, patch) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { error } = await db.from("styles").update(patch).eq("id", id);
    if (error) throw error;
  },
  async remove(id) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { error } = await db.from("styles").delete().eq("id", id);
    if (error) throw error;
  },
};

// ── Regiments: a shared, user-extensible régiment/clan vocabulary. The base
//    list ships in papers.js (DAIHBI_CLANS); the `regiments` table holds the ones
//    contributors add. list() merges both (defaults first, deduped) so an added
//    régiment appears in every picker; add() is open to any signed-in user.
const Regiments = {
  defaults() { return (window.DAIHBI_CLANS || []).slice(); },
  async list() {
    const defaults = Regiments.defaults();
    if (!db) return defaults;
    try {
      const { data, error } = await db.from("regiments").select("name").order("created_at", { ascending: true });
      if (error) throw error;
      const seen = new Set(defaults.map(s => s.toLowerCase()));
      const extra = (data || []).map(r => r.name).filter(n => n && !seen.has(n.toLowerCase()));
      return defaults.concat(extra);
    } catch (e) { return defaults; }
  },
  async add(name) {
    name = (name || "").trim();
    if (!name) throw new Error("Nom de régiment vide.");
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { error } = await db.from("regiments").insert({ name });
    // a duplicate just means the régiment already exists — treat as success.
    if (error && !/duplicate|unique|23505/i.test(error.message || error.code || "")) throw error;
    return name;
  },
};

window.Daihbi = { db, ISSUE, configured: _configured, Auth, AuthModal, NavUser, Chronicles, Placements, AdPlacements, Media, Profiles, Comments, Portfolio, Ads, Papers, Revisions, Styles, Regiments, esc, md, I18n, Prefs, LANGS };
})();
