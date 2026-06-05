// ── Publisheur — Supabase connection ───────────────────────────────────
// Fill these in from your Supabase dashboard: Settings → API.
// These two values are SAFE to commit / ship to the browser (the anon key is
// public by design; Row Level Security in schema.sql is what protects data).
window.DAIHBI_CONFIG = {
  SUPABASE_URL: "https://YOUR-PROJECT-ref.supabase.co",
  SUPABASE_ANON_KEY: "YOUR-ANON-PUBLIC-KEY",

  // Which edition the editor reads/writes. Bump this to start a new issue.
  ISSUE: "current",
};
