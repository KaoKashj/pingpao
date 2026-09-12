#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enumerate zdbk 自主选课 catalogs for the plan-relevant categories
(通识必修一级/二级 + 通识选修一级/二级 + 体育) into a candidate course set."""
from config import load_jwglxt, tmp
import json, sys, time, urllib.parse

mod = load_jwglxt()

j = mod.Jwglxt(*mod.get_credentials())
if not j.login():
    raise SystemExit("login fail")
ctx, cats = j.course_context()
xn, xq, nj, zydm = ctx["xn"], ctx["xq"], ctx["nj"], ctx["zydm"]
print("xn", xn, "xq", xq, "nj", nj, "zydm", zydm, flush=True)

# (dl, lx, kcbs, xkmc, label)
QUERIES = [
    ("xk_b", "bl", "", "通识必修课程", "通识必修-全部"),
    ("EA",   "zl", "必修课程",         "思政类", "通识必修-思政必修"),
    ("EA",   "zl", "选择性必修课程",    "思政类", "通识必修-思政选择性必修"),
    ("EB",   "zl", "", "军体类", "通识必修-军体"),
    ("F",    "zl", "英语进阶课程", "外语类", "通识必修-外语进阶"),
    ("F",    "zl", "英语发展课程", "外语类", "通识必修-外语发展"),
    ("F",    "zl", "英语高阶课程", "外语类", "通识必修-外语高阶"),
    ("F",    "zl", "英语卓越课程", "外语类", "通识必修-外语卓越"),
    ("F",    "zl", "小语种课程",   "外语类", "通识必修-小语种"),
    ("G",    "zl", "", "计算机类", "通识必修-计算机"),
    ("T",    "zl", "", "自然科学通识类", "通识必修-自然科学"),
    ("xk_n", "bl", "", "新通识选修课程", "通识选修-全部"),
    ("zhct", "zl", "", "中华传统", "通识选修-中华传统"),
    ("sjwm", "zl", "", "世界文明", "通识选修-世界文明"),
    ("ddsh", "zl", "", "当代社会", "通识选修-当代社会"),
    ("kjcx", "zl", "", "科技创新", "通识选修-科技创新"),
    ("wysm", "zl", "", "文艺审美", "通识选修-文艺审美"),
    ("smts", "zl", "", "生命探索", "通识选修-生命探索"),
    ("byjy", "zl", "", "博雅技艺", "通识选修-博雅技艺"),
    ("xhxk", "zl", "", "通识核心课程", "通识选修-通识核心"),
    ("xk_8", "bl", "", "体育课程", "体育课程"),
]

def list_page(dl, lx, kcbs, xkmc, kspage, jspage):
    jxjhh = nj + zydm
    params = {
        "dl": dl, "lx": lx, "xkmc": xkmc, "kcbs": kcbs,
        "nj": nj, "xn": xn, "xq": xq, "zydm": zydm, "jxjhh": jxjhh,
        "xnxq": "(%s-%s)-" % (xn, xq), "kspage": str(kspage), "jspage": str(jspage),
    }
    _, body = j.req(
        "https://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbKcList.html",
        data=urllib.parse.urlencode(params).encode(),
        referer="https://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbIndex.html?gnmkdm=N253530",
    )
    try:
        return json.loads(body)
    except Exception:
        return None

PAGE = 200
seen_code = {}
by_label = {}

def add(code, it, label):
    if code not in seen_code:
        seen_code[code] = {"code": code, "kcmc": it.get("kcmc", ""),
                           "kkxy": it.get("kkxy", ""), "kclb": it.get("kclb", ""),
                           "kcxz": it.get("kcxz", ""), "kcxx": it.get("kcxx", ""),
                           "kcbs": it.get("kcbs", ""), "kcgs": it.get("kcgs", ""),
                           "xskcdm": it.get("xskcdm", ""), "xxq": it.get("xxq", ""),
                           "labels": set()}
    seen_code[code]["labels"].add(label)
    by_label.setdefault(label, []).append(code)

for dl, lx, kcbs, xkmc, label in QUERIES:
    total = 0
    k = 0
    while True:
        arr = list_page(dl, lx, kcbs, xkmc, k * PAGE + 1, (k + 1) * PAGE)
        if not arr:
            break
        for it in arr:
            code = it.get("kcdm")
            if code:
                add(code, it, label)
                total += 1
        if len(arr) < PAGE:
            break
        k += 1
        if k >= 60:   # safety cap (12000 rows)
            break
    print("[%s] %d 条" % (label, total), flush=True)

for c in seen_code.values():
    c["labels"] = sorted(c["labels"])

out = sorted(seen_code.values(), key=lambda c: c["code"])
with open(tmp("jwglxt_catalog.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("\n== 通识类候选课程(去重后):", len(out), "门 ==")
for label, codes in by_label.items():
    print("  %-22s %4d" % (label, len(codes)))
