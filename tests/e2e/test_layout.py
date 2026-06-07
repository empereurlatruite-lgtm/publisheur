#!/usr/bin/env python3
"""End-to-end layout test for the rendered paper (web/paper.html).

Boots a throwaway static server over web/, drives the page in a real Chrome via
Playwright, and asserts the *layout invariants* the mise-en-page is built on —
not the seed content, which changes. See web/paper.html (renderLead/renderStory)
and Placements.publishedForIssue in web/daihbi.js for the rules under test.

Layout invariants asserted per published edition:
  1. The sheet finishes loading (never stuck on "Loading the press…").
  2. No data-layer error state ("Could not load articles." / "Not connected").
  3. No uncaught JS console errors, and no 4xx/5xx requests (favicon excepted).
  4. When the edition has chronicles: exactly one .lead, with a non-empty <h2>.
  5. Chronicle stories carry a valid weight class (major | minor | brief) and
     appear in non-decreasing weight rank (lead→major→minor→brief), then by
     position — i.e. the published-order contract holds in the DOM.
  6. Every <img> the layout renders actually loads (no broken photos).
  7. When the edition is empty, the empty-state ("Aucun article publié.") shows
     instead of a half-rendered or stuck sheet.

The page pulls live from Supabase (config.js anon key), so this is a true e2e.

Run:  python3 tests/e2e/test_layout.py
      python3 tests/e2e/test_layout.py --issues current,echo-du-front --headed
Exit code 0 = all editions pass, 1 = at least one failure.
"""
from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import socket
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

# web/ is two levels up from this file (tests/e2e/ -> repo root -> web/).
WEB_DIR = Path(__file__).resolve().parents[2] / "web"
DEFAULT_ISSUES = ["current", "horizon-bleu", "echo-du-front"]

# Order the editor lays out in; mirrors WRANK in web/daihbi.js. Chronicle stories
# rendered into the well are <article class="story {weight}"> (ads are .adbox).
WRANK = {"lead": 0, "major": 1, "minor": 2, "brief": 3}
VALID_STORY_WEIGHTS = {"major", "minor", "brief"}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def static_server(directory: Path):
    """Serve `directory` on an ephemeral localhost port for the test's lifetime."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=str(directory)
    )
    # Quiet the per-request logging.
    handler.log_message = lambda *a, **k: None  # type: ignore[assignment]
    port = _free_port()
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()


# DOM snapshot pulled in one round-trip; mirrors the structure paper.html builds.
_PROBE_JS = """
() => {
  const sheet = document.querySelector('#sheet');
  const story = [...document.querySelectorAll('.story:not(.adbox)')];
  const weightOf = el =>
    ['lead','major','minor','brief'].find(w => el.classList.contains(w)) || null;
  const imgs = [...document.querySelectorAll('#sheet img')];
  return {
    loading: /Loading the press/i.test(sheet ? sheet.textContent : ''),
    emptyMsg: document.querySelector('#sheet .empty')?.textContent?.trim() || null,
    leadCount: document.querySelectorAll('.lead').length,
    leadHeadline: document.querySelector('.lead h2')?.textContent?.trim() || '',
    storyWeights: story.map(weightOf),
    brokenImgs: imgs
      .filter(i => i.getAttribute('src') && !i.complete || (i.complete && i.naturalWidth === 0))
      .map(i => i.getAttribute('src')),
    imgCount: imgs.length,
    // masonry "snap": the well is a CSS grid and every story card has a
    // JS-applied row-span (packWell). columnSpread = how unevenly the columns
    // end (0 = perfectly level); should be small relative to the tallest card.
    well: (() => {
      const w = document.querySelector('.well');
      if (!w) return null;
      const cards = [...w.children].filter(el => el.classList.contains('story'));
      const bottoms = {};   // grid column index -> lowest card bottom
      let tallest = 0;
      for (const el of cards) {
        const r = el.getBoundingClientRect();
        tallest = Math.max(tallest, r.height);
        const col = Math.round(el.getBoundingClientRect().left);
        bottoms[col] = Math.max(bottoms[col] || 0, r.bottom);
      }
      const bs = Object.values(bottoms);
      return {
        display: getComputedStyle(w).display,
        cards: cards.length,
        spanned: cards.filter(el => /\\bspan\\b/.test(el.style.gridRowEnd)).length,
        columnSpread: bs.length ? Math.max(...bs) - Math.min(...bs) : 0,
        tallest: Math.round(tallest),
      };
    })(),
  };
}
"""


def check_issue(page, base_url: str, issue: str) -> list[str]:
    """Load one edition and return a list of invariant-violation messages."""
    console_errors: list[str] = []
    bad_responses: list[str] = []

    def on_console(m):
        # JS errors only; HTTP failures ("Failed to load resource…") are caught
        # by the response handler below, which excepts favicon noise.
        if m.type == "error" and "Failed to load resource" not in m.text:
            console_errors.append(m.text)

    page.on("console", on_console)
    page.on(
        "response",
        lambda r: bad_responses.append(f"{r.status} {r.url}")
        if r.status >= 400 and "favicon" not in r.url
        else None,
    )

    page.goto(
        f"{base_url}/paper.html?issue={issue}",
        wait_until="networkidle",
        timeout=30000,
    )
    # paper.html renders after its async Supabase fetches resolve; give the
    # post-networkidle render + image loads a moment to settle.
    page.wait_for_timeout(1500)
    s = page.evaluate(_PROBE_JS)

    fails: list[str] = []
    if s["loading"]:
        fails.append("sheet stuck on 'Loading the press…' (render never completed)")
    if s["emptyMsg"] and "Aucun article publié" not in s["emptyMsg"]:
        fails.append(f"data-layer error state: {s['emptyMsg']!r}")
    if console_errors:
        fails.append("console errors: " + "; ".join(console_errors[:5]))
    if bad_responses:
        fails.append("failed requests: " + "; ".join(bad_responses[:5]))

    has_articles = s["leadCount"] > 0 or len(s["storyWeights"]) > 0
    if not has_articles:
        # Empty edition: the empty-state must be shown, nothing half-rendered.
        if not (s["emptyMsg"] and "Aucun article publié" in s["emptyMsg"]):
            fails.append("no articles but empty-state 'Aucun article publié.' missing")
        return fails

    # --- layout invariants for a populated edition -----------------------------
    if s["leadCount"] != 1:
        fails.append(f"expected exactly 1 .lead, found {s['leadCount']}")
    if s["leadCount"] == 1 and not s["leadHeadline"]:
        fails.append("lead has an empty <h2> headline")

    weights = s["storyWeights"]
    if None in weights:
        fails.append("a .story is missing a weight class")
    bad = [w for w in weights if w and w not in VALID_STORY_WEIGHTS]
    if bad:
        fails.append(f"invalid story weight class(es): {bad}")

    ranks = [WRANK[w] for w in weights if w in WRANK]
    if ranks != sorted(ranks):
        fails.append(
            f"stories not in weight order (lead→major→minor→brief): {weights}"
        )

    if s["brokenImgs"]:
        fails.append(
            f"{len(s['brokenImgs'])} broken image(s): {s['brokenImgs'][:3]}"
        )

    # masonry "snap": the well must be a packed CSS grid (cards span rows so they
    # snap together), and with several cards the columns should end roughly level.
    w = s["well"]
    if w and w["cards"] > 0:
        if w["display"] != "grid":
            fails.append(f".well is not a CSS grid (display={w['display']!r})")
        if w["spanned"] != w["cards"]:
            fails.append(f"masonry packing not applied: {w['spanned']}/{w['cards']} cards have a row-span")
        # columns should snap level — uneven bottoms under one card height are fine
        if w["cards"] >= 4 and w["columnSpread"] > max(w["tallest"], 1):
            fails.append(
                f"columns not snapping level: spread={w['columnSpread']}px > tallest card {w['tallest']}px"
            )

    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--issues",
        default=",".join(DEFAULT_ISSUES),
        help="comma-separated edition slugs (default: the three seed editions)",
    )
    ap.add_argument(
        "--headed", action="store_true", help="run Chrome headed (for debugging)"
    )
    args = ap.parse_args()
    issues = [i.strip() for i in args.issues.split(",") if i.strip()]

    if not WEB_DIR.is_dir():
        print(f"web/ not found at {WEB_DIR}", file=sys.stderr)
        return 1

    shots_dir = Path(__file__).resolve().parent / "_failures"
    results: dict[str, list[str]] = {}

    with static_server(WEB_DIR) as base_url, sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=not args.headed)
        for issue in issues:
            page = browser.new_page(viewport={"width": 1200, "height": 1600})
            try:
                fails = check_issue(page, base_url, issue)
            except Exception as e:  # a thrown error is itself a failure
                fails = [f"exception during check: {e!r}"]
            results[issue] = fails
            if fails:  # keep a screenshot to debug the failing layout
                shots_dir.mkdir(exist_ok=True)
                shot = shots_dir / f"{issue}.png"
                with contextlib.suppress(Exception):
                    page.screenshot(path=str(shot), full_page=True)
            page.close()
        browser.close()

    print("\nLayout e2e — paper.html")
    print("=" * 48)
    failed = 0
    for issue in issues:
        fails = results[issue]
        if fails:
            failed += 1
            print(f"✗ {issue}")
            for f in fails:
                print(f"    - {f}")
            print(f"    screenshot: {shots_dir / (issue + '.png')}")
        else:
            print(f"✓ {issue}")
    print("=" * 48)
    print(f"{len(issues) - failed}/{len(issues)} editions passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
