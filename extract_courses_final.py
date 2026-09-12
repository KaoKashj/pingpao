#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract (课程号, 课程名称) rows from the 培养方案 course tables."""
import re
import pdfplumber

PDF = "/Users/kaorouchuan/Desktop/浙江大学/浙江大学2026级培养方案PDF/计算机科学与技术学院/2026级人工智能专业培养方案.pdf"

WATERMARK = set("ytisrevnUgnaijehZ浙江大学")

def clean_line(words):
    ws = [w for w in words if not (len(w["text"].strip()) == 1 and w["text"] in WATERMARK)]
    ws.sort(key=lambda w: (round(w["top"] / 4.0), w["x0"]))
    return " ".join(w["text"] for w in ws)

CODE_RE = re.compile(r"[A-Za-z]{2,8}\d{3,5}[A-Za-z]?")
CREDIT_RE = re.compile(r"\d+\.\d")

def lines_for_page(page):
    words = [w for w in page.extract_words()]
    words.sort(key=lambda w: (round(w["top"] / 4.0), w["x0"]))
    lines, cur = [], None
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
    return [clean_line(l) for l in lines]

rows = {}   # code -> dict
order = []

def add(code, text):
    # text like "<CODE> <name> <credit> ..." ; name = middle part before credit number
    m = CREDIT_RE.search(text[len(code):])
    if m:
        name_part = text[len(code):m.start()].strip()
    else:
        name_part = text[len(code):].strip()
    # strip trailing digits/'*'
    name = re.sub(r"\s+", "", name_part)
    name = re.sub(r"[*]+$", "", name).strip()
    if code not in rows:
        rows[code] = {"name": name, "raw": [text]}
        order.append(code)
    else:
        rows[code]["raw"].append(text)
        # prefer longer name
        cand = re.sub(r"\s+", "", name_part).rstrip("*")
        if len(cand) > len(rows[code]["name"]):
            rows[code]["name"] = cand

with pdfplumber.open(PDF) as pdf:
    for pno in range(4, 13):
        for ln in lines_for_page(pdf.pages[pno - 1]):
            # strip stray leading watermark chars
            ln2 = ln
            while ln2 and len(ln2.split()[0]) == 1 and ln2.split()[0] in WATERMARK:
                ln2 = ln2[1:].strip()
            mm = re.match(r"^([A-Za-z]{2,8}\d{3,5}[A-Za-z]?)\b", ln2)
            if mm:
                code = mm.group(1)
                # normalize weird single-char corruption inside code (e.g. AaI3004M)
                add(code, ln2)

for code in order:
    r = rows[code]
    print(f"{code}\t{r['name']}\t{r['raw'][0]}")
print("\nTotal unique course codes:", len(order))
