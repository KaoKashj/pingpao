#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch 自主选课 page HTML, list script assets, dump for inspection."""
from config import load_jwglxt, tmp
import re, sys, urllib.parse

mod = load_jwglxt()

j = mod.Jwglxt(*mod.get_credentials())
if not j.login():
    sys.exit("登录失败")

url = "https://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbIndex.html?gnmkdm=N253530"
resp, body = j.req(url)
open(tmp("zzxk_index.html"), "w", encoding="utf-8").write(body)
print("index bytes:", len(body))
scripts = re.findall(r'<script[^>]+src="([^"]+)"', body)
for s in scripts:
    print("SCRIPT", s)
print("---inline keywords---")
for kw in ["教学班", "上课时间", "cxZzxkGhbXk", "cxXkxx", "kcb", "周次", "节"]:
    print(kw, body.count(kw))
