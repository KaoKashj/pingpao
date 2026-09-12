#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract text pages from the AI major 培养方案 PDF into a txt file."""
import sys

PDF = "/Users/kaorouchuan/Desktop/浙江大学/浙江大学2026级培养方案PDF/计算机科学与技术学院/2026级人工智能专业培养方案.pdf"
OUT = "/Users/kaorouchuan/Documents/ChatGPT/选课/培养方案_人工智能_2026.txt"

import pdfplumber

with pdfplumber.open(PDF) as pdf:
    print("pages:", len(pdf.pages))
    lines = []
    for i, page in enumerate(pdf.pages):
        lines.append(f"\n===== PAGE {i+1} =====\n")
        txt = page.extract_text() or ""
        lines.append(txt)
    full = "\n".join(lines)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(full)
    print("chars:", len(full))
