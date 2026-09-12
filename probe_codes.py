#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""For a sample of plan codes, try JxbList across candidate dls to see which return sections."""
from config import load_jwglxt
import json, urllib.parse

mod = load_jwglxt()

j = mod.Jwglxt(*mod.get_credentials())
if not j.login():
    raise SystemExit("login fail")
ctx, _ = j.course_context()
xn, xq = ctx["xn"], ctx["xq"]

def jxb(dl, kcdm, xkkh):
    params = {"dl": dl, "xn": xn, "xq": xq, "kcdm": kcdm, "xkkh": xkkh, "ylxs": "1"}
    _, body = j.req(
        "https://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbJxbList.html",
        data=urllib.parse.urlencode(params).encode(),
        referer="https://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbIndex.html?gnmkdm=N253530",
    )
    try:
        return json.loads(body)
    except Exception:
        return None

codes = ["AI2002M", "AI2005M", "AI1001M", "AI1004M", "MATH2432F", "CS3162M",
         "MARX2004G", "MATH1232G", "SIS1001G", "BIO1001G", "CS3256M",
         "PPAE4001G", "ADMN1001G", "AI3001M", "AI2007M", "AI3004M"]
dls = ["xk_b", "xk_1", "xk_1_1", "Z", "xk_4", "zy_b", "zy_qb", "xhxk"]
for code in codes:
    hits = []
    for dl in dls:
        arr = jxb(dl, code, "T(%s-%s)-%s" % (xn, xq, code))
        if arr:
            fri = sum(1 for it in arr if "周五" in (it.get("sksj") or ""))
            hits.append("%s:%d(fri%d)" % (dl, len(arr), fri))
    print("%-12s -> %s" % (code, " | ".join(hits) if hits else "EMPTY"), flush=True)
