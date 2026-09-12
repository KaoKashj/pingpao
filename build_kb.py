# -*- coding: utf-8 -*-
"""
build_kb.py — 从《浙江大学2026级培养方案》PDF 目录构建专业课程知识库 (kb.json)

基于 zdbk-course-schedule skill 的 plan-pdf-extraction.md 结论：
  - 这类 PDF 每页叠有水印单字（浙江大学 / ytisrevnUgnaijehZ），字号 >=20pt
  - 正文 9.0pt，章节标题 12.0pt
  - 课程行以课程号开头：^[A-Za-z]{2,8}\\d{3,5}[A-Za-z]?

产出结构：
{
  "generated": "...",
  "majors": [
     {"name": "人工智能", "college": "计算机科学与技术学院", "file": "...",
      "courses": [{"code","name","credits","category","section"}],
      "sections": {"一、通识课程 > 1.通识必修课程 > (1)思政类": 5, ...}}
  ]
}
"""
import json
import os
import re
import sys
import collections
from datetime import datetime

import pdfplumber

from config import PLAN_PDF_DIR, path as _path
ROOT = PLAN_PDF_DIR
OUT = _path("kb.json")

WATERMARK = set("ytisrevnUgnaijehZ浙江大学")
CODE_RE = re.compile(r"^([A-Za-z]{2,8}\d{3,5}[A-Za-z]?)\s")
HEAD_MIN = 10.5          # 标题字号下限（正文 9.0）
WATERMARK_MIN = 20.0     # 水印字号下限
CREDIT_RE = re.compile(r"^\d+(\.\d+)?$")

# 顶层章节 → 归一化类别。键是标题里的关键词，命中即归入对应类别。
TOP_RULES = [
    ("通识必修", "通识必修"), ("通识选修", "通识选修"), ("通识核心", "通识核心"),
    ("专业基础", "专业基础"),
    ("专业必修", "专业必修"), ("专业模块", "专业模块"),
    ("实践教学", "实践教学"), ("毕业论文", "毕业论文"),
    ("个性修读", "个性修读"), ("第二课堂", "第二课堂"), ("第三课堂", "第三课堂"),
    ("第四课堂", "第四课堂"),
    ("美育", "认定型-美育"), ("劳育", "认定型-劳育"),
    ("创新创业", "认定型-创新创业"), ("心理健康", "认定型-心理健康"),
    ("思政", "通识必修-思政"), ("军体", "通识必修-军体"), ("外语", "通识必修-外语"),
    ("计算机", "通识必修-计算机"), ("自然科学", "通识必修-自然科学"),
]

# 无课程号的开放池（只有规则，需要去教务网目录里取课）
OPEN_POOLS = [
    ("通识选修", "通识选修课程（含通识核心）没有固定课号，需按教务网目录纳入"),
    ("个性修读", "跨专业/自主修读模块按规则选择，无固定课号"),
]


def lines_of(page):
    """按坐标重建文本行，返回 [(文本, 最大字号)]，已剔除水印"""
    words = page.extract_words(extra_attrs=["size"])
    ws = [w for w in words if w["size"] < WATERMARK_MIN]
    ws.sort(key=lambda w: (round(w["top"] / 4.0), w["x0"]))
    groups, cur = [], None
    for w in ws:
        b = round(w["top"] / 4.0)
        if cur is None or abs(b - cur) > 1:
            groups.append([w])
            cur = b
        else:
            groups[-1].append(w)
    out = []
    for grp in groups:
        txt = " ".join(w["text"] for w in grp
                       if not (len(w["text"].strip()) == 1 and w["text"].strip() in WATERMARK))
        out.append((txt.strip(), max(w["size"] for w in grp)))
    return out


def normalize_category(heading_stack):
    """把标题栈归一化成一个类别名。

    关键：必须【由深到浅】匹配。从最外层匹配会让 "一、通识课程" 抢走
    所有内层标题（如 "二、专业基础课程"），导致分类泄漏。
    """
    for title in reversed(heading_stack):
        for kw, cat in TOP_RULES:
            if kw in title:
                return cat
    return heading_stack[-1] if heading_stack else "未分类"


def parse_pdf(path):
    courses, sections = {}, collections.Counter()
    stack = []          # 标题栈 [(level_marker, title)]，用缩进/序号推断层级
    in_plan_table = False

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for txt, size in lines_of(page):
                if not txt:
                    continue
                if size >= HEAD_MIN:
                    if len(txt) > 60:
                        continue
                    # 指导性计划表是重复视图，遇到就停用标题追踪（避免污染类别）
                    if "培养方案修读指导性计划" in txt:
                        in_plan_table = True
                        continue
                    # 层级：一、/二、 为 L1；1./2. 为 L2；(1) 为 L3
                    if re.match(r"^[一二三四五六七八九十]+、", txt):
                        stack = [txt]
                    elif re.match(r"^\d+\.", txt):
                        stack = stack[:1] + [txt]
                    elif re.match(r"^[（(]\d+[)）]", txt):
                        stack = stack[:2] + [txt]
                    else:
                        continue
                    continue

                m = CODE_RE.match(txt)
                if not m:
                    continue
                code = m.group(1)
                # 名称：课程号之后、第一个纯数字字段（学分）之前
                rest = txt[len(code):].strip()
                parts = rest.split()
                buf = []
                for p in parts:
                    if CREDIT_RE.match(p):
                        break
                    buf.append(p)
                name = "".join(buf).replace("*", "").strip()
                credits = ""
                for p in parts:
                    if CREDIT_RE.match(p):
                        credits = p
                        break
                cat = normalize_category(stack) if not in_plan_table else None
                if cat is None:
                    continue
                # 同一课号保留信息更全的一条
                prev = courses.get(code)
                if prev is None or len(name) > len(prev[1]):
                    courses[code] = [code, name, credits, cat]
                sections[cat] += 1

    return courses, sections


def major_name_from(file_stem):
    s = file_stem.replace("培养方案", "")
    s = re.sub(r"^2026级?", "", s).strip()
    s = re.sub(r"专业$", "", s).strip()
    return s or file_stem


def main():
    majors = []
    files = []
    for dirpath, _dirnames, filenames in os.walk(ROOT):
        for fn in filenames:
            if fn.lower().endswith(".pdf"):
                files.append(os.path.join(dirpath, fn))
    files.sort()
    print(f"发现 {len(files)} 份 PDF", file=sys.stderr)

    for i, path in enumerate(files, 1):
        rel = os.path.relpath(path, ROOT)
        college = os.path.dirname(rel) or "（校级）"
        stem = os.path.splitext(os.path.basename(rel))[0]
        try:
            courses, sections = parse_pdf(path)
        except Exception as e:
            print(f"  [{i}/{len(files)}] 失败 {rel}: {e}", file=sys.stderr)
            continue
        if not courses:
            print(f"  [{i}/{len(files)}] 无课程 {rel}", file=sys.stderr)
            continue
        majors.append({
            "name": major_name_from(stem),
            "college": college,
            "file": rel,
            "courseCount": len(courses),
            "sections": dict(sections.most_common()),
            "courses": sorted(courses.values(), key=lambda c: (c[3], c[0])),
        })
        print(f"  [{i}/{len(files)}] {major_name_from(stem):<22} {len(courses):>3} 门  {rel}",
              file=sys.stderr)

    kb = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": "浙江大学 2026 级各专业培养方案 PDF",
        "majorCount": len(majors),
        "openPools": [[c, n] for c, n in OPEN_POOLS],
        "majors": majors,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, separators=(",", ":"))

    total = sum(m["courseCount"] for m in majors)
    print(f"\n知识库: {OUT}")
    print(f"专业 {len(majors)} 个 | 课程条目 {total} 条 | 大小 {os.path.getsize(OUT)/1024:.0f} KB")

    # 抽样校验
    print("\n=== 抽样：人工智能 ===")
    for m in majors:
        if m["name"] == "人工智能":
            for c in m["courses"][:8]:
                print(f"  {c[0]:<12} {c[1]:<28} {c[3]}")
            print("  分类统计:", json.dumps(m["sections"], ensure_ascii=False))
            break


if __name__ == "__main__":
    main()
