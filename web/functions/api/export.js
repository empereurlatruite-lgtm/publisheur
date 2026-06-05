// Cloudflare Pages Function — POST /api/export
// Triggered by an editor in the newsroom to render a print-grade PDF via the
// Scribus GitHub Action. Verifies the caller is a logged-in editor (Supabase
// JWT), then dispatches the `publish.yml` workflow for the given issue.
//
// Required Pages secret:  GITHUB_TOKEN  (fine-grained PAT, repo Actions: read+write)
// (SUPABASE_URL / anon key and GH_REPO are public and inlined below; override
//  via Pages env vars of the same name if you fork.)

const SUPABASE_URL  = "https://atnmzlaiglmkykzryjar.supabase.co";
const SUPABASE_ANON = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF0bm16bGFpZ2xta3lrenJ5amFyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2MTYwNjUsImV4cCI6MjA5NjE5MjA2NX0.Zw07rk3ey-UhZG_Y6-mb1IKYU-gRUIF-E-fCpXr5oW0";
const GH_REPO = "empereurlatruite-lgtm/publisheur";

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status, headers: { "content-type": "application/json" },
  });
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const url  = env.SUPABASE_URL  || SUPABASE_URL;
  const anon = env.SUPABASE_ANON_KEY || SUPABASE_ANON;
  const repo = env.GH_REPO || GH_REPO;
  const token = env.GITHUB_TOKEN;
  if (!token) return json({ error: "Export non configuré (GITHUB_TOKEN manquant)." }, 500);

  let issue = "current";
  try { issue = (await request.json()).issue || "current"; } catch (_) {}
  issue = String(issue).toLowerCase().replace(/[^a-z0-9-]/g, "");
  if (!issue) return json({ error: "Édition invalide." }, 400);

  // 1) verify the caller's Supabase session
  const auth = request.headers.get("Authorization") || "";
  const jwt = auth.replace(/^Bearer\s+/i, "");
  if (!jwt) return json({ error: "Connectez-vous." }, 401);
  const ures = await fetch(`${url}/auth/v1/user`, { headers: { apikey: anon, Authorization: `Bearer ${jwt}` } });
  if (!ures.ok) return json({ error: "Session invalide." }, 401);
  const user = await ures.json();

  // 2) must be an editor
  const pres = await fetch(`${url}/rest/v1/profiles?id=eq.${user.id}&select=role`, {
    headers: { apikey: anon, Authorization: `Bearer ${jwt}` },
  });
  const profs = pres.ok ? await pres.json() : [];
  if (!profs[0] || profs[0].role !== "editor") return json({ error: "Réservé aux éditeurs." }, 403);

  // 3) dispatch the Scribus workflow
  const gh = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/publish.yml/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "publisheur-export",
      "content-type": "application/json",
    },
    body: JSON.stringify({ ref: "main", inputs: { issue } }),
  });
  if (!(gh.status === 204 || gh.ok)) {
    const t = await gh.text();
    return json({ error: `Échec du déclenchement (${gh.status}). ${t.slice(0, 160)}` }, 502);
  }
  return json({ ok: true, issue, pdf: `${url}/storage/v1/object/public/media/exports/${issue}.pdf` });
}
