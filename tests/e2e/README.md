# E2E tests

End-to-end tests that drive the real pages in a headless Chrome (Playwright,
Python) against **live Supabase** seed data.

## Requirements
- `google-chrome` on PATH (the tests use `channel="chrome"` — no Playwright
  browser download needed).
- Python `playwright` package (`pip install --user playwright`).

## `test_layout.py` — paper layout invariants
Boots a throwaway static server over `web/`, opens `paper.html?issue=…` for each
seed edition, and asserts the mise-en-page rules (not the seed content):

- the sheet finishes loading and shows no data-layer error state;
- no JS console errors and no 4xx/5xx requests (favicon excepted);
- exactly one `.lead` with a non-empty headline when the edition has chronicles;
- chronicle stories carry a valid weight class and appear in published order
  (lead→major→minor→brief, then by position) — the `WRANK` contract from
  `web/daihbi.js`;
- every rendered `<img>` actually loads (no broken photos);
- an empty edition shows the "Aucun article publié." empty-state.

```bash
python3 tests/e2e/test_layout.py                       # the three seed editions
python3 tests/e2e/test_layout.py --issues current      # a subset
python3 tests/e2e/test_layout.py --headed              # watch it run
```

Exit code `0` = all editions pass, `1` = at least one failure. On failure a
full-page screenshot of the offending edition is written to
`tests/e2e/_failures/<issue>.png`.

## `test_i18n.py` — multilingual UI + language filter
Drives the kiosque/paper to assert the i18n behaviour that needs no login or the
i18n DB migration: browser-language auto-detect (FR vs EN), the masthead language
switcher flipping all chrome and persisting (`localStorage daihbi_ui_lang`) across
reloads, locale-aware dates, the kiosque language filter (All + curated langs) with
a remembered reader preference (`localStorage daihbi_pref_lang`), `paper.html`
declaring its edition's content language on `<html lang>`, the board's
**preview embed mode** (`paper.html?embed=1`: toolbar + reader comments hidden,
the sheet scaled to fit with no horizontal overflow), and the board **canvas
mode** (`paper.html?embed=1&all=1`: `allmode` class + every article tagged with
`data-pid` so the board can open its edit panel on click).

```bash
python3 tests/e2e/test_i18n.py
```

Exit code `0` = all checks pass, `1` = at least one failed.

## `test_login.py` — sign-in surface
Drives the signed-out sign-in surface (no real account or Supabase round-trip):

- the kiosque masthead "Se connecter" control exists and is **actually
  clickable** — the full-width `<h1>` nameplate must not paint over it (or over
  "Rejoindre" / "Espace rédaction") and swallow the click. This is the
  regression guard for the z-index bug where the button "did nothing";
- clicking it opens the inline login modal with email + password + a submit
  button whose handler fires (invalid email → inline error, no navigation), a
  working sign-up tab, and a "Mot de passe oublié" link that swaps to the
  reset-request screen;
- `editor.html`, signed out, shows its login gate with email + password inputs
  and a "Se connecter" submit button whose handler runs (empty → inline error).

```bash
python3 tests/e2e/test_login.py
```

Exit code `0` = all checks pass, `1` = at least one failed.
