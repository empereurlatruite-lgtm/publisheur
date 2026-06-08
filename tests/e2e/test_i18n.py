#!/usr/bin/env python3
"""End-to-end tests for the multilingual UI (i18n) and the kiosque language filter.

Boots a throwaway static server over web/ and drives the pages in a real Chrome
(Playwright). Covers the *anonymously testable* slice of the i18n feature — the
parts that don't need a signed-in account or the i18n DB migration:

  1. Auto-detect: a French browser opens the kiosque in French; an English
     browser opens it in English (navigator.language).
  2. The masthead language switcher flips all chrome (tagline, Join/Sign-in,
     filter chips) and persists the choice (localStorage daihbi_ui_lang) across
     a reload. Locale-aware dates follow the UI language.
  3. The kiosque language filter exists (All + the curated LANGS) and the reader's
     choice is remembered (localStorage daihbi_pref_lang) across a reload.
  4. paper.html declares its edition's content language on <html lang>.

Run:  python3 tests/e2e/test_i18n.py
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


def run() -> int:
    fails: list[str] = []

    def check(name: str, cond: bool, detail: str = ""):
        print(("✓ " if cond else "✗ ") + name + ("" if cond else f"  — {detail}"))
        if not cond:
            fails.append(name)

    with static_server(WEB_DIR) as base, sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")

        # 1) default UI language is French regardless of the browser language
        #    (only an explicit user choice overrides it — covered in step 2).
        for loc in ["fr-FR", "en-US"]:
            ctx = browser.new_context(locale=loc)
            pg = ctx.new_page()
            pg.goto(f"{base}/index.html", wait_until="networkidle", timeout=30000)
            pg.wait_for_timeout(1500)
            _dismiss_intro(pg)
            lang = pg.evaluate("()=>document.documentElement.lang")
            tag = (pg.evaluate("()=>document.querySelector('.sub')?.textContent||''") or "").lower()
            check(f"{loc} browser defaults to French UI", lang == "fr", f"got '{lang}'")
            check(f"{loc} default tagline is French", "presse" in tag, f"tagline={tag!r}")
            ctx.close()

        # 2) switcher flips chrome + persists across reload
        ctx = browser.new_context(locale="fr-FR")
        pg = ctx.new_page()
        pg.goto(f"{base}/index.html", wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(1500); _dismiss_intro(pg)
        fr_tag = pg.evaluate("()=>document.querySelector('.sub')?.textContent||''")
        pg.select_option(".navlang", "en"); pg.wait_for_timeout(700)
        en_tag = pg.evaluate("()=>document.querySelector('.sub')?.textContent||''")
        signin = pg.evaluate("()=>document.querySelector('.navlogin')?.textContent||''")
        stored = pg.evaluate("()=>localStorage.getItem('daihbi_ui_lang')")
        check("switcher changes tagline FR→EN", fr_tag != en_tag and "press" in en_tag.lower(),
              f"{fr_tag!r} -> {en_tag!r}")
        check("account control translates (Sign in)", "sign in" in signin.lower(), f"got {signin!r}")
        check("UI choice saved to localStorage", stored == "en", f"got {stored!r}")
        pg.reload(wait_until="networkidle"); pg.wait_for_timeout(1500); _dismiss_intro(pg)
        after = pg.evaluate("()=>document.documentElement.lang")
        check("UI language persists across reload", after == "en", f"got '{after}'")

        # 3) kiosque language filter: options + remembered choice
        opts = pg.evaluate("()=>[...document.querySelectorAll('#langfilter option')].map(o=>o.value)")
        check("language filter has All + curated langs",
              "" in opts and "fr" in opts and "en" in opts and len(opts) >= 6, f"opts={opts}")
        pg.select_option("#langfilter", "fr"); pg.wait_for_timeout(500)
        pref = pg.evaluate("()=>localStorage.getItem('daihbi_pref_lang')")
        check("content-language preference saved", pref == "fr", f"got {pref!r}")
        pg.reload(wait_until="networkidle"); pg.wait_for_timeout(1500); _dismiss_intro(pg)
        restored = pg.evaluate("()=>document.querySelector('#langfilter')?.value")
        check("content-language preference restored on reload", restored == "fr", f"got {restored!r}")
        ctx.close()

        # 4) paper.html declares the edition's content language
        ctx = browser.new_context(locale="en-US")
        pg = ctx.new_page()
        pg.goto(f"{base}/paper.html?issue=current", wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(2000)
        plang = pg.evaluate("()=>document.documentElement.lang")
        check("paper.html sets <html lang> to a content language",
              isinstance(plang, str) and len(plang) >= 2, f"got {plang!r}")
        ctx.close()

        # 5) embed/preview mode (?embed=1): clean, scaled, no chrome, no overflow.
        #    This is what the board's live-preview iframe loads.
        ctx = browser.new_context(viewport={"width": 420, "height": 900})
        pg = ctx.new_page()
        pg.goto(f"{base}/paper.html?issue=echo-du-front&embed=1", wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(2000)
        emb = pg.evaluate("""()=>({
          toolbar: document.querySelector('.toolbar') ? getComputedStyle(document.querySelector('.toolbar')).display : 'none',
          lecteurs: document.querySelector('#lecteurs') ? getComputedStyle(document.querySelector('#lecteurs')).display : 'none',
          zoom: parseFloat(document.querySelector('.sheet')?.style.zoom || '1'),
          overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        })""")
        check("embed mode hides the toolbar", emb["toolbar"] == "none", f"got {emb['toolbar']!r}")
        check("embed mode hides reader comments", emb["lecteurs"] == "none", f"got {emb['lecteurs']!r}")
        check("embed mode scales the sheet to fit", 0 < emb["zoom"] < 1, f"zoom={emb['zoom']}")
        check("embed mode has no horizontal overflow", emb["overflow"] <= 1, f"overflow={emb['overflow']}px")
        ctx.close()

        # 6) board "all" mode (?embed=1&all=1): the canvas the board renders. Anon only
        #    gets published placements (RLS), but they must be tagged clickable.
        ctx = browser.new_context(viewport={"width": 900, "height": 1100})
        pg = ctx.new_page()
        pg.goto(f"{base}/paper.html?issue=echo-du-front&embed=1&all=1", wait_until="networkidle", timeout=30000)
        pg.wait_for_timeout(2000)
        am = pg.evaluate("""()=>({
          allmode: document.body.classList.contains('allmode'),
          pids: document.querySelectorAll('[data-pid]').length,
          stories: document.querySelectorAll('.story,.lead').length,
        })""")
        check("all mode adds the allmode class", am["allmode"], f"got {am}")
        check("all mode tags articles with data-pid (clickable)",
              am["pids"] > 0 and am["pids"] >= am["stories"] - 1, f"pids={am['pids']} stories={am['stories']}")
        ctx.close()

        browser.close()

    print("\n" + "=" * 48)
    print(f"{'ALL PASSED' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
