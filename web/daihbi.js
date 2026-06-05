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
  async signUp(email, password, meta) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    const { data, error } = await db.auth.signUp({
      email, password,
      options: { emailRedirectTo: location.href.split("#")[0], data: meta || {} },
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

// ── Media: upload images (article photos, avatars) to public Storage ────────
const Media = {
  /** Upload an image File into <folder>/, return its public URL. */
  async upload(file, folder) {
    if (!db) throw new Error("Supabase not configured (edit web/config.js).");
    if (!file.type || !file.type.startsWith("image/"))
      throw new Error("Ce fichier n'est pas une image.");
    if (file.size > 10 * 1024 * 1024)
      throw new Error("Image trop lourde (max 10 Mo).");
    const ext = (file.name.split(".").pop() || "jpg").toLowerCase().replace(/[^a-z0-9]/g, "") || "jpg";
    const path = `${folder || ISSUE}/${Date.now()}-${Math.random().toString(36).slice(2, 8)}.${ext}`;
    const { error } = await db.storage.from("media").upload(path, file, {
      cacheControl: "31536000", upsert: false, contentType: file.type,
    });
    if (error) throw error;
    return db.storage.from("media").getPublicUrl(path).data.publicUrl;
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
    if (!user) throw new Error("Connectez-vous pour commenter.");
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
  async add({ url, caption, clan, uploader_name }) {
    const { data: { user } } = await db.auth.getUser();
    const { data, error } = await db.from("images")
      .insert({ url, caption: caption || "", clan: clan || "", uploader_name: uploader_name || "", uploader_id: user.id })
      .select().single();
    if (error) throw error;
    return data;
  },
  async remove(id) {
    const { error } = await db.from("images").delete().eq("id", id);
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

window.Daihbi = { db, ISSUE, configured: _configured, Auth, Articles, Media, Profiles, Comments, Portfolio, sortArticles, esc, md };
})();
