#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把一份培养方案 PDF 的文本抽出来（调试用）。

产物写在临时目录，不进仓库——真正要用的课程清单在 kb.json 里，
由 build_kb.py 从全部培养方案的 PDF 解析而来。"""
from config import tmp, pdf_path
import sys

PDF = pdf_path()
OUT = tmp("plan_extract.txt")   # 临时产物，不进仓库

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
