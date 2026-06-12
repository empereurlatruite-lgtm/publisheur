#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""layout.py — Scribus Scripter script: lay out one issue and export PDF.

Run via the publisher (NOT directly):
    DAIHBI_ISSUE=out/issue.json DAIHBI_OUTPDF=out/issue.pdf \
        xvfb-run -a scribus -g -ns -py layout.py

Reads the normalized issue.json produced by build_issue.py and flows the
articles into a vintage A3 front page using linked, multi-column text frames
(true newspaper auto-flow). Exports a print-grade PDF.
"""

import json
import math
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import scribus


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "")

ISSUE = os.environ.get("DAIHBI_ISSUE", "out/issue.json")
OUTPDF = os.environ.get("DAIHBI_OUTPDF", "out/issue.pdf")
OUTSLA = os.environ.get("DAIHBI_OUTSLA", OUTPDF[:-4] + ".sla")

# ── Page geometry (mm) ──────────────────────────────────────────────────
PW, PH, M = 297.0, 420.0, 15.0
CX, CW = M, PW - 2 * M                # content x, width  (15 .. 282, width 267)
COLS, CGAP = 5, 5.0                   # well: 5 columns

# ── Fonts ───────────────────────────────────────────────────────────────
# Match the web edition's type (paper.html role vars): Playfair Display for
# heads/masthead, PT Serif for body, Old Standard TT for meta. Installed from
# Google Fonts (see publish/fonts/ + publish.yml); Liberation is the fallback
# if a face is missing so the layout never crashes.
def _font(preferred, fallback):
    try:
        return preferred if preferred in scribus.getFontNames() else fallback
    except Exception:
        return fallback

F_HEAD = _font("Playfair Display Black", "Liberation Serif Bold")
F_HEAD_IT = _font("Playfair Display Black Italic", "Liberation Serif Bold Italic")
F_BODY = _font("PT Serif Regular", "Liberation Serif Regular")
F_BODY_IT = _font("PT Serif Italic", "Liberation Serif Italic")
F_SANS = _font("Old Standard TT Bold", "Liberation Sans Bold")

# Per-edition masthead plate → nameplate face, mirroring paper.html's `.plate-*`
# rules: fraktur/columns (and the default) keep the Playfair masthead; anton and
# echo switch to a condensed sans. The preferred faces aren't bundled in
# publish/fonts/, so _font() falls back to Liberation Sans Bold — still a sans,
# which matches the web masthead far better than the serif Playfair would. This
# is why the print `plate` field is no longer silently dropped.
PLATE_HEAD = {
    "plate-anton": _font("Anton Regular", "Liberation Sans Bold"),
    "plate-echo":  _font("Oswald Bold", "Liberation Sans Bold"),
    "plate-expedition": _font("Cinzel Decorative", "Liberation Serif Bold"),
}
def plate_head_font(plate):
    return PLATE_HEAD.get((plate or "").lower(), F_HEAD)

ALIGN_L, ALIGN_C, ALIGN_R, ALIGN_BLOCK = 0, 1, 2, 3


def rgb_to_cmyk(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    k = 1 - max(r, g, b)
    if k >= 1:
        return 0, 0, 0, 255
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return int(c * 255), int(m * 255), int(y * 255), int(k * 255)


def defc(name, r, g, b):
    c, m, y, k = rgb_to_cmyk(r, g, b)
    scribus.defineColor(name, c, m, y, k)


def _hex(h):
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


# Per-edition theme palettes — mirror the `.sheet.theme-*` role variables in
# web/paper.html (--ink/--paper/--accent/--rule) so the print edition matches
# the web skin the rédacteur en chef picked. Fonts/masthead plate can't be
# matched (Scribus lacks the web fonts), so this is colour-accurate only.
THEME_PALETTES = {
    "classic":  {"ink": "#1a1714", "paper": "#f5efe1", "accent": "#7a1f1a", "rule": "#aa9c82"},
    "fujimoto": {"ink": "#2B2D31", "paper": "#EADFC9", "accent": "#C87A65", "rule": "#626D71"},
    "noir":     {"ink": "#0d0d0d", "paper": "#ffffff", "accent": "#c01818", "rule": "#0d0d0d"},
    "gazette":  {"ink": "#23303a", "paper": "#f3f5f7", "accent": "#2f6f8f", "rule": "#9fb0bb"},
    "brasil":   {"ink": "#173f1f", "paper": "#fbf7e6", "accent": "#009c3b", "rule": "#2e7d32"},
    "expedition": {"ink": "#e8dcc1", "paper": "#15110c", "accent": "#cca24c", "rule": "#7c6427"},
}


def define_theme(theme):
    """Define Ink/Paper/Accent/Hair from the edition's theme (classic fallback;
    custom `style:<id>` themes fall back to classic too)."""
    pal = THEME_PALETTES.get((theme or "classic").lower(), THEME_PALETTES["classic"])
    defc("Ink", *_hex(pal["ink"]))
    defc("Accent", *_hex(pal["accent"]))
    defc("Paper", *_hex(pal["paper"]))
    defc("Hair", *_hex(pal["rule"]))


# ── Style helpers ───────────────────────────────────────────────────────
def mkstyle(name, font, size, align, color="Ink", firstindent=0.0,
            gapbefore=0.0, gapafter=0.0, dropcap=0):
    cs = name + "_c"
    scribus.createCharStyle(name=cs, font=font, fontsize=size, fillcolor=color)
    scribus.createParagraphStyle(
        name=name,
        linespacingmode=1,                       # 1 = automatic (scales with font)
        alignment=align, firstindent=firstindent,
        gapbefore=gapbefore, gapafter=gapafter,
        hasdropcap=dropcap, dropcaplines=3, charstyle=cs)


def add(frame, text, style):
    """Append a paragraph to `frame` and apply paragraph style `style`."""
    if not text:
        text = " "
    start = scribus.getTextLength(frame)
    scribus.insertText(text + "\n", start, frame)
    scribus.selectText(start, len(text) + 1, frame)
    scribus.setParagraphStyle(style, frame)
    scribus.deselectAll()


def rule(x1, y, x2, width=0.4, color="Ink"):
    n = scribus.createLine(x1, y, x2, y)
    scribus.setLineWidth(width, n)
    scribus.setLineColor(color, n)
    return n


def double_rule(x1, y, x2):
    rule(x1, y, x2, 0.8)
    rule(x1, y + 1.1, x2, 0.8)


def paras(body):
    return [p.strip() for p in body.replace("\r", "").split("\n\n") if p.strip()]


def byline_text(a):
    """The byline line + provenance badge, mirroring paper.html's srcBadge():
    régiment of origin, or « Rédigé par IA » when the text was AI-generated."""
    parts = []
    if a.get("byline"):
        parts.append("par " + a["byline"])
    src = (a.get("source") or "").strip()
    if src:
        parts.append("Rédigé par IA" if src.lower() in ("ia", "ai") else src)
    return " · ".join(parts).upper()


def _sniff_ext(data):
    """Real image extension from magic bytes — don't trust the URL. A `.jpg` URL
    on foxhole.wiki.gg serves WebP via content negotiation."""
    if data[:2] == b"\xff\xd8":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return ".tif"
    return ".png"


def fetch_image(url):
    """Download an image URL to a temp file Scribus can decode (or None). Sends a
    browser User-Agent (hosts like foxhole.wiki.gg 403 the default urllib UA) and
    an Accept that avoids WebP/AVIF. Scribus picks its decoder from the file
    extension, so the extension is set from the real magic bytes — and WebP, which
    Scribus can't read, is converted to PNG with ImageMagick."""
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/124 Safari/537.36",
            "Accept": "image/jpeg,image/png,image/gif,image/tiff,image/*;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        ext = _sniff_ext(data)
        fd, path = tempfile.mkstemp(suffix=ext)
        os.close(fd)
        with open(path, "wb") as f:
            f.write(data)
        if ext == ".webp":                       # Scribus can't decode WebP
            png = path[:-5] + ".png"
            try:
                subprocess.run(["convert", path, png], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return png
            except Exception as e:
                print("  (webp->png convert failed: %s)" % e)
        return path
    except Exception as e:
        print("  (image fetch failed: %s)" % e)
        return None


def place_emblem(path, x, y, size):
    if not path:
        return
    try:
        fr = scribus.createImage(x, y, size, size)
        scribus.loadImage(path, fr)
        scribus.setScaleImageToFrame(1, 1, fr)   # scale to frame, proportional
        scribus.setLineColor("None", fr)
    except Exception as e:
        print("  (emblem place failed: %s)" % e)


def image_size(path):
    """Native (w, h) in pixels for PNG/GIF/JPEG/WEBP, or None. Pure stdlib so it
    works inside Scribus's interpreter."""
    import struct
    try:
        with open(path, "rb") as f:
            head = f.read(30)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                return struct.unpack(">II", head[16:24])
            if head[:6] in (b"GIF87a", b"GIF89a"):
                return struct.unpack("<HH", head[6:10])
            if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
                fmt = head[12:16]
                if fmt == b"VP8 ":
                    return (struct.unpack("<H", head[26:28])[0] & 0x3fff,
                            struct.unpack("<H", head[28:30])[0] & 0x3fff)
                if fmt == b"VP8L":
                    b = head[21:25]; bits = b[0] | b[1] << 8 | b[2] << 16 | b[3] << 24
                    return (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
                if fmt == b"VP8X":
                    return ((head[24] | head[25] << 8 | head[26] << 16) + 1,
                            (head[27] | head[28] << 8 | head[29] << 16) + 1)
            if head[:2] == b"\xff\xd8":          # JPEG: scan to a SOF marker
                f.seek(2); b = f.read(1)
                while b:
                    while b and b != b"\xff": b = f.read(1)
                    while b == b"\xff": b = f.read(1)
                    if not b: break
                    m = b[0]
                    if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                        f.read(3); hh, ww = struct.unpack(">HH", f.read(4)); return ww, hh
                    seg = struct.unpack(">H", f.read(2))[0]; f.seek(seg - 2, 1); b = f.read(1)
    except Exception:
        pass
    return None


def place_photo(path, x, y, w, h, cover=False):
    """Place a story photo. cover=True fills the whole w×h box crop-to-fill (like
    the web's object-fit:cover) by pre-cropping to the box aspect with ImageMagick;
    otherwise fit proportionally, centred. Aspect ratio is always preserved (equal
    x/y scale). Returns True if placed."""
    if not path:
        return False
    try:
        if cover:
            tw, th = max(1, int(w / 25.4 * 200)), max(1, int(h / 25.4 * 200))  # 200dpi target
            cropped = path + ".cover.jpg"
            try:
                subprocess.run(["convert", path, "-resize", "%dx%d^" % (tw, th),
                                "-gravity", "center", "-extent", "%dx%d" % (tw, th), cropped],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                path = cropped
            except Exception as e:
                print("  (cover crop failed, fitting instead: %s)" % e); cover = False
        # Frame sized to the displayed image (no letterbox), scale set explicitly
        # from the native size (setScaleImageToFrame is unreliable in a busy doc).
        dims = image_size(path)
        fx, fy, fw, fh, s = x, y, w, h, None
        if dims and dims[0] and dims[1]:
            iw, ih = dims
            fit = min(w * 72.0 / (25.4 * iw), h * 72.0 / (25.4 * ih))
            s = fit
            fw, fh = iw * s / 72.0 * 25.4, ih * s / 72.0 * 25.4
            fx, fy = x + (w - fw) / 2.0, y + (h - fh) / 2.0
        fr = scribus.createImage(fx, fy, fw, fh)
        scribus.loadImage(path, fr)
        if s is not None:
            scribus.setImageScale(s, s, fr)
        else:
            scribus.setScaleImageToFrame(scaletoframe=1, proportional=1, name=fr)
        scribus.setLineColor("Hair", fr)
        scribus.setLineWidth(0.4, fr)
        return True
    except Exception as e:
        print("  (photo place failed: %s)" % e)
        return False


# ════════════════════════════════════════════════════════════════════════
def main():
    with open(ISSUE, encoding="utf-8") as f:
        data = json.load(f)
    arts = data.get("articles", [])

    scribus.newDocument((PW, PH), (M, M, M, M), scribus.PORTRAIT, 1,
                        scribus.UNIT_MILLIMETERS, scribus.PAGE_1, 0, 1)
    scribus.setUnit(scribus.UNIT_MILLIMETERS)

    define_theme(data.get("theme"))

    # paper background
    bg = scribus.createRect(0, 0, PW, PH)
    scribus.setFillColor("Paper", bg)
    scribus.setLineColor("None", bg)

    # styles
    mkstyle("Nameplate", plate_head_font(data.get("plate")), 56, ALIGN_C)
    mkstyle("Tagline", F_BODY_IT, 12, ALIGN_C)
    mkstyle("BarL", F_SANS, 8, ALIGN_L)
    mkstyle("BarC", F_SANS, 9, ALIGN_C)
    mkstyle("BarR", F_SANS, 8, ALIGN_R)
    mkstyle("KickerC", F_SANS, 8.5, ALIGN_C, "Accent", gapafter=1.5)
    mkstyle("KickerL", F_SANS, 8, ALIGN_L, "Accent", gapbefore=7.0, gapafter=1.0)
    mkstyle("HLead", F_HEAD, 34, ALIGN_C)
    mkstyle("Deck", F_BODY_IT, 14, ALIGN_C, gapbefore=2.0)
    mkstyle("BylineC", F_SANS, 8, ALIGN_C, gapbefore=2.0)
    mkstyle("BylineL", F_SANS, 7.5, ALIGN_L, gapafter=1.5)
    mkstyle("HMajor", F_HEAD, 22, ALIGN_L, gapafter=1.5)
    mkstyle("HMinor", F_HEAD, 14, ALIGN_L, gapafter=1.0)
    mkstyle("HBrief", F_HEAD, 11, ALIGN_L, gapafter=1.0)
    mkstyle("Body", F_BODY, 9.5, ALIGN_BLOCK, firstindent=10.0)
    mkstyle("BodyDrop", F_BODY, 9.5, ALIGN_BLOCK, dropcap=1)
    mkstyle("LeadBody", F_BODY, 10.5, ALIGN_BLOCK, firstindent=11.0)
    mkstyle("LeadBodyDrop", F_BODY, 10.5, ALIGN_BLOCK, dropcap=1)
    mkstyle("SloganL", F_HEAD, 11, ALIGN_L)
    mkstyle("SloganC", F_HEAD, 11, ALIGN_C)
    mkstyle("SloganR", F_HEAD, 11, ALIGN_R)

    ear = data.get("ear") or []
    slogans = [strip_html(s) for s in (data.get("slogans") or [])]
    regiment = strip_html(ear[2]) if len(ear) > 2 and ear[2] else "Warden"

    y = M

    # ── Masthead ────────────────────────────────────────────────────────
    rule(CX, y + 5, CX + CW, 0.4, "Ink")
    name_f = scribus.createText(CX, y + 1, CW, 24)
    add(name_f, data.get("masthead", "Le Petit Daihbi"), "Nameplate")
    tag_f = scribus.createText(CX, y + 26, CW, 7)
    add(tag_f, data.get("tagline", ""), "Tagline")
    # regiment crests flanking the nameplate (full colour)
    EM = 22
    place_emblem(fetch_image(data.get("emblem_left")), CX, y + 4, EM)
    place_emblem(fetch_image(data.get("emblem_right")), CX + CW - EM, y + 4, EM)

    yb = y + 34
    double_rule(CX, yb, CX + CW)
    bar_h = 6
    bl = scribus.createText(CX, yb + 1.5, CW * 0.4, bar_h)
    add(bl, data.get("date_fr", data.get("date", "")).upper(), "BarL")
    bc = scribus.createText(CX + CW * 0.3, yb + 1.5, CW * 0.4, bar_h)
    add(bc, data.get("edition", "").upper(), "BarC")
    br = scribus.createText(CX + CW * 0.6, yb + 1.5, CW * 0.4, bar_h)
    add(br, regiment.upper(), "BarR")
    double_rule(CX, yb + bar_h + 2, CX + CW)

    y = yb + bar_h + 5     # content starts here

    # ── Lead story ───────────────────────────────────────────────────────
    leads = [a for a in arts if a["weight"] == "lead"]
    lead = leads[0] if leads else None
    rest = [a for a in arts if a is not lead]
    rest = [dict(a, weight="major") if a["weight"] == "lead" else a for a in rest]

    if lead:
        kf = scribus.createText(CX, y, CW, 5)
        add(kf, lead["kicker"].upper() or " ", "KickerC")
        y += 6
        # Headline frame height adapts to estimated line count (≈34 chars/line
        # at 34pt across the full content width) so long headlines don't clip.
        hlines = max(1, math.ceil(len(lead["headline"]) / 34.0))
        hh = hlines * 14 + 2
        hf = scribus.createText(CX, y, CW, hh)
        add(hf, lead["headline"], "HLead")
        y += hh + 1
        if lead["subhead"]:
            dlines = max(1, math.ceil(len(lead["subhead"]) / 70.0))
            dh = dlines * 7 + 2
            df = scribus.createText(CX, y, CW, dh)
            add(df, lead["subhead"], "Deck")
            y += dh
        lead_by = byline_text(lead)
        if lead_by:
            # Author headshot above the byline — the web edition shows it inline;
            # in the well's linked auto-flow an image can't be inlined per story,
            # but the lead is absolutely positioned so we can mirror it here.
            av = fetch_image(lead.get("author_avatar"))
            if av:
                AV = 7.0
                place_emblem(av, CX + (CW - AV) / 2.0, y, AV)
                y += AV + 1
            bf = scribus.createText(CX, y, CW, 5)
            add(bf, lead_by, "BylineC")
            y += 5
        y += 1
        # lead hero photo — the prominent image the web edition shows under the
        # headline (was previously dropped by the print layout).
        lead_ph_h = 120
        if place_photo(fetch_image(lead.get("image_url")), CX, y, CW, lead_ph_h, cover=True):
            y += lead_ph_h + 2
        rule(CX, y, CX + CW, 0.4, "Hair")
        y += 2
        lb_h = 66
        lb = scribus.createText(CX, y, CW, lb_h)
        scribus.setColumns(3, lb)
        scribus.setColumnGap(CGAP, lb)
        for i, p in enumerate(paras(lead["body"])):
            add(lb, p, "LeadBodyDrop" if i == 0 else "LeadBody")
        scribus.hyphenateText(lb)
        y += lb_h + 3
        double_rule(CX, y, CX + CW)
        y += 4

    # ── The well: everything else, 5-column auto-flow ────────────────────
    footer_h = 9 if slogans else 0          # reserve room for the slogan bar
    well_top = y
    well_h = (PH - M) - well_top - footer_h
    well = scribus.createText(CX, well_top, CW, well_h)
    scribus.setColumns(COLS, well)
    scribus.setColumnGap(CGAP, well)

    for idx, a in enumerate(rest):
        hstyle = {"major": "HMajor", "minor": "HMinor", "brief": "HBrief"}.get(a["weight"], "HMinor")
        # KickerL carries the gap-before that separates stories; if a story has
        # no kicker, emit one anyway (the section/weight) so spacing holds.
        add(well, (a["kicker"] or a["weight"]).upper(), "KickerL")
        add(well, a["headline"], hstyle)
        a_by = byline_text(a)
        if a_by:
            add(well, a_by, "BylineL")
        if a["subhead"]:
            add(well, a["subhead"], "Body")
        body_ps = paras(a["body"])
        for j, p in enumerate(body_ps):
            add(well, p, "Body")
    scribus.hyphenateText(well)

    # overflow → extra pages, linked. The cap stops a runaway issue from spinning
    # forever; if we still overflow after it, stories would be silently dropped —
    # so warn loudly (to stderr, where the publisher surfaces it) instead.
    prev = well
    guard, GUARD_MAX = 0, 24
    while scribus.textOverflows(prev) and guard < GUARD_MAX:
        guard += 1
        scribus.newPage(-1)
        scribus.gotoPage(scribus.pageCount())
        nf = scribus.createText(CX, M, CW, PH - 2 * M)
        scribus.setColumns(COLS, nf)
        scribus.setColumnGap(CGAP, nf)
        scribus.linkTextFrames(prev, nf)
        prev = nf
    if scribus.textOverflows(prev):
        sys.stderr.write(
            "WARNING: issue content still overflows after %d pages — some stories "
            "are not shown in the PDF. Trim the edition or raise GUARD_MAX in "
            "layout.py.\n" % (GUARD_MAX + 1))

    # ── Slogan footer bar (page 1) ───────────────────────────────────────
    if slogans:
        scribus.gotoPage(1)
        sy = PH - M - footer_h + 1
        double_rule(CX, sy, CX + CW)
        n = len(slogans)
        cellw = CW / float(n)
        for i, s in enumerate(slogans):
            style = "SloganL" if i == 0 else ("SloganR" if i == n - 1 else "SloganC")
            sf = scribus.createText(CX + i * cellw, sy + 1.5, cellw, 7)
            add(sf, s, style)
        double_rule(CX, PH - M, CX + CW)

    # ── Export ───────────────────────────────────────────────────────────
    scribus.saveDocAs(OUTSLA)
    pdf = scribus.PDFfile()
    pdf.file = OUTPDF
    pdf.fontEmbedding = 0
    pdf.quality = 0
    pdf.resolution = 300
    pdf.save()


main()
