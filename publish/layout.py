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

# ── Fonts (verified present in this Scribus) ────────────────────────────
F_HEAD = "Liberation Serif Bold"
F_HEAD_IT = "Liberation Serif Bold Italic"
F_BODY = "Liberation Serif Regular"
F_BODY_IT = "Liberation Serif Italic"
F_SANS = "Liberation Sans Bold"

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


def fetch_image(url):
    """Download an emblem URL to a temp file; return its path (or None)."""
    if not url:
        return None
    try:
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        urllib.request.urlretrieve(url, path)
        return path
    except Exception as e:
        print("  (emblem fetch failed: %s)" % e)
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


# ════════════════════════════════════════════════════════════════════════
def main():
    with open(ISSUE, encoding="utf-8") as f:
        data = json.load(f)
    arts = data.get("articles", [])

    scribus.newDocument((PW, PH), (M, M, M, M), scribus.PORTRAIT, 1,
                        scribus.UNIT_MILLIMETERS, scribus.PAGE_1, 0, 1)
    scribus.setUnit(scribus.UNIT_MILLIMETERS)

    defc("Ink", 26, 23, 20)
    defc("Accent", 122, 31, 26)
    defc("Paper", 245, 239, 225)
    defc("Hair", 170, 156, 130)

    # paper background
    bg = scribus.createRect(0, 0, PW, PH)
    scribus.setFillColor("Paper", bg)
    scribus.setLineColor("None", bg)

    # styles
    mkstyle("Nameplate", F_HEAD, 56, ALIGN_C)
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
        if lead["byline"]:
            bf = scribus.createText(CX, y, CW, 5)
            add(bf, ("par " + lead["byline"]).upper(), "BylineC")
            y += 5
        y += 1
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
        if a["byline"]:
            add(well, ("par " + a["byline"]).upper(), "BylineL")
        if a["subhead"]:
            add(well, a["subhead"], "Body")
        body_ps = paras(a["body"])
        for j, p in enumerate(body_ps):
            add(well, p, "Body")
    scribus.hyphenateText(well)

    # overflow → extra pages, linked
    prev = well
    guard = 0
    while scribus.textOverflows(prev) and guard < 8:
        guard += 1
        scribus.newPage(-1)
        scribus.gotoPage(scribus.pageCount())
        nf = scribus.createText(CX, M, CW, PH - 2 * M)
        scribus.setColumns(COLS, nf)
        scribus.setColumnGap(CGAP, nf)
        scribus.linkTextFrames(prev, nf)
        prev = nf

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
