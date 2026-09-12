#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""For every course code in the 培养方案, fetch its teaching sections for
2026-2027-1 from zdbk, keep the ones whose schedule includes 周五."""
from config import load_jwglxt, path, tmp
import json, re, urllib.parse

mod = load_jwglxt()

PLAN_TSV = path("培养方案课程清单.tsv")

j = mod.Jwglxt(*mod.get_credentials())
if not j.login():
    raise SystemExit("login fail")
ctx, _ = j.course_context()
xn, xq = ctx["xn"], ctx["xq"]

plan = []
for ln in open(PLAN_TSV, encoding="utf-8"):
    ln = ln.rstrip("\n")
    if not ln or ln.startswith("#"):
        continue
    parts = ln.split("\t")
    plan.append({"code": parts[0], "name": parts[1], "cat": parts[2] if len(parts) > 2 else ""})
print("plan codes:", len(plan), flush=True)

def jxb(dl, kcdm):
    params = {"dl": dl, "xn": xn, "xq": xq, "kcdm": kcdm,
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

DL_CANDIDATES = ["xk_b", "xk_1", "xk_4", "zy_qb", "Z", "xk_1_1", "zy_b", "xhxk"]

offered = []   # {code,name,cat,sections}
for p in plan:
    arr = None
    for dl in DL_CANDIDATES:
        arr = jxb(dl, p["code"])
        if arr:
            break
    if arr:
        offered.append({"code": p["code"], "name": p["name"], "cat": p["cat"],
                        "dl": dl, "n": len(arr), "sections": arr})
    print("%s %s -> %s" % (p["code"], p["name"], ("%d jxb" % len(arr)) if arr else "无教学班"), flush=True)

with open(tmp("jwglxt_offered_plan.json"), "w", encoding="utf-8") as f:
    json.dump(offered, f, ensure_ascii=False, indent=1)

def has_fri(it):
    s = (it.get("sksj") or "").replace("<br>", ";").replace("；", ";").replace(";", " ")
    return "周五" in s

fri_courses = [c for c in offered if any(has_fri(s) for s in c["sections"])]
print("\n== 本学期开设的培养方案课程数:", len(offered))
print("== 其中含周五教学班的课程数:", len(fri_courses))

with open(path("周五课程明细.tsv"), "w", encoding="utf-8") as f:
    f.write("课程号\t课程名称\t培养方案类别\t教学班\t教师\t上课时间\t地点\t学期段\t考试时间\t容量(已选/容量)\t是否已选\n")
    for c in offered:
        for s in c["sections"]:
            f.write("\t".join([
                c["code"], c["name"], c["cat"], s.get("xkkh", ""),
                (s.get("jsxm") or "").replace("<br>", "、"),
                (s.get("vsksj") or s.get("sksj") or "").replace("<br>", ";"),
                (s.get("skdd") or "").replace("<br>", ";"),
                s.get("t_xxq") or s.get("xxq") or "",
                (s.get("vkssj") or s.get("kssj") or "").replace("<br>", ";"),
                s.get("rs", ""), "是" if s.get("sfxz") == "1" else "否",
            ]) + "\n")

print("saved 周五课程明细.tsv")
print("\n== 周五课程列表 ==")
for c in fri_courses:
    fri_s = [s for s in c["sections"] if has_fri(s)]
    print("%s %s (%s) 共%d个教学班, 含周五%d个" % (c["code"], c["name"], c["cat"], len(c["sections"]), len(fri_s)))
    for s in fri_s:
        print("   -", s.get("xkkh"), "|", (s.get("jsxm") or "").replace("<br>", "、"),
              "|", (s.get("vsksj") or "").replace("<br>", ";"),
              "|", (s.get("skdd") or "").replace("<br>", ";"),
              "| rs:", s.get("rs"), "| 已选:", s.get("sfxz"))
