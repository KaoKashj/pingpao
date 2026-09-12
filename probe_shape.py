#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect shape of offerings returned for relevant categories (first page only)."""
from config import load_jwglxt
import json, sys

mod = load_jwglxt()

j = mod.Jwglxt(*mod.get_credentials())
if not j.login():
    sys.exit("登录失败")
ctx, cats = j.course_context()
print("学年学期:", ctx["xn"], ctx["xq"], "| 年级", ctx["nj"], "| 专业", ctx["zydm"], flush=True)

interesting = ["xk_1", "xk_1_1", "xk_b", "EA", "EB", "F", "G", "T",
               "Z", "xk_4", "zy_b", "zy_qb", "xhxk"]
for dl in interesting:
    arr = j.course_list(dl, ctx, kspage=1, jspage=200)
    n = len(arr) if arr else 0
    print("\n### cat %s -> %d items" % (dl, n), flush=True)
    if not n:
        continue
    keys = set()
    for it in arr:
        keys.update(it.keys())
    print("keys:", sorted(keys), flush=True)
    # print two samples compactly
    for it in arr[:2]:
        s = json.dumps(it, ensure_ascii=False)
        print(s[:900], flush=True)
