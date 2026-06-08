#!/usr/bin/env python3
"""End-to-end tests for the sign-in surface.

Boots a throwaway static server over web/ and drives the pages in a real Chrome
(Playwright). Covers the *anonymously testable* slice of login — the parts that
need no real account or network round-trip to Supabase:

  1. The kiosque masthead "Se connecter" button is actually clickable — i.e. the
     full-width <h1> nameplate does NOT paint over it and swallow the click
     (regression for the z-index bug where the button "did nothing"). The same
     guard covers the "Rejoindre" and "Espace rédaction" controls beside it.
  2. Clicking it opens the inline login modal (AuthModal), which exposes the
     email + password fields, a working submit button (client-side validation
     fires — proving the handler is wired), a sign-up tab, and the
     "Mot de passe oublié" link that swaps to the reset-request screen.
  3. editor.html, signed out, shows its login gate with email + password inputs
     and a "Se connecter" button whose handler runs (empty-field validation).

None of these submit valid credentials, so no Supabase account is needed.

Run:  python3 tests/e2e/test_login.py
Exit 0 = all checks pass, 1 = at least one failed.
"""
from __future__ import annotations

import contextlib
import functools
import http.server
import socket
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

WEB_DIR = Path(__file__).resolve().parents[2] / "web"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def static_server(directory: Path):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    handler.log_message = lambda *a, **k: None  # type: ignore[assignment]
    port = _free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown(); httpd.server_close()


def _dismiss_intro(page):
    with contextlib.suppress(Exception):
        page.click(".introx", timeout=1500)


# True when the element actually sitting at the centre of `selector` is that
# element (or a descendant of it) — i.e. nothing is painted on top intercepting
# clicks. This is what catches the masthead overlap regression.
_UNCOVERED = """(sel)=>{
  const el = document.querySelector(sel);
  if(!el) return false;
  const r = el.getBoundingClientRect();
  const hit = document.elementFromPoint(r.left + r.width/2, r.top + r.height/2);
  return !!hit && (hit === el || el.contains(hit) || hit.contains(el));
}"""


def run() -> int:
    fails: list[str] = []

    def check(name: str, cond: bool, detail: str = ""):
        print(("✓ " if cond else "✗ ") + name + ("" if cond else f"  — {detail}"))
        if not cond:
            fails.append(name)

    with static_server(WEB_DIR) as base, sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")

        # ── Kiosque masthead, signed out ────────────────────────────────────
        ctx = browser.new_context(locale="fr-FR")
        pg = ctx.new_page()
        pg.goto(f"{base}/index.html", wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(1500); _dismiss_intro(pg)

        login = pg.query_selector(".navlogin")
        check("masthead shows a 'Se connecter' control when signed out",
              bool(login) and "connecter" in (login.inner_text().lower() if login else ""),
              f"text={login.inner_text() if login else None!r}")

        # The bug: the <h1> nameplate overlapped these and ate the clicks.
        check("'Se connecter' is not covered by the nameplate",
              pg.evaluate(_UNCOVERED, ".navlogin"))
        check("'Rejoindre' is not covered by the nameplate",
              pg.evaluate(_UNCOVERED, "#joinBtn"))
        check("'Espace rédaction' is not covered by the nameplate",
              pg.evaluate(_UNCOVERED, "#redacLink"))

        # Clicking it must open the modal (would silently fail if covered).
        pg.click(".navlogin"); pg.wait_for_timeout(600)
        overlay_disp = pg.evaluate(
            "()=>{const o=document.querySelector('.dam-overlay');return o?getComputedStyle(o).display:'none'}")
        check("clicking 'Se connecter' opens the login modal", overlay_disp == "flex",
              f"overlay display={overlay_disp!r}")
        check("login modal has email, password and a submit button",
              bool(pg.query_selector("#dam-email")) and bool(pg.query_selector("#dam-pw"))
              and bool(pg.query_selector("#dam-go")))

        # The submit handler is wired: empty/invalid input → inline error, no nav.
        pg.fill("#dam-email", "not-an-email")
        pg.click("#dam-go"); pg.wait_for_timeout(300)
        msg_cls = pg.evaluate("()=>document.querySelector('#dam-msg')?.className||''")
        check("submit button runs validation (invalid email → error)", "err" in msg_cls,
              f"msg class={msg_cls!r}")

        # Sign-up tab toggles to the create-account form.
        pg.click(".dam-tab[data-m='signup']"); pg.wait_for_timeout(300)
        signup_on = pg.evaluate(
            "()=>document.querySelector(\".dam-tab[data-m='signup']\")?.classList.contains('on')")
        check("can switch to the 'Créer un compte' tab", bool(signup_on))

        # Forgot-password link swaps to the reset-request screen.
        pg.click(".dam-tab[data-m='signin']"); pg.wait_for_timeout(200)
        pg.click("#dam-forgot"); pg.wait_for_timeout(300)
        forgot_h2 = pg.evaluate("()=>document.querySelector('.dam-card h2')?.textContent||''")
        check("'Mot de passe oublié' opens the reset-request screen",
              "oubli" in forgot_h2.lower() or "forgot" in forgot_h2.lower(),
              f"heading={forgot_h2!r}")
        ctx.close()

        # ── editor.html login gate, signed out ──────────────────────────────
        ctx = browser.new_context(locale="fr-FR")
        pg = ctx.new_page()
        pg.goto(f"{base}/editor.html", wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(2500)
        gate_disp = pg.evaluate("()=>document.querySelector('#gate')?.style.display")
        has_inputs = pg.evaluate(
            "()=>!!document.querySelector('#gateCard #email') && !!document.querySelector('#gateCard #password')")
        # The gate has two "Se connecter" buttons — the sign-in *tab* and the
        # actual *submit*. Target the submit by its handler, not its text.
        submit_sel = "#gateCard button[onclick*='doPasswordLogin']"
        signin_btn = pg.evaluate(
            "(s)=>{const b=document.querySelector(s);return b?b.textContent.trim():null}", submit_sel)
        check("editor.html shows the login gate when signed out", gate_disp == "flex",
              f"gate display={gate_disp!r}")
        check("editor login gate has email + password inputs", bool(has_inputs))
        check("editor login gate has a 'Se connecter' submit button", bool(signin_btn),
              f"button={signin_btn!r}")

        # The submit button's handler runs (empty fields → inline error).
        if has_inputs and signin_btn:
            pg.click(submit_sel); pg.wait_for_timeout(300)
            err = pg.evaluate("()=>document.querySelector('#loginErr')?.textContent||''")
            check("editor 'Se connecter' runs validation (empty → error)", bool(err.strip()),
                  f"err={err!r}")
        ctx.close()

        browser.close()

    print("\n" + "=" * 48)
    print(f"{'ALL PASSED' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
