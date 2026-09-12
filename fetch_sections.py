#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取全部候选课程（zdbk 目录 + 培养方案知识库）的教学班信息。

不按星期筛选——抓到的教学班全部保留，输出成一张可筛选的明细表。
筛选留给下游（比如网页上的"空闲时段"过滤）。

候选来源 = zdbk 选课目录 ∪ kb.json（131 个专业的培养方案课程）。
注：全部专业的课号加起来有几千个，逐门查教学班会比较慢；
只需要自己专业的话，改 kb.json 的读取范围即可。"""
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
# 2) 培养方案知识库：131 个专业的带课号课程（kb.json，由 build_kb.py 生成）
#    原来这里只读某一个专业的课程清单（写死的），现在改成 kb.json 里的全部专业。
kb = json.load(open(path("kb.json"), encoding="utf-8"))
plan_codes = 0
for major in kb["majors"]:
    for code, name, _credit, cat in major["courses"]:
        plan_codes += 1
        if code in cand:
            cand[code]["labels"] = sorted(set(cand[code].get("labels", []) + [cat]))
            cand[code]["src"] = cand[code]["src"] + "+培养方案"
        else:
            cand[code] = {"kcmc": name, "kkxy": "", "labels": [cat], "src": "培养方案"}
        if not cand[code]["kcmc"]:
            cand[code]["kcmc"] = name
print("知识库: %d 个专业 / %d 条课程记录" % (kb["majorCount"], plan_codes), flush=True)

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

# 原来这里有个 has_fri()，只保留周五开课的教学班。
# 现在不按星期筛了：抓到的教学班全部保留，用得到的时候再按自己的时段过滤。

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
        if arr:
            results.append({"code": code, **cand[code],
                            "total_sections": len(arr), "sections": arr})
    if (i + 1) % 40 == 0:
        el = time.time() - t0
        print("  %d/%d  elapsed %.0fs" % (i + 1, len(codes), el), flush=True)

el = time.time() - t0
print("done in %.0fs  | no-section:%d  err:%d  courses-with-sections:%d" % (
    el, no_sec, empty, len(results)), flush=True)

json.dump(results, open(tmp("jwglxt_sections.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---- TSV ----
tsv = path("候选课程教学班明细.tsv")
with open(tsv, "w", encoding="utf-8") as f:
    f.write("课程号\t课程名称\t开课学院\t候选依据\t所在目录/方案类别\t教学班\t教师\t上课时间\t地点\t学期段\t考试时间\t容量(已选/容量)\t是否已选\n")
    for r in sorted(results, key=lambda x: x["code"]):
        for s in r["sections"]:
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
print("\n== 有教学班的课程(共%d门) ==" % len(results))
for r in sorted(results, key=lambda x: x["code"]):
    all_times = sorted({(s.get("vsksj") or s.get("sksj") or "") for s in r["sections"]})
    print("%s\t%s\t%s\t%d门课%d个班\t%s" % (
        r["code"], r.get("kcmc", ""), "、".join(r.get("labels", [])) or "-",
        len(r["total_sections"]), len(r["sections"]), " | ".join(all_times)))
