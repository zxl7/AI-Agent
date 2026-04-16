#!/usr/bin/env python3
"""
查询涨停股所属题材/概念板块，并按题材出现频次聚合（过滤通用标签）
"""
import urllib.request
import json
import ssl
from collections import Counter

BASE = "https://api.biyingapi.com"
TOKEN = "60D084A7-FF4A-4B42-9E1C-45F0B719F33C"
DATE = "2026-04-16"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def api(path):
    url = f"{BASE}/{path}/{TOKEN}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return json.loads(r.read())

zt_data = api(f"hslt/ztgc/{DATE}")
zt_list = zt_data if isinstance(zt_data, list) else (zt_data.get("data", []) if isinstance(zt_data, dict) else [])
zt_list = [s for s in zt_list if 'ST' not in s.get('mc', '') and '*' not in s.get('mc', '')]

print(f"涨停池共 {len(zt_list)} 只（非ST）\n")

# 过滤掉通用标签，只保留真正的题材
EXCLUDE_PREFIXES = (
    'A股-分类', 'A股-指数成分', 'A股-证监会行业',
    'A股-申万行业', 'A股-申万二级', 'A股-地域板块',
    '基金-', '港股-', '美股-'
)

def fetch_theme(stock):
    dm = stock.get('dm', '')
    mc = stock.get('mc', '')
    try:
        raw = api(f"hszg/zg/{dm}")
        if isinstance(raw, dict):
            data = raw.get('data', []) or raw.get('result', []) or []
        elif isinstance(raw, list):
            data = raw
        else:
            data = []

        themes = []
        for item in data:
            if isinstance(item, dict):
                name = item.get('name') or item.get('mc') or item.get('plate') or item.get('idea') or ''
                if name and not any(name.startswith(p) for p in EXCLUDE_PREFIXES):
                    themes.append(name)
            elif isinstance(item, str) and item and not any(item.startswith(p) for p in EXCLUDE_PREFIXES):
                themes.append(item)
        return mc, dm, themes
    except Exception as e:
        return mc, dm, []

from concurrent.futures import ThreadPoolExecutor, as_completed

theme_counter = Counter()
stock_themes = {}
theme_stocks = {}

with ThreadPoolExecutor(max_workers=15) as pool:
    futures = {pool.submit(fetch_theme, s): s for s in zt_list}
    for i, fut in enumerate(as_completed(futures), 1):
        mc, dm, themes = fut.result()
        stock_themes[mc] = themes
        seen = set()
        for t in themes:
            if t and t not in seen:
                theme_counter[t] += 1
                seen.add(t)
                if t not in theme_stocks:
                    theme_stocks[t] = []
                theme_stocks[t].append(mc)

print("=" * 65)
print("  📊 涨停股题材分布（TOP25）— 2026-04-16")
print("=" * 65)

top = theme_counter.most_common(25)
max_theme_len = max(len(t) for t, _ in top)

for rank, (theme, cnt) in enumerate(top, 1):
    bar_len = min(cnt * 2, 40)
    bar = '█' * bar_len
    pct = cnt / len(zt_list) * 100
    stocks = theme_stocks.get(theme, [])
    # 标注有连板的个股
    board_marks = []
    for s in zt_list:
        if s['mc'] in stocks and s.get('lbc', 1) > 1:
            board_marks.append(f"{s['mc']}({s['lbc']}板)")
    board_str = " | 连板→" + " ".join(board_marks[:5]) if board_marks else ""
    print(f" {rank:2d}. {theme:<{max_theme_len}}  {bar:<40s} {cnt:2d}只({pct:4.1f}%){board_str}")

print("\n" + "=" * 65)
print("  🏆 核心龙头题材 — 涨停股明细")
print("=" * 65)

# 重点题材深度展开（TOP5）
for theme, cnt in top[:5]:
    stocks = theme_stocks.get(theme, [])
    print(f"\n▶ {theme}  ({cnt}只涨停)")
    print("  " + "-" * 50)
    members = [(s['mc'], s.get('lbc', 1), s.get('p', 0), s.get('zf', 0))
               for s in zt_list if s['mc'] in stocks]
    members.sort(key=lambda x: (-x[1], -x[3]))  # 优先按连板数，再按涨幅
    for mc, lbc, p, zf in members:
        tag = f"  🔥{lbc}板" if lbc > 1 else "  ⭐首板"
        print(f"    {mc:<10s}{tag}  {p:>8.2f}元  涨幅{zf:>6.2f}%")
