#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch teaching sections for every candidate course (catalog pool + plan PDF
codes) and keep sections scheduled on Friday. Save results."""
from config import load_jwglxt, path, tmp
import json, sys, time, urllib.parse

mod = load_jwglxt()

j = mod.Jwglxt(*mod.get_credentials())
if not j.login():
    raise SystemExit("login fail")
ctx, _ = j.course_context()
xn, xq = ctx["xn"], ctx["xq"]

# 1) load catalog pool
pool = json.load(open(tmp("jwglxt_catalog.json"), encoding="utf-8"))
cand = {}   # code -> meta
for c in pool:
    cand[c["code"]] = {
        "kcmc": c.get("kcmc", ""),
        "kkxy": c.get("kkxy", ""),
        "labels": c.get("labels", []),
        "src": "zdbk通识/体育目录",
    }
# 2) plan pdf codes
for ln in open(path("培养方案课程清单.tsv"), encoding="utf-8"):
    ln = ln.rstrip("\n")
    if not ln or ln.startswith("#"):
        continue
    p = ln.split("\t")
    code, name, cat = p[0], p[1], p[2] if len(p) > 2 else ""
    if code in cand:
        cand[code]["labels"] = sorted(set(cand[code].get("labels", []) + [cat]))
        cand[code]["src"] = cand[code]["src"] + "+PDF"
    else:
        cand[code] = {"kcmc": name, "kkxy": "", "labels": [cat], "src": "PDF"}
    if not cand[code]["kcmc"]:
        cand[code]["kcmc"] = name

codes = sorted(cand)
print("candidate courses:", len(codes), flush=True)

def jxb(kcdm):
    params = {"dl": "xk_b", "xn": xn, "xq": xq, "kcdm": kcdm,
              "xkkh": "T(%s-%s)-%s" % (xn, xq, kcdm), "ylxs": "1"}
    _, body = j.req(
        "https://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbJxbList.html",
        data=urllib.parse.urlencode(params).encode(),
        referer="https://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbIndex.html?gnmkdm=N253530",
    )
    try:
        return json.loads(body)
    except Exception:
        return None

def has_fri(it):
    return "周五" in (it.get("sksj") or "")

results = []     # course entries that have >=1 Friday section
no_sec = 0
empty = 0
t0 = time.time()
for i, code in enumerate(codes):
    arr = jxb(code)
    if arr is None:
        empty += 1
    elif not arr:
        no_sec += 1
    else:
        fri = [s for s in arr if has_fri(s)]
        if fri:
            results.append({"code": code, **cand[code],
                            "total_sections": len(arr), "friday": fri})
    if (i + 1) % 40 == 0:
        el = time.time() - t0
        print("  %d/%d  elapsed %.0fs" % (i + 1, len(codes), el), flush=True)

el = time.time() - t0
print("done in %.0fs  | no-section:%d  err:%d  with-friday-courses:%d" % (
    el, no_sec, empty, len(results)), flush=True)

json.dump(results, open(tmp("jwglxt_friday.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---- TSV ----
tsv = path("周五开课_候选课程明细.tsv")
with open(tsv, "w", encoding="utf-8") as f:
    f.write("课程号\t课程名称\t开课学院\t候选依据\t所在目录/方案类别\t教学班\t教师\t周五上课时间\t地点\t学期段\t考试时间\t容量(已选/容量)\t是否已选\n")
    for r in sorted(results, key=lambda x: x["code"]):
        for s in r["friday"]:
            f.write("\t".join([
                r["code"], r.get("kcmc", ""), r.get("kkxy", ""), r.get("src", ""),
                "、".join(r.get("labels", [])) or "-",
                s.get("xkkh", ""), (s.get("jsxm") or "").replace("<br>", "、"),
                (s.get("vsksj") or s.get("sksj") or "").replace("<br>", ";"),
                (s.get("skdd") or "").replace("<br>", ";"),
                s.get("t_xxq") or s.get("xxq") or "",
                (s.get("vkssj") or s.get("kssj") or "").replace("<br>", ";"),
                s.get("rs", ""), "是" if s.get("sfxz") == "1" else "否",
            ]) + "\n")
print("saved", tsv, flush=True)

# ---- course-level summary print ----
print("\n== 含周五教学班的课程(共%d门) ==" % len(results))
for r in sorted(results, key=lambda x: x["code"]):
    fri_times = sorted({(s.get("vsksj") or s.get("sksj") or "") for s in r["friday"]})
    print("%s\t%s\t%s\t%d门课%d个周五班\t%s" % (
        r["code"], r.get("kcmc", ""), "、".join(r.get("labels", [])) or "-",
        len(r["total_sections"]), len(r["friday"]), " | ".join(fri_times)))
