#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan zdbk 选课 categories, dump all offerings to /tmp, inspect fields."""
from config import load_jwglxt, tmp
import json, sys

mod = load_jwglxt()

j = mod.Jwglxt(*mod.get_credentials())
if not j.login():
    sys.exit("登录失败")

ctx, cats = j.course_context()
print("学年学期:", ctx["xn"], ctx["xq"], "| 年级", ctx["nj"], "| 专业", ctx["zydm"])

# collect all items per category
out = []
keys = set()
for dl, name in cats:
    got = 0
    page = 200
    for k in range(12):
        arr = j.course_list(dl, ctx, kspage=k * page + 1, jspage=(k + 1) * page)
        if not arr:
            break
        for it in arr:
            keys.update(it.keys())
            out.append({"cat": dl, "cat_name": name, "item": it})
            got += 1
        if len(arr) < page:
            break
    print("[%s] %s 门" % (name, got), flush=True)

with open(tmp("jwglxt_scan_all.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)

print("\nunion of keys:", sorted(keys))
