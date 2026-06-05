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

function sortArticles(rows) {
  return [...rows].sort(
    (a, b) =>
      (WRANK[a.weight] ?? 9) - (WRANK[b.weight] ?? 9) ||
      (a.position || 0) - (b.position || 0) ||
      String(a.created_at).localeCompare(String(b.created_at))
  );
}

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
      options: { emailRedirectTo: location.href.split("#")[0] },
    });
    if (error) throw error;
  },
  async signInPassword(email, password) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { error } = await db.auth.signInWithPassword({ email, password });
    if (error) throw error;
  },
  async signUp(email, password) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { data, error } = await db.auth.signUp({
      email, password,
      options: { emailRedirectTo: location.href.split("#")[0] },
    });
    if (error) throw error;
    return data; // data.session is non-null when email auto-confirm is on
  },
  async signOut() {
    if (db) await db.auth.signOut();
  },
  onChange(cb) {
    if (db) db.auth.onAuthStateChange((_e, session) => cb(session));
  },
};

// ── Articles ──────────────────────────────────────────────────────────────
const Articles = {
  /** All articles in the current issue (editor view: includes drafts). */
  async listAll() {
    if (!db) return [];
    const { data, error } = await db
      .from("articles")
      .select("*")
      .eq("issue", ISSUE);
    if (error) throw error;
    return sortArticles(data || []);
  },

  /** Published only (public paper). */
  async listPublished() {
    if (!db) return [];
    const { data, error } = await db
      .from("articles")
      .select("*")
      .eq("issue", ISSUE)
      .eq("published", true);
    if (error) throw error;
    return sortArticles(data || []);
  },

  async get(id) {
    const { data, error } = await db.from("articles").select("*").eq("id", id).single();
    if (error) throw error;
    return data;
  },

  async create(fields) {
    const { data: { user } } = await db.auth.getUser();
    const max = await this._maxPosition();
    const row = {
      issue: ISSUE,
      kicker: "", headline: "Untitled", subhead: "", byline: "",
      body: "", weight: "minor", image_url: "", published: true,
      position: max + 1,
      author_id: user?.id || null,
      ...fields,
    };
    const { data, error } = await db.from("articles").insert(row).select().single();
    if (error) throw error;
    return data;
  },

  async update(id, fields) {
    const { data, error } = await db.from("articles").update(fields).eq("id", id).select().single();
    if (error) throw error;
    return data;
  },

  async remove(id) {
    const { error } = await db.from("articles").delete().eq("id", id);
    if (error) throw error;
  },

  /** Swap position with the adjacent article in the same weight band. */
  async move(id, direction) {
    const all = await this.listAll();
    const me = all.find((a) => a.id === id);
    if (!me) return;
    const band = all.filter((a) => a.weight === me.weight);
    const i = band.findIndex((a) => a.id === id);
    const j = direction === "up" ? i - 1 : i + 1;
    if (j < 0 || j >= band.length) return;
    const other = band[j];
    await Promise.all([
      this.update(me.id, { position: other.position }),
      this.update(other.id, { position: me.position }),
    ]);
  },

  async _maxPosition() {
    const { data } = await db
      .from("articles")
      .select("position")
      .eq("issue", ISSUE)
      .order("position", { ascending: false })
      .limit(1);
    return data && data[0] ? data[0].position : 0;
  },

  /** Live updates: cb() fires whenever any article in this issue changes. */
  subscribe(cb) {
    if (!db) return;
    db.channel("articles-" + ISSUE)
      .on("postgres_changes",
          { event: "*", schema: "public", table: "articles" },
          () => cb())
      .subscribe();
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

window.Daihbi = { db, ISSUE, configured: _configured, Auth, Articles, sortArticles, esc, md };
})();
