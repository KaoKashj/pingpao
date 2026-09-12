#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract text pages from the AI major 培养方案 PDF into a txt file."""
from config import path, pdf_path
import sys

PDF = pdf_path()
OUT = path("培养方案_人工智能_2026.txt")

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
