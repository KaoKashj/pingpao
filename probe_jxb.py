#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test JxbList endpoint for sample course codes; print returned teaching-class fields."""
import importlib.util, json, sys, urllib.parse

spec = importlib.util.spec_from_file_location(
    "zju_jwglxt", "/Users/kaorouchuan/.codex/skills/zju-jwglxt/scripts/zju_jwglxt.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

j = mod.Jwglxt(*mod.get_credentials())
if not j.login():
    sys.exit("登录失败")
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

codes = ["EDU2001G", "MARX1004G", "MATH1135G", "AI1001G", "ECON2001G"]
dl_guesses = ["xk_b", "Z", "xk_4", "zy_qb", "G", "T"]
for code in codes:
    for dl in dl_guesses:
        arr = jxb(dl, code, "T(%s-%s)-%s" % (xn, xq, code))
        if arr:
            print("\n### %s (dl=%s) -> %d 教学班" % (code, dl, len(arr)), flush=True)
            keys = set()
            for it in arr:
                keys.update(it.keys())
            print("keys:", sorted(keys), flush=True)
            for it in arr[:2]:
                print(json.dumps({k: it.get(k) for k in sorted(keys)}, ensure_ascii=False)[:1200], flush=True)
            break
    else:
        print("\n### %s -> no result in dl %s" % (code, dl_guesses), flush=True)
