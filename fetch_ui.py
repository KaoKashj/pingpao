#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch 自主选课 page HTML, list script assets, dump for inspection."""
import importlib.util, re, sys, urllib.parse

spec = importlib.util.spec_from_file_location(
    "zju_jwglxt", "/Users/kaorouchuan/.codex/skills/zju-jwglxt/scripts/zju_jwglxt.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

j = mod.Jwglxt(*mod.get_credentials())
if not j.login():
    sys.exit("登录失败")

url = "https://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbIndex.html?gnmkdm=N253530"
resp, body = j.req(url)
open("/tmp/zzxk_index.html", "w", encoding="utf-8").write(body)
print("index bytes:", len(body))
scripts = re.findall(r'<script[^>]+src="([^"]+)"', body)
for s in scripts:
    print("SCRIPT", s)
print("---inline keywords---")
for kw in ["教学班", "上课时间", "cxZzxkGhbXk", "cxXkxx", "kcb", "周次", "节"]:
    print(kw, body.count(kw))
