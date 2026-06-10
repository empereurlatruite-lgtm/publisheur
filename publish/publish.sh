#!/usr/bin/env bash
# ── Publisheur — one-command publish ───────────────────────────────────
# Gathers articles → lays them out in Scribus → exports PDF + page images.
#
#   ./publish.sh                # issue "current"
#   ./publish.sh special-1      # a named issue
#
# Needs: python3, scribus, poppler-utils (pdftoppm), xvfb.
# Supabase: set SUPABASE_URL + SUPABASE_KEY in the environment to pull from
# the cloud; otherwise it uses the local articles.db + war-wire.
set -euo pipefail
cd "$(dirname "$0")"

ISSUE="${1:-current}"
OUT="out"
mkdir -p "$OUT"

# Register the bundled web fonts (Playfair Display / PT Serif / Old Standard TT)
# so Scribus renders the print edition with the same type as paper.html. No-op
# if already installed; harmless without them (layout.py falls back to Liberation).
if [ -d fonts ]; then
  mkdir -p "$HOME/.fonts/publisheur"
  cp -f fonts/*.ttf "$HOME/.fonts/publisheur/" 2>/dev/null || true
  fc-cache -f "$HOME/.fonts" >/dev/null 2>&1 || true
fi

echo "▶ 1/3  Gathering articles (issue: $ISSUE) …"
python3 build_issue.py --issue "$ISSUE" --out "$OUT/issue.json"

echo "▶ 2/3  Laying out in Scribus …"
DAIHBI_ISSUE="$PWD/$OUT/issue.json" \
DAIHBI_OUTPDF="$PWD/$OUT/issue.pdf" \
DAIHBI_OUTSLA="$PWD/$OUT/issue.sla" \
  xvfb-run -a scribus -g -ns -py layout.py

echo "▶ 3/3  Rendering page images …"
rm -f "$OUT"/page-*.png
pdftoppm -png -r 150 "$OUT/issue.pdf" "$OUT/page"

echo "✓ Published:"
ls -1 "$OUT"/issue.pdf "$OUT"/page-*.png
