#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""选出一个不与当天已有迁移包重名的包名。

背景：一天里可能有好几场对话各自要打包，都叫 `迁移包_<日期>` 会互相覆盖，
跨工作区/网盘同步时分不清谁是谁。本脚本扫描全机当天的迁移包，给出可用名。

用法：
    python pick_package_dir.py                      # 今天，自动决定是否需要后缀
    python pick_package_dir.py 2026-09-30           # 指定日期
    python pick_package_dir.py 2026-09-30 模型选型   # 指定主题后缀
    python pick_package_dir.py --list               # 只列出当天已占用的包
    python pick_package_dir.py --plain              # 只输出包名一行（给 shell 用）
    python pick_package_dir.py --root D:/WB         # 换扫描根目录

扫描范围：<root>/*/迁移包_<日期>*   （root 默认 ~/WorkBuddy）
输出：可用的包目录名 + 对应的内层「对话全文」文件名（后缀保持一致）。
"""
import argparse
import datetime
import os
import re
import sys
import unicodedata
from pathlib import Path

PREFIX = "迁移包_"
DATE_RE = re.compile(r"^迁移包_(\d{4}-\d{2}-\d{2})(?:_(.+))?$")

# 允许非 UTF-8 控制台（Windows 中文环境常见 GBK）
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass


def default_root() -> Path:
    home = Path(os.path.expanduser("~"))
    for cand in (home / "WorkBuddy", home / "workbuddy"):
        if cand.is_dir():
            return cand
    return home / "WorkBuddy"


def sanitize(topic: str) -> str:
    """主题词清成安全的文件名片段：去空白/路径符号，保留中英文数字。"""
    t = unicodedata.normalize("NFC", topic).strip()
    t = re.sub(r'[\\/:*?"<>|\s]+', "", t)
    return t[:12]


def scan(root: Path, date_str: str) -> list:
    """返回 [(包目录名, 所在路径)]，含 root 下各工作区以及 root 自身。"""
    found = []
    if not root.is_dir():
        return found
    search_dirs = [root] + [p for p in sorted(root.iterdir()) if p.is_dir()]
    for base in search_dirs:
        try:
            entries = list(base.iterdir())
        except OSError:
            continue
        for p in entries:
            if not p.is_dir():
                continue
            m = DATE_RE.match(p.name)
            if m and m.group(1) == date_str:
                found.append((p.name, p))
    return found


def pick(root: Path, date_str: str, topic: str = "") -> tuple:
    taken = {name for name, _ in scan(root, date_str)}
    base = f"{PREFIX}{date_str}"

    if topic:
        stem = f"{base}_{sanitize(topic)}"
        cand = stem
        n = 2
        while cand in taken:
            cand = f"{stem}_{n}"
            n += 1
    else:
        if base not in taken:
            cand = base
        else:
            n = 2
            cand = f"{base}_{n}"
            while cand in taken:
                n += 1
                cand = f"{base}_{n}"

    suffix = cand[len(base):]  # "" 或 "_模型选型" 或 "_2"
    doc = f"对话全文_{date_str}{suffix}.md"
    return cand, doc, taken


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("date", nargs="?", default=datetime.date.today().isoformat(),
                    help="目标日期 YYYY-MM-DD，默认今天")
    ap.add_argument("topic", nargs="?", default="", help="主题后缀（2-4 字），可省略")
    ap.add_argument("--root", default="", help="扫描根目录，默认 ~/WorkBuddy")
    ap.add_argument("--plain", action="store_true", help="只输出包名")
    ap.add_argument("--list", action="store_true", help="只列出已占用的包")
    args = ap.parse_args()

    date_str = args.date
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        print(f"日期格式应为 YYYY-MM-DD，收到：{date_str}", file=sys.stderr)
        return 2

    root = Path(args.root) if args.root else default_root()
    cand, doc, taken = pick(root, date_str, args.topic)

    if args.list:
        if not taken:
            print(f"{date_str} 当天没有已存在的迁移包（扫描根：{root}）")
        else:
            print(f"{date_str} 当天已占用 {len(taken)} 个包（扫描根：{root}）：")
            for name, path in sorted(scan(root, date_str)):
                print(f"  {name}   ← {path}")
        return 0

    if args.plain:
        print(cand)
        return 0

    print(f"扫描根目录 : {root}")
    print(f"目标日期   : {date_str}")
    if taken:
        print(f"已占用     : {len(taken)} 个")
        for name, path in sorted(scan(root, date_str)):
            print(f"             {name}  ← {path}")
    else:
        print("已占用     : 无（当天第一个包，可用基础名）")
    print(f"可用包名   : {cand}")
    print(f"内层全文   : {doc}")
    if cand != f"{PREFIX}{date_str}":
        print("提示       : 已加后缀。若此刻能提炼出主题词，"
              f"建议改用 `python pick_package_dir.py {date_str} <主题>` 重新取一个更易读的名字。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
