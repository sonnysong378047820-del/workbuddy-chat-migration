#!/usr/bin/env python3
"""从 WorkBuddy 本机原始会话库提取对话全文（字节级保真）。

用法：
    python extract_session.py                      # 自动定位当前工作区最新会话
    python extract_session.py <session.jsonl>      # 指定会话文件
    python extract_session.py <session.jsonl> <out.md>

会话库位置：
    ~/.workbuddy/projects/<工作区路径转义>/*.jsonl
    转义规则：C:\\Users\\sonny\\WorkBuddy\\2026-09-29-13-18-03
           -> c-Users-sonny-WorkBuddy-2026-09-29-13-18-03
           （盘符小写，反斜杠与冒号换成连字符）

事件类型（每行一个 JSON）：
    message | function_call | function_call_result | reasoning
    | file-history-snapshot | session-meta | ai-title
"""
import json
import os
import re
import sys
import glob
import time
import datetime


def slugify(workspace: str) -> str:
    """工作区绝对路径 -> projects 目录名。

    C:\\Users\\sonny\\WorkBuddy\\2026-09-29-13-18-03
      -> c-Users-sonny-WorkBuddy-2026-09-29-13-18-03
    """
    p = os.path.abspath(workspace)
    p = p.replace(':', '')                 # 去掉盘符冒号
    if p:
        p = p[0].lower() + p[1:]           # 盘符小写
    p = p.replace('\\', '-').replace('/', '-')
    return p.strip('-')


def find_session(workspace=None):
    """定位工作区下最新的 .jsonl 会话文件。"""
    workspace = workspace or os.getcwd()
    root = os.path.join(os.path.expanduser('~'), '.workbuddy', 'projects')
    cand = os.path.join(root, slugify(workspace))
    if not os.path.isdir(cand):
        avail = sorted(os.path.basename(d) for d in glob.glob(os.path.join(root, '*'))
                       if os.path.isdir(d))
        near = [a for a in avail if a.startswith(slugify(workspace)[:24])]
        hint = ('\n相近目录: ' + ', '.join(near)) if near else ''
        raise SystemExit(f'找不到会话目录: {cand}{hint}')
    files = [f for f in glob.glob(os.path.join(cand, '*.jsonl'))]
    if not files:
        raise SystemExit(f'会话目录里没有 .jsonl: {cand}')
    return max(files, key=os.path.getmtime)


def txt_of(content):
    if isinstance(content, str):
        return content
    out = []
    for c in content or []:
        if isinstance(c, dict) and c.get('type') in ('input_text', 'output_text', 'text'):
            out.append(c.get('text', ''))
    return '\n'.join(out)


def clean_user(t):
    """剥离系统注入块，只留用户原话。"""
    m = re.search(r'<user_query>(.*?)</user_query>', t, re.S)
    if m:
        return m.group(1).strip()
    t = re.sub(r'<system-reminder.*?</system-reminder>', '', t, flags=re.S)
    return t.strip()


def hhmmss(ms):
    return datetime.datetime.fromtimestamp(ms / 1000).strftime('%H:%M:%S')


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else ''
    if not src or src == '-':
        src = find_session()
    out = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else os.path.join(
        os.getcwd(), f'对话全文_{time.strftime("%Y-%m-%d")}.md')

    msgs = []
    with open(src, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get('type') == 'message' and d.get('role') in ('user', 'assistant'):
                msgs.append(d)

    turns = []
    cur = None
    for m in msgs:
        when = hhmmss(m.get('timestamp', 0))
        body = txt_of(m.get('content'))
        if m['role'] == 'user':
            cur = {'u': clean_user(body), 'ut': when, 'a': []}
            turns.append(cur)
        elif cur is not None and body.strip():
            cur['a'].append(body.strip())

    L = ['# 对话全文', '',
         f'> **来源**：本机原始会话记录 `{src}`',
         '> **提取方式**：直接解析系统 JSONL 会话库，**文本字节级保真**（emoji / markdown / 链接原样保留）。',
         f'> **会话 ID**：{os.path.basename(src).replace(".jsonl", "")}',
         '', '**说明**：用户消息中的系统注入块已剥离，只保留用户实际说过的话。', '',
         '---', '']
    for i, t in enumerate(turns, 1):
        L += [f'## 第 {i} 轮', '', f'### 👤 我（{t["ut"]}）', '', t['u'] or '（无文字，见图片）', '',
              '### 🤖 助手', '']
        L += [x for a in t['a'] for x in (a, '')] or ['（本轮无文字回复）', '']
        L += ['---', '']

    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))

    print(f'写出: {out}')
    print(f'轮次: {len(turns)}　字节: {os.path.getsize(out):,}')


if __name__ == '__main__':
    main()
