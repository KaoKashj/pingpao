#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""集中配置：所有路径与外部模块加载都在这里，脚本里不要再写绝对路径。

## 为什么需要这个文件

原来 12 个脚本里各自硬编码了 `~/Desktop/...`、`~/Documents/ChatGPT/选课/...`，
换个机器、换个目录就跑不起来。现在全部收敛到这里，**用环境变量覆盖即可移植**。

## 用法

    from config import load_jwglxt, PLAN_TSV, PROJECT_DIR, TMP_DIR, PDF_DEFAULT

    mod = load_jwglxt()                       # 加载登录模块（替代 importlib 样板）
    j = mod.Jwglxt(*mod.get_credentials())
    if not j.login():
        raise SystemExit("登录失败")

## 可覆盖的环境变量

| 变量 | 作用 | 默认值 |
|---|---|---|
| `ZJU_JWGLXT_MODULE` | 登录模块 `zju_jwglxt.py` 的路径 | `~/.codex/skills/zju-jwglxt/scripts/zju_jwglxt.py` |
| `COURSEFIT_PROJECT` | 本项目的输出目录 | `~/Documents/ChatGPT/选课` |
| `COURSEFIT_TMP` | 中间产物目录 | 系统临时目录下的 `coursefit/` |
| `COURSEFIT_PDF` | 培养方案 PDF | 空（必须指定，见下） |

凭据**不在这里**——由登录模块自己从环境变量
`ZJU_JWGLXT_USERNAME`/`ZJU_JWGLXT_PASSWORD` 或 `~/.config/zju-jwglxt/credentials.json` 读取。
"""
import importlib.util
import os
import sys
import tempfile

__all__ = [
    "PROJECT_DIR", "TMP_DIR", "JWGLXT_MODULE", "PDF_PATH",
    "PLAN_TSV", "CATALOG_JSON", "PDF_PATH_DEFAULT", "PLAN_PDF_DIR", "KB_JSON",
    "path", "tmp", "load_jwglxt", "require_pdf", "jwglxt_path",
]

# ---- 目录 ----------------------------------------------------------------

#: 项目输出目录（TSV / Excel / Markdown 落在这里）
PROJECT_DIR = os.path.abspath(
    os.path.expanduser(os.environ.get("COURSEFIT_PROJECT", "~/Documents/ChatGPT/选课")))

#: 中间产物目录（原来是写死 /tmp/xxx.json）
TMP_DIR = os.path.abspath(os.path.expanduser(
    os.environ.get("COURSEFIT_TMP", os.path.join(tempfile.gettempdir(), "coursefit"))))

# ---- 外部登录模块 --------------------------------------------------------

#: 教务系统登录模块（不在本仓库内，需要用户自备）
JWGLXT_MODULE = os.path.abspath(os.path.expanduser(
    os.environ.get("ZJU_JWGLXT_MODULE",
                   "~/.codex/skills/zju-jwglxt/scripts/zju_jwglxt.py")))

# ---- 培养方案 PDF --------------------------------------------------------

#: 默认路径。**换机器基本都要改**，所以优先用 COURSEFIT_PDF 覆盖。
PDF_PATH_DEFAULT = os.path.expanduser(
    "~/Desktop/浙江大学/浙江大学2026级培养方案PDF/计算机科学与技术学院/2026级人工智能专业培养方案.pdf")

#: 实际使用的 PDF 路径（COURSEFIT_PDF 优先）
PDF_PATH = os.path.expanduser(os.environ.get("COURSEFIT_PDF", PDF_PATH_DEFAULT))

#: 培养方案 PDF 总目录（131 个专业，用于 build_kb.py 建知识库）
PLAN_PDF_DIR = os.path.abspath(os.path.expanduser(
    os.environ.get("COURSEFIT_PLAN_DIR",
                   "~/Desktop/浙江大学/浙江大学2026级培养方案PDF")))

#: 知识库（131 个专业的带课号课程，由 build_kb.py 生成）
KB_JSON = os.path.join(PROJECT_DIR, "kb.json")


# ---- 本项目内部的产物路径 -------------------------------------------------

PLAN_TSV = os.path.join(PROJECT_DIR, "培养方案课程清单.tsv")
CATALOG_JSON = os.path.join(TMP_DIR, "jwglxt_catalog.json")


# ---- 工具函数 ------------------------------------------------------------

def path(*parts):
    """拼一个项目内路径：path("周五课程结果.xlsx")"""
    return os.path.join(PROJECT_DIR, *parts)


def tmp(*parts):
    """拼一个中间产物路径：tmp("jwglxt_catalog.json")"""
    return os.path.join(TMP_DIR, *parts)


def jwglxt_path():
    """返回登录模块路径字符串（用于替换脚本里写死的长路径）。"""
    return JWGLXT_MODULE


def pdf_path():
    """返回培养方案 PDF 路径（不存在时抛出可读错误）。"""
    return require_pdf()


def load_jwglxt():
    """加载并返回登录模块（替代各脚本里 4 行 importlib 样板）。

    失败时给出**可操作的**报错，而不是让用户猜。
    """
    if not os.path.exists(JWGLXT_MODULE):
        sys.exit(
            "找不到教务登录模块：\n"
            f"  {JWGLXT_MODULE}\n\n"
            "本项目不含登录逻辑（避免账号密码进版本控制）。你需要自己提供一份\n"
            "zju_jwglxt.py，暴露 get_credentials() 与 class Jwglxt（含 login/req/course_context）。\n\n"
            "然后用环境变量指向它：\n"
            "  export ZJU_JWGLXT_MODULE=/你的路径/zju_jwglxt.py\n\n"
            "详见 README 的「⚠️ 运行前提」一节。")

    spec = importlib.util.spec_from_file_location("zju_jwglxt", JWGLXT_MODULE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def require_pdf():
    """返回培养方案 PDF 路径；不存在时给出可操作的报错。"""
    if not os.path.exists(PDF_PATH):
        sys.exit(
            "找不到培养方案 PDF：\n"
            f"  {PDF_PATH}\n\n"
            "请用环境变量指向你下载的培养方案 PDF：\n"
            "  export COURSEFIT_PDF=/你的路径/2026级XXX专业培养方案.pdf\n\n"
            "（培养方案可在教务网或学院网站下载）")
    return PDF_PATH


def ensure_dirs():
    """确保输出目录存在。"""
    for d in (PROJECT_DIR, TMP_DIR):
        os.makedirs(d, exist_ok=True)
