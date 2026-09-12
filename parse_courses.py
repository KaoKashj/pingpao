#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconstruct table rows from the 培养方案 PDF using word positions,
filtering the 浙江大学 watermark chars, then extract course rows."""
from config import pdf_path
import re, json
import pdfplumber

PDF = pdf_path()

# single chars that form the diagonal watermark: letters + 浙 江 大 学
WATERMARK = set("ytisrevnUgnaijehZ浙江大学")

def is_watermark_word(w):
    t = w["text"].strip()
    return len(t) == 1 and t in WATERMARK

COURSE_RE = re.compile(r"^[A-Za-z]{2,6}\d{3,4}[A-Za-z]?$")

def lines_for_page(page):
    words = [w for w in page.extract_words() if not is_watermark_word(w)]
    words.sort(key=lambda w: (round(w["top"] / 4.0), w["x0"]))
    lines = []
    cur = None
    for w in words:
        bucket = round(w["top"] / 4.0)
        if cur is None or abs(bucket - cur[0]) > 1:
            if cur:
                lines.append(cur[1])
            cur = (bucket, [w])
        else:
            cur[1].append(w)
    if cur:
        lines.append(cur[1])
    out = []
    for ws in lines:
        ws.sort(key=lambda w: w["x0"])
        out.append(" ".join(w["text"] for w in ws))
    return out

all_lines = []
with pdfplumber.open(PDF) as pdf:
    for i, page in enumerate(pdf.pages):
        all_lines.append((i + 1, lines_for_page(page)))

# print all lines for pages 4-12 for inspection
for pno, lines in all_lines:
    if pno >= 4:
        print(f"\n----- page {pno} -----")
        for ln in lines:
            print(ln)
