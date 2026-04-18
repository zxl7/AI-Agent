#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短线复盘HTML报告生成器 v4 (ECharts版)
严格按照 /Users/zxl/Desktop/短线复盘利器-优化版.html 模板结构输出
"""

import json, urllib.request, time, sys, datetime, os

TOKEN = "60D084A7-FF4A-4B42-9E1C-45F0B719F33C"
DATE = sys.argv[1] if len(sys.argv) > 1 else "2026-04-17"
BASE = "https://api.biyingapi.com"

# ── 噪音过滤 ──
NOISE_PREFIXES = ('A股-分类', 'A股-指数成分', 'A股-证监会行业', 'A股-申万行业',
                   'A股-申万二级', 'A股-地域板块', '基金-', '港股-', '美股-', 'A股-概念板块')
NOISE_THEMES = {'小盘', '中盘', '大盘', '融资融券', 'QFII持股', '基金重仓',
                '年度强势', '深股通', '沪股通', '富时罗素'}

def clean_theme(name):
    if not name: return None
    for p in NOISE_PREFIXES:
        if name.startswith(p): return None
    if name.startswith('A股-热门概念-'):
        return name.replace('A股-热门概念-', '')
    return name

def api(path):
    url = f"{BASE}/{path}/{TOKEN}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def api_get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

print("=" * 50)
print("📊 数据采集开始")
print("=" * 50)

# ══════════════════════════
# ① 四大指数
# ══════════════════════════
print("\n[1/12] 获取四大指数...")
indices_data = []
for code, name in [("000001.SH","上证指数"), ("399001.SZ","深证成指"),
                    ("399006.SZ","创业板指"), ("000688.SH","科创50")]:
    try:
        d = api_get(f"{BASE}/hsindex/latest/{code}/d/{TOKEN}?lt=5")
        k = d[-1] if isinstance(d, list) and len(d) > 0 else {}
        prev = d[-2] if isinstance(d, list) and len(d) > 1 else {}
        close = k.get('c', 0)
        prev_close = prev.get('c', k.get('pc', 0))
        chg_pct = (close - prev_close) / prev_close * 100 if prev_close else 0
        vol_a = k.get('a', 0)  # 成交额
        indices_data.append({
            'name': name, 'code': code,
            'close': close, 'pct': chg_pct,
            'vol': vol_a, 'up': chg_pct >= 0
        })
        print(f"   {name}: {close:.2f} ({chg_pct:+.2f}%)")
    except Exception as e:
        print(f"   {name} ERROR: {e}")

# 两市总量能 = 上证+深证成交额
total_vol_sh = indices_data[0]['vol'] if len(indices_data) > 0 else 0
total_vol_sz = indices_data[1]['vol'] if len(indices_data) > 1 else 0
today_total_vol = (total_vol_sh + total_vol_sz) / 1e8  # 亿
print(f"   两市合计: {today_total_vol:.2f}亿")

# ══════════════════════════
# ② 市场全景(涨停/炸板/跌停)
# ══════════════════════════
print("\n[2/12] 获取市场全景...")
zt_all = api(f"hslt/ztgc/{DATE}")
dt_all = api(f"hslt/dtgc/{DATE}")
zb_all = api(f"hslt/zbgc/{DATE}")
qs_all = api(f"hslt/qsgc/{DATE}")  # 强势股池

zt_count = len(zt_all)
dt_count = len(dt_all)
zb_count = len(zb_all)
qs_count = len(qs_all) if qs_all else 0
fb_rate = zt_count / (zt_count + zb_count) * 100 if (zt_count + zb_count) > 0 else 0
zb_rate = zb_count / (zt_count + zb_count) * 100 if (zt_count + zb_count) > 0 else 0

print(f"   涨停:{zt_count} 炸板:{zb_count} 跌停:{dt_count} 封板率:{fb_rate:.1f}%")

# 涨停总成交额
zt_total_cje = sum(s.get('cje', 0) for s in zt_all) / 1e8

# ══════════════════════════
# ③ 近5日量能趋势（取最近K线数据）
# ══════════════════════════
print("\n[3/12] 获取近5日量能...")

def fetch_index_klines(code, n=5):
    """获取指数最近n根K线，返回 {日期: 成交额} 字典"""
    try:
        d = api_get(f"{BASE}/hsindex/latest/{code}/d/{TOKEN}?lt={n}")
        if isinstance(d, list):
            result = {}
            for k in d:
                dt_str = k.get('t', '')  # '2026-04-10 00:00:00'
                date_key = dt_str[:10] if len(dt_str) >= 10 else dt_str
                vol_a = k.get('a', 0)   # 成交额
                result[date_key] = vol_a
            return result
        return {}
    except Exception as e:
        print(f"   {code} K线获取失败: {e}")
        return {}

def get_trading_days(n=7):
    k_days = 5 if n > 5 else n
    sh = fetch_index_klines("000001.SH", k_days) or {}
    sz = fetch_index_klines("399001.SZ", k_days) or {}
    result = sorted(set(list(sh.keys()) + list(sz.keys())))
    if len(result) < n:
        today = datetime.date.today()
        for delta in range(1, 14):
            if len(result) >= n: break
            check = (today - datetime.timedelta(days=delta)).strftime("%Y-%m-%d")
            if check in result: continue
            try:
                z = api(f"hslt/ztgc/{check}")
                if isinstance(z, list) and len(z) > 0: result.append(check)
            except: pass
    return sorted(result)

# 取上证和深证最近5日K线
sh_d = fetch_index_klines("000001.SH", 5)
sz_d = fetch_index_klines("399001.SZ", 5)

# 取K线自动过滤后的真实交易日
all_dates = get_trading_days(5)
recent5_dates = all_dates[-5:]
vol_history = []
prev_v = None
for d in recent5_dates:
    sh_v = sh_d.get(d, 0)
    sz_v = sz_d.get(d, 0)
    total = (sh_v + sz_v) / 1e8
    chg = (total - prev_v) / prev_v * 100 if prev_v else 0
    vol_history.append({'date': d[5:].replace('-', ''), 'vol': total, 'chg': chg})
    prev_v = total

for v in vol_history:
    print(f"   {v['date']}: {v['vol']:.0f}亿 ({v['chg']:+.1f}%)")


for v in vol_history:
    print(f"   {v['date']}: {v['vol']:.0f}亿")

# 计算较昨日变化
if len(vol_history) >= 2:
    yest_vol = vol_history[-2]['vol']
    today_v = vol_history[-1]['vol']
    vol_chg_pct = (today_v - yest_vol) / yest_vol * 100 if yest_vol else 0
    vol_diff = today_v - yest_vol
else:
    vol_chg_pct = 0
    vol_diff = 0

# ══════════════════════════
# ④ 连板天梯 & 昨日晋级分析
# ══════════════════════════
print("\n[4/12] 分析连板天梯...")
by_lbc = {}
for s in zt_all:
    lb = s.get('lbc', 1)
    by_lbc.setdefault(lb, []).append(s)
for k in by_lbc:
    by_lbc[k].sort(key=lambda x: x.get('zf', 0), reverse=True)

max_lb = max(by_lbc.keys()) if by_lbc else 1
ladder_rows = []
for lb in sorted(by_lbc.keys(), reverse=True):
    if lb == 1:
        continue  # 跳过首板，只显示2板及以上连板
    for s in by_lbc[lb]:
        ladder_rows.append({
            'badge': lb,
            'name': s.get('mc', ''),
            'code': s.get('dm', ''),
            'zf': s.get('zf', 0),
            'note': ''
        })

# 昨日连板股今日是否存活
print("   获取昨日数据对比晋级...")
yest_zt = []
try:
    # 从 all_dates 寻找昨日
    yest_date = None
    for i, d in enumerate(all_dates):
        if d == DATE and i > 0:
            yest_date = all_dates[i-1]
            break
    if not yest_date:
        # 如果 DATE 不在 all_dates 中，找比 DATE 小的最大日期
        past_dates = [d for d in all_dates if d < DATE]
        if past_dates: yest_date = past_dates[-1]
    
    if yest_date:
        print(f"   昨日交易日: {yest_date}")
        yest_zt = api(f"hslt/ztgc/{yest_date}")
    else:
        print("   警告: 无法确定昨日交易日")
except Exception as e:
    print(f"   获取昨日数据失败: {e}")

yest_lb_stocks = {}  # code -> {lbc, mc}
for s in yest_zt:
    lbc = s.get('lbc', 1)
    if lbc >= 2:
        yest_lb_stocks[s['dm']] = {'lbc': lbc, 'mc': s.get('mc', '')}

today_lb_codes = set()
for row in ladder_rows:
    if row['badge'] >= 2:
        today_lb_codes.add(row['code'])

jinwei_list = []  # 晋级成功
duanban_list = []  # 断板
for code, info in yest_lb_stocks.items():
    if code in today_lb_codes:
        jinwei_list.append(info)
    else:
        duanban_list.append(info)

jj_rate = len(jinwei_list) / len(yest_lb_stocks) * 100 if yest_lb_stocks else 0

# 首板晋级率: 昨日首板(lbc=1)中今日晋级到2板+
yest_1b_codes = set(s['dm'] for s in yest_zt if s.get('lbc', 1) == 1)
jinwei_from_1b = [c for c in today_lb_codes if c in yest_1b_codes]
jj_1b_rate = len(jinwei_from_1b) / len(yest_1b_codes) * 100 if yest_1b_codes else 0

# 标记天梯状态
for row in ladder_rows:
    code = row['code']
    if code in yest_lb_stocks:
        row['status'] = '晋级'
    elif code in yest_1b_codes and row['badge'] == 2:
        row['status'] = '新晋'
    elif row['badge'] == 1:
        row['status'] = '首板'
    else:
        row['status'] = '新晋'

# 最高板标记 👑
if ladder_rows:
    ladder_rows[0]['name'] = f"👑 {ladder_rows[0]['name']}"

print(f"   天梯: 最高{max_lb}板, 共{len(ladder_rows)}只连板")
print(f"   昨日{len(yest_lb_stocks)}只连板→存活{len(jinwei_list)}只({jj_rate:.0f}%)")
print(f"   断板: {', '.join([s['mc']+f'({s['lbc']}板)' for s in duanban_list[:8]])}")

# ══════════════════════════
# ⑤ 近7日高度趋势
# ══════════════════════════
print("\n[5/12] 获取近7日高度趋势...")
his_dates = get_trading_days(7)
height_trend = {'dates': [], 'main': [], 'sub': [], 'gem': [], 'labels_main': [], 'labels_sub': [], 'labels_gem': []}

for d in his_dates:
    try:
        data = api(f"hslt/ztgc/{d}")
        lbs = [s.get('lbc', 1) for s in data]
        main_max = max(lbs) if lbs else 0
        # 创业板20cm最高
        gem_data = [s for s in data if s.get('dm','').startswith('300')]
        gem_max = max((s.get('lbc', 1) for s in gem_data), default=0)
        # 次高
        sorted_lb = sorted(set(lbs), reverse=True)
        sub_max = sorted_lb[1] if len(sorted_lb) > 1 else 0
        
        # 标注各系列名称
        top_stock = max(data, key=lambda x: x.get('lbc', 0), default={})
        top_name = top_stock.get('mc', '')[:4] if top_stock else ''
        
        sub_stock = next((s for s in data if s.get('lbc') == sub_max), {})
        sub_name = sub_stock.get('mc', '')[:4] if sub_stock else ''
        
        gem_stock = max(gem_data, key=lambda x: x.get('lbc', 0), default={}) if gem_data else {}
        gem_name = gem_stock.get('mc', '')[:4] if gem_stock else ''
        
        height_trend['dates'].append(d[5:])
        height_trend['main'].append(main_max)
        height_trend['sub'].append(sub_max)
        height_trend['gem'].append(gem_max)
        height_trend['labels_main'].append(top_name if main_max >= 3 else '')
        height_trend['labels_sub'].append(sub_name if sub_max >= 2 else '')
        height_trend['labels_gem'].append(gem_name if gem_max >= 1 else '')
        
        print(f"   {d[5:]}: 主板{main_max}板({top_name}) 次高{sub_max}({sub_name}) 创板{gem_max}板({gem_name})")
        time.sleep(0.03)
    except Exception as e:
        height_trend['dates'].append(d[5:])
        height_trend['main'].append(0)
        height_trend['sub'].append(0)
        height_trend['gem'].append(0)
        height_trend['labels_main'].append('')
        height_trend['labels_sub'].append('')
        height_trend['labels_gem'].append('')
        print(f"   {d[5:]}: error {e}")

# ══════════════════════════
# ⑥ 题材聚合(每只涨停股查询)
# ══════════════════════════
print("\n[6/12] 聚合题材数据(逐票查询，耗时较长)...")
theme_count = {}      # theme -> count
theme_stocks = {}     # theme -> [names]
zb_theme_count = {}   # 炸板题材

def query_themes(stock_list, target_dict):
    """批量查询股票题材"""
    print(f"   准备查询 {len(stock_list)} 只股票题材...")
    for i, s in enumerate(stock_list):
        code = s['dm']
        name = s.get('mc', code)
        try:
            url = f"{BASE}/hszg/zg/{code}/{TOKEN}"
            req = urllib.request.Request(url)
            # 缩短超时时间到5秒
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
            if isinstance(data, list):
                for item in data:
                    t = clean_theme(item.get('name', ''))
                    if t and t not in NOISE_THEMES:
                        target_dict[t] = target_dict.get(t, 0) + 1
                        # 确保存储的是名称而非代码
                        if name not in theme_stocks.get(t, []):
                            theme_stocks.setdefault(t, []).append(name)
            if (i + 1) % 10 == 0:
                print(f"   已处理 {i+1}/{len(stock_list)}...")
            time.sleep(0.01)
        except Exception as e:
            # print(f"   查询 {code} 失败: {e}")
            pass

# 查询涨停股题材
query_themes(zt_all, theme_count)

# 查询炸板股题材
if zb_all:
    print(f"   准备查询 {len(zb_all)} 只炸板股题材...")
    query_themes(zb_all, zb_theme_count)

# 过滤掉噪音题材和"昨日涨停"
real_themes = [item for item in theme_count.items() if item[0] != "昨日涨停"]
real_themes = sorted(real_themes, key=lambda x: -x[1])
print(f"   有效题材: {len(real_themes)} 个")
for t, c in real_themes[:10]:
    print(f"   · {t}: {c}只 ({', '.join(theme_stocks.get(t, [])[:4])})")

# ══════════════════════════
# ⑦ 大面股 / 核按钮 (跌停池)
# ══════════════════════════
print("\n[7/12] 大面股分析...")
big_face = []  # -5%以下的大面股
for s in dt_all:
    zf = s.get('zf', 0)
    if zf <= -9.5 or zf <= -5:
        big_face.append({
            'name': s.get('mc', ''), 'code': s.get('dm', ''),
            'zf': zf, 'p': s.get('p', 0)
        })

# 从强势股池找大面(-5%以下)
big_face_from_qs = []
if qs_all:
    for s in qs_all:
        zf = s.get('zf', 0)
        if zf <= -5:
            big_face_from_qs.append({
                'name': s.get('mc', ''), 'code': s.get('dm', ''),
                'zf': zf, 'p': s.get('p', 0)
            })

all_big_faces = big_face + big_face_from_qs
print(f"   大面股(-5%↓): {len(all_big_faces)}只")
for b in all_big_faces[:5]:
    print(f"   · {b['name']} {b['zf']:.2f}%")

# ══════════════════════════
# ⑧ 成交额TOP10 (全市场)
# ══════════════════════════
print("\n[8/12] 成交额TOP10...")

# 合并涨停池和强势股池取TOP10
all_stocks_for_top10 = []
for s in zt_all:
    all_stocks_for_top10.append({
        'mc': s.get('mc', ''), 'dm': s.get('dm', ''),
        'zf': s.get('zf', 0), 'cje': s.get('cje', 0),
        'source': 'zt'
    })
if qs_all:
    for s in qs_all:
        all_stocks_for_top10.append({
            'mc': s.get('mc', ''), 'dm': s.get('dm', ''),
            'zf': s.get('zf', 0), 'cje': s.get('cje', 0),
            'source': 'qs'
        })

# 去重(优先用zt)
seen = set()
unique_stocks = []
for s in all_stocks_for_top10:
    if s['dm'] not in seen:
        seen.add(s['dm'])
        unique_stocks.append(s)

unique_stocks.sort(key=lambda x: x.get('cje', 0), reverse=True)
top10 = unique_stocks[:10]

print(f"   TOP1: {top10[0]['mc']} {top10[0]['cje']/1e8:.0f}亿")
top10_total = sum(t['cje'] for t in top10) / 1e8

# 为TOP10查板块
print("   查询TOP10题材...")
top10_with_theme = []
for t in top10:
    themes_for_this = []
    try:
        req = urllib.request.Request(f"{BASE}/hszg/zg/{t['dm']}/{TOKEN}")
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        if isinstance(data, list):
            for item in data:
                ct = clean_theme(item.get('name', ''))
                if ct and ct not in NOISE_THEMES:
                    themes_for_this.append(ct)
        time.sleep(0.03)
    except:
        pass
    top10_with_theme.append({
        **t,
        'sector': themes_for_this[0] if themes_for_this else '未知'
    })

for t in top10_with_theme[:5]:
    print(f"   {t['mc']} {t['zf']:+.2f}% {t['cje']/1e8:.0f}亿 [{t['sector']}]")

# ══════════════════════════
# ⑨ 昨日涨停今表现(qsgc)
# ══════════════════════════
print("\n[9/12] 昨日涨停今表现...")
# qsgc是今日强势股池，里面包含昨日涨停今涨幅分布
avg_zf_qs = 0
best_qs = []
worst_qs = []
if qs_all:
    zs = [(s.get('zf', 0), s.get('mc', '')) for s in qs_all]
    zs.sort(key=lambda x: x[0], reverse=True)
    avg_zf_qs = sum(z[0] for z in zs) / len(zs) if zs else 0
    best_qs = zs[:5]
    worst_qs = zs[-5:] if len(zs) >= 5 else zs
    print(f"   强势股均涨: {avg_zf_qs:+.2f}%")
    print(f"   最佳: {best_qs[0][1]} {best_qs[0][0]:+.2f}%")
    print(f"   最差: {worst_qs[0][1]} {worst_qs[0][0]:+.2f}%")

# ══════════════════════════
# ⑩ 综合判断计算
# ══════════════════════════
print("\n[10/12] 计算综合判断...")

# 赚钱效应四维
first_board = len([s for s in zt_all if s.get('lbc', 1) == 1])
link_board = len([s for s in zt_all if s.get('lbc', 1) >= 2])
ratio_fb = first_board / link_board if link_board > 0 else first_board

effect_ratio_val = f"{int(jj_1b_rate)}%"
effect_ratio_detail = f"(昨日首板{len(yest_1b_codes)}只→今晋级{len(jinwei_from_1b)}只)"
effect_prop_val = f"{first_board}:{link_board}" if link_board > 0 else f"{first_board}:0"
effect_prop_detail = f"(首板{first_board},连板{link_board})"

# 梯队完整度
lb_levels = sorted(by_lbc.keys(), reverse=True)
ladder_str = '→'.join(str(lb) for lb in lb_levels[:4]) if len(lb_levels) >= 2 else str(max_lb)
effect_ladder_val = ladder_str
effect_ladder_detail = f"(最高{max_lb}板)"

limit_ratio = f"{zt_count}:{dt_count}" if dt_count > 0 else str(zt_count)
limit_ratio_detail = f"({zt_count/dt_count:.1f}:1)" if dt_count > 0 else "(无跌停)"

# verdict
if zt_count >= 70 and fb_rate >= 75 and jj_rate >= 40:
    effect_verdict_type = "good"
    effect_verdict_title = "📋 综合判断：大涨高潮日，赚钱效应极好。"
    effect_verdict_detail = (
        f"四大指数全红{'（创业板最强）' if any(i['name']=='创业板指' and i['pct']>2 for i in indices_data) else ''}，"
        f"封板率{fb_rate:.0f}%创近期高点，晋级率{jj_rate:.0f}%。当前是出手时机，但注意高潮次日分化风险。"
    )
elif zt_count >= 50 and fb_rate >= 65:
    effect_verdict_type = "warn"
    effect_verdict_title = "📋 综合判断：冰点修复期，赚钱效应偏弱但结构性机会存在。"
    effect_verdict_detail = (
        f"今日连板梯队完整度尚可（{max_lb}板龙头存活），但高位股断板率高，分歧较大。操作上以低位首板为主，高位接力需谨慎。"
    )
else:
    effect_verdict_type = "fire"
    effect_verdict_title = "📋 综合判断：情绪冰点期，亏钱效应明显。"
    effect_verdict_detail = (
        f"涨停数不足{zt_count}只，封板率仅{fb_rate:.0f}%，建议空仓观望或极轻仓试错。"
    )

# 恐惧指标评级
bf_count = len(all_big_faces)  # typo fix below
if bf_count <= 2 and dt_count <= 2:
    fear_risk = "极低"
    fear_risk_note = "亏钱效应极小"
    risk_color = "green-text"
elif bf_count <= 5 and dt_count <= 5:
    fear_risk = "偏低"
    fear_risk_note = "少量大面股，整体可控"
    risk_color = "blue-text"
elif bf_count <= 10:
    fear_risk = "偏高"
    fear_risk_note = "大面股数量偏多，注意回避高位"
    risk_color = "orange-text"
else:
    fear_risk = "高"
    fear_risk_note = "大面横飞，建议观望"
    risk_color = "red-text"

# 昨涨停表现评级
if avg_zf_qs >= 3:
    yesterday_perf = "良好"
    yesterday_note = "昨日涨停多数盈利"
elif avg_zf_qs >= 0:
    yesterday_perf = "中等"
    yesterday_note = "部分分化"
elif avg_zf_qs >= -2:
    yesterday_perf = "偏弱"
    yesterday_note = "多数断板分化"
else:
    yesterday_perf = "差"
    yesterday_note = "大面积回落"

print(f"   效应verdict: {effect_verdict_type}")
print(f"   恐惧风险: {fear_risk}")

# ══════════════════════════
# ⑪ 动态热点板块解读生成
# ══════════════════════════
print("\n[11/12] 生成热点解读...")

hot_topics = []
topic_tags = ['fire', 'fire', 'good', 'caution', 'good', 'caution']
tag_texts = ['最强主线', '持续 ✅', '关注', '活跃', '活跃', '活跃']

# 取TOP6题材生成解读
emojis = ['🔥', '🔋', '📡', '⚡', '🤖', '💻']
for idx, (t_name, t_cnt) in enumerate(real_themes[:6]):
    stocks_in_theme = theme_stocks.get(t_name, [])[:5]
    # 找该题材下涨幅最大的代表股
    reps = []
    for s in zt_all:
        if s['mc'] in stocks_in_theme:
            reps.append(f"{s['mc']}({s.get('zf',0):+.1f}%)")
    
    tag_idx = min(idx, len(tag_texts)-1)
    emoji = emojis[min(idx, len(emojis)-1)]
    
    # 动态生成描述
    desc_parts = []
    if reps:
        desc_parts.append('、'.join(reps[:3]))
    desc_parts.append(f"共{t_cnt}只涨停")
    
    # 根据题材特点加描述
    if '锂' in t_name or '电池' in t_name:
        topic_desc = f"新能源方向活跃，{desc_parts[0] if desc_parts else t_name}领涨。"
    elif 'AI' in t_name or '算力' in t_name or '机器人' in t_name:
        topic_desc = f"科技主线延续，{desc_parts[0] if desc_parts else t_name}表现突出。"
    elif '华为' in t_name:
        topic_desc = f"华为产业链联动，{desc_parts[0] if desc_parts else t_name}封板坚决。"
    elif 'IDC' in t_name or '数据中心' in t_name or '东数西算' in t_name:
        topic_desc = f"数字经济方向资金涌入，{desc_parts[0] if desc_parts else t_name}走强。"
    elif '光伏' in t_name or '新能源' in t_name:
        topic_desc = f"赛道股反弹，{desc_parts[0] if desc_parts else t_name}异动。"
    elif '军工' in t_name or '航空' in t_name:
        topic_desc = f"国防军工活跃，{desc_parts[0] if desc_parts else t_name}带动板块。"
    else:
        topic_desc = f"{t_name}方向{t_cnt}只涨停，资金关注度提升。{' '.join(reps[:2]) if reps else ''}"

    hot_topics.append({
        'emoji': emoji,
        'title': f"{t_name}",
        'desc': topic_desc,
        'type': topic_tags[tag_idx],
        'tag': tag_texts[tag_idx],
        'count': t_cnt
    })

for h in hot_topics:
    print(f"   [{h['tag']}] {h['emoji']} {h['title']} — {h['count']}只")

# ══════════════════════════
# ⑫ 板块强度TOP5
# ══════════════════════════
print("\n[12/12] 板块强度排名...")
sector_top5 = []
sector_evals = ['最强', '爆发', '活跃', '活跃', '活跃']
for idx, (t_name, t_cnt) in enumerate(real_themes[:5]):
    eval_word = sector_evals[idx] if idx < len(sector_evals) else '一般'
    stocks_str = '·'.join(theme_stocks.get(t_name, [])[:3])
    sector_top5.append({
        'rank': idx + 1,
        'name': t_name,
        'detail': stocks_str,
        'eval': eval_word,
        'eval_color': ['red-text', 'success', 'primary', 'warning', 'text-muted'][min(idx, 4)]
    })

# ══════════════════════════
# 输出汇总
# ══════════════════════════
print("\n" + "=" * 50)
print("✅ 数据采集完成!")
print("=" * 50)

# ───────────────────────────────
# HTML生成
# ───────────────────────────────
print("\n正在生成HTML...")

def up_down_class(val):
    if val > 0: return 'up'
    elif val < 0: return 'down'
    return 'flat'

def pct_class(val):
    if val > 0: return 'red-text'
    elif val < 0: return 'green-text'
    return ''

# 构建指数行
idx_cards_html = ""
for idx in indices_data:
    ud = up_down_class(idx['pct'])
    hl = ' highlight' if (idx['name'] == '创业板指' and idx['pct'] > 2) else ''
    font_extra = 'style="font-size: 15px"' if hl else ''
    idx_cards_html += f"""
          <div class="index-card{hl}">
            <div class="index-name">{idx['name']}</div>
            <div class="index-val">{idx['close']:.2f}</div>
            <div class="index-pct {ud}" {font_extra}>{"🔼" if idx["pct"]>=0 else "🔽"} {idx['pct']:+.2f}%</div>
          </div>"""

# 全景网格
panorama_html = f"""
          <div class="panorama-box pulse">
            <div class="panorama-num red-text">{zt_count}</div>
            <div class="panorama-label">涨停</div>
          </div>
          <div class="panorama-box">
            <div class="panorama-num orange-text">{zb_count}</div>
            <div class="panorama-label">炸板</div>
          </div>
          <div class="panorama-box">
            <div class="panorama-num green-text">{dt_count}</div>
            <div class="panorama-label">跌停</div>
          </div>
          <div class="panorama-box">
            <div class="panorama-num green-text">{fb_rate:.1f}%</div>
            <div class="panorama-label">封板率</div>
          </div>"""

# 量能
vol_dates_str = ','.join(v['date'] for v in vol_history)
vol_values_str = ','.join(str(round(v['vol'], 2)) for v in vol_history)

summary_text = f"""📊 涨停<span class="summary-highlight">{zt_count}家</span>、封板率<span class="summary-highlight">{fb_rate:.1f}%</span>显示短线情绪<span class="summary-highlight">{'良好' if fb_rate>=70 else '一般'}</span>。<br />量能<span class="summary-highlight">{'增量' if vol_diff>=0 else '缩量'}{abs(vol_diff):.0f}亿({vol_chg_pct:+.2f}%)</span>，资金{'仍在博弈' if abs(vol_chg_pct)<5 else ('加速进场' if vol_diff>0 else '有所退潮')}。"""

# 赚钱效应四维
effect_grid_html = f"""
          <div class="effect-item yellow-bg">
            <div class="effect-val orange-text" id="effectRatio">{effect_ratio_val}</div>
            <div class="effect-label">
              首板晋级率<br />
              <span style="color: var(--text-muted); font-size: 10px" id="effectRatioDetail">{effect_ratio_detail}</span>
            </div>
          </div>
          <div class="effect-item blue-bg">
            <div class="effect-val blue-text" id="effectProp">{effect_prop_val}</div>
            <div class="effect-label">
              首:连板比<br />
              <span style="color: var(--text-muted); font-size: 10px" id="effectPropDetail">{effect_prop_detail}</span>
            </div>
          </div>
          <div class="effect-item green-bg">
            <div class="effect-val green-text" id="effectLadder">{effect_ladder_val}</div>
            <div class="effect-label">
              梯队完整度<br />
              <span style="color: var(--text-muted); font-size: 10px" id="effectLadderDetail">{effect_ladder_detail}</span>
            </div>
          </div>
          <div class="effect-item red-bg">
            <div class="effect-val red-text" id="effectLimit">{limit_ratio}</div>
            <div class="effect-label">
              涨跌停比<br />
              <span style="color: var(--text-muted); font-size: 10px" id="effectLimitDetail">{limit_ratio_detail}</span>
            </div>
          </div>"""

# 恐惧指标 - 大面股组
bf_names = ', '.join([b['name'] for b in all_big_faces[:3]]) if all_big_faces else '无'
dt_names = ', '.join([f"{s.get('mc','')}{s.get('zf',0):.1f}%" for s in dt_all[:2]]) if dt_all else '—'

fear_grid1 = f"""
          <div class="fear-card">
            <div class="fear-val red-text" id="fearBigFace">{bf_count}只</div>
            <div class="fear-label">大面股(-5%↓)</div>
            <div class="fear-note" id="fearBigFaceNote">{bf_names if bf_names else '无'}</div>
          </div>
          <div class="fear-card">
            <div class="fear-val green-text" id="fearLimitDown">{dt_count}只</div>
            <div class="fear-label">非ST跌停</div>
            <div class="fear-note" id="fearLimitDownNote">{dt_names}</div>
          </div>
          <div class="fear-card">
            <div class="fear-val {risk_color}" id="fearRisk">{fear_risk}</div>
            <div class="fear-label">亏钱效应</div>
            <div class="fear-note">{fear_risk_note}</div>
          </div>"""

# 恐惧指标 - 炸板&昨表现组
fear_grid2 = f"""
          <div class="fear-card">
            <div class="fear-val orange-text" id="fearBroken">{zb_rate:.1f}%</div>
            <div class="fear-label">今日炸板率</div>
            <div class="fear-note" id="fearBrokenNote">{zb_count}/({zt_count}+{zb_count}) = {zb_rate:.1f}% | {'高于' if zb_rate>25 else '低于'}均值</div>
          </div>
          <div class="fear-card">
            <div class="fear-val green-text" id="fearSuccess">{fb_rate:.1f}%</div>
            <div class="fear-label">封板成功率</div>
            <div class="fear-note">封板质量{'极高' if fb_rate>=80 else ('尚可' if fb_rate>=70 else '偏低')}</div>
          </div>
          <div class="fear-card">
            <div class="fear-val blue-text" id="fearYesterday">{yesterday_perf}</div>
            <div class="fear-label">昨涨停今表现</div>
            <div class="fear-note">{yesterday_note}</div>
          </div>"""

# 热点板块解读
topics_html = ""
for h in hot_topics:
    topics_html += f"""
        <div class="hot-topic {h['type']}">
          <div class="topic-title">
            {h['emoji']} {h['title']}
            <span class="topic-tag tag-{h['type'].replace('good','sustained').replace('caution','caution').replace('fire','fire')}">{h['tag']}</span>
          </div>
          <div class="topic-desc">{h['desc']}</div>
        </div>"""

# 高度趋势数据
ht_dates_str = ','.join(height_trend['dates'])
ht_main_str = ','.join(str(x) for x in height_trend['main'])
ht_sub_str = ','.join(str(x) for x in height_trend['sub'])
ht_gem_str = ','.join(str(x) for x in height_trend['gem'])
ht_labels_main = ','.join(height_trend['labels_main'])
ht_labels_sub = ','.join(height_trend['labels_sub'])

# 连板天梯
ladder_body = ""
for row in ladder_rows:
    status_cls = 'green-text' if row['status'] == '晋级' else 'blue-text'
    badge_cls = f"badge-{row['badge']}" if row['badge'] <= 6 else 'badge-1'
    ladder_body += f"""            <tr>
              <td><span class="ladder-badge {badge_cls}">{row['badge']}板</span></td>
              <td class="stock-name-cell">{row['name']}</td>
              <td class="{status_cls}">{row['status']}</td>
              <td style="font-size: 12px; color: var(--text-muted)">{row['note']}</td>
            </tr>
"""

# 断板列表
broken_text = ' / '.join([f"{s['mc']}({s['lbc']}板)" for s in duanban_list[:8]])
if broken_text:
    broken_text = f"❌ 昨日断板：{broken_text}"
else:
    broken_text = "✅ 昨日无断板"

# 板块强度TOP5
sector_list_html = ""
for sec in sector_top5:
    rank_cls = f"rank-{sec['rank']}" if sec['rank'] <= 3 else 'rank-n'
    sector_list_html += f"""          <li class="sector-item">
            <span class="sector-rank {rank_cls}">{sec['rank']}</span>
            <div class="sector-info">
              <div class="sector-name">{sec['name']}</div>
              <div class="sector-detail">{sec['detail']}</div>
            </div>
            <div class="sector-pct" style="color: var(--{sec['eval_color']})">{sec['eval']}</div>
          </li>
"""

# 成交额TOP10
top10_body = ""
for i, t in enumerate(top10_with_theme):
    cls = pct_class(t['zf'])
    w = '900' if i == 0 else ('800' if i <= 2 else '700')
    top10_body += f"""            <tr>
              <td><span style="color: var(--danger); font-weight: {w}">{i+1}</span></td>
              <td class="stock-name-cell">{t['mc']}</td>
              <td class="{cls}">{t['zf']:+.2f}%</td>
              <td style="font-weight: {w}">{t['cje']/1e8:.0f}亿</td>
              <td>{t['sector']}</td>
            </tr>
"""

# 行动指南
# 关键看点
key_watch1 = f"{ladder_rows[0]['name'].replace('👑 ','')}{max_lb}→{max_lb+1}板能否晋级？决定空间是否打开。" if ladder_rows else ""
key_watch2 = f"{hot_topics[0]['title']}持续性！" if hot_topics else ""

action_items = f"""          <li class="action-item">
            <span class="action-dot dot-key"></span>
            <span class="action-text">
              <strong>关键看点①：</strong>
              {key_watch1}
            </span>
          </li>
          <li class="action-item">
            <span class="action-dot dot-key"></span>
            <span class="action-text">
              <strong>关键看点②：</strong>
              {key_watch2}
            </span>
          </li>
          <li class="action-item">
            <span class="action-dot dot-watch"></span>
            <span class="action-text">
              <strong>观察：</strong>
              {hot_topics[1]['title'] if len(hot_topics)>1 else '主流板块'}是否分化。
            </span>
          </li>
          <li class="action-item">
            <span class="action-dot dot-risk"></span>
            <span class="action-text">
              <strong>风险提示：</strong>
              {'高潮次日分化风险！' if zt_count>=70 else '注意情绪变化'}今日涨停{zt_count}只是{'近期峰值' if zt_count>=70 else '正常水平'}，{'不追涨' if zt_count>=70 else '控制仓位'}。
            </span>
          </li>
          <li class="action-item">
            <span class="action-dot dot-safe"></span>
            <span class="action-text" style="color: var(--success)">
              <strong>策略建议：{'持仓观察' if effect_verdict_type=='good' else ('轻仓试错' if effect_verdict_type=='warn' else '空仓观望')}</strong>
              {'— 四维度向好，但今天高潮，只持仓不追涨。' if effect_verdict_type=='good' else ('— 有结构性机会，以低位首板为主。' if effect_verdict_type=='warn' else '— 等待情绪修复再入场。')}
            </span>
          </li>"""

# ───────────────────────────────
# 最终HTML组装
# ───────────────────────────────
html = f'''<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>A股收盘简报 | {DATE}</title>
    <script src="https://fastly.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
      :root {{
        --primary: #2563eb;
        --success: #10b981;
        --danger: #ef4444;
        --warning: #f59e0b;
        --purple: #8b5cf6;
        --pink: #ec4899;

        /* 亮色主题 */
        --bg-base: #f4f7fa;
        --bg-card: #ffffff;
        --bg-elevated: #f8fafc;
        --border: rgba(0, 0, 0, 0.06);
        --text-primary: #1e293b;
        --text-secondary: #475569;
        --text-muted: #94a3b8;

        --radius-lg: 18px;
        --radius-md: 12px;
        --radius-sm: 8px;
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.04);
        --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.05);
        --shadow-lg: 0 10px 40px rgba(0, 0, 0, 0.08);
      }}

      [data-theme="dark"] {{
        --bg-base: #0f172a;
        --bg-card: #1e293b;
        --bg-elevated: #334155;
        --border: rgba(255, 255, 255, 0.08);
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-muted: #64748b;
        --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.4);
      }}

      * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }}

      body {{
        font-family: -apple-system, "SF Pro Text", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", sans-serif;
        background: var(--bg-base);
        color: var(--text-primary);
        line-height: 1.6;
        padding: 24px 12px 60px;
        transition:
          background 0.3s,
          color 0.3s;
      }}
      .container {{
        max-width: 860px;
        margin: 0 auto;
      }}

      /* Hero */
      .hero {{
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #60a5fa 100%);
        border-radius: var(--radius-lg);
        padding: 32px 28px;
        color: #fff;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
        box-shadow: var(--shadow-lg);
      }}
      .hero::before {{
        content: "";
        position: absolute;
        top: -30%;
        right: -15%;
        width: 320px;
        height: 320px;
        background: rgba(255, 255, 255, 0.06);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
      }}
      .hero::after {{
        content: "";
        position: absolute;
        bottom: -40%;
        left: -10%;
        width: 200px;
        height: 200px;
        background: rgba(255, 255, 255, 0.04);
        border-radius: 50%;
        animation: float 8s ease-in-out infinite reverse;
      }}
      @keyframes float {{
        0%, 100% {{ transform: translateY(0) scale(1); }}
        50% {{ transform: translateY(-20px) scale(1.05); }}
      }}
      .hero-top {{ position: relative; z-index: 1; }}
      .hero-controls {{
        position: absolute;
        top: 20px;
        right: 20px;
        display: flex;
        gap: 8px;
        z-index: 2;
      }}
      .theme-toggle {{
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #fff;
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s;
        backdrop-filter: blur(10px);
      }}
      .theme-toggle:hover {{ background: rgba(255, 255, 255, 0.25); }}
      .cycle-tag {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(10px);
        padding: 6px 16px;
        border-radius: 30px;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 12px;
      }}
      .cycle-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--success);
        animation: pulse 2s infinite;
      }}
      @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} }}
      .hero-date {{ font-size: 26px; font-weight: 800; letter-spacing: 0.5px; }}
      .hero-subtitle {{ opacity: 0.8; font-size: 13px; margin-top: 6px; font-weight: 500; }}

      .index-row {{ display: flex; gap: 12px; margin-top: 24px; position: relative; z-index: 1; flex-wrap: wrap; }}
      .index-card {{
        flex: 1; min-width: 120px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: var(--radius-md);
        padding: 16px 12px;
        text-align: center;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.2s, background 0.2s;
      }}
      .index-card:hover {{ transform: translateY(-3px); background: rgba(255, 255, 255, 0.18); }}
      .index-card.highlight {{ background: rgba(239, 68, 68, 0.25); border-color: rgba(239, 68, 68, 0.4); box-shadow: 0 0 30px rgba(239, 68, 68, 0.2); }}
      .index-name {{ font-size: 12px; opacity: 0.85; margin-bottom: 6px; font-weight: 600; }}
      .index-val {{ font-size: 20px; font-weight: 800; margin-bottom: 2px; }}
      .index-pct {{ font-size: 13px; font-weight: 700; }}
      .up {{ color: #fecaca !important; }}
      .down {{ color: #bbf7d0 !important; }}
      .flat {{ color: #fef08a !important; }}

      /* Card */
      .card {{
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        padding: 24px;
        margin-bottom: 18px;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--border);
        transition: background 0.3s, border-color 0.3s;
      }}
      .card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }}
      .card-title {{
        display: flex; align-items: center; gap: 10px;
        font-size: 17px; font-weight: 800; color: var(--text-primary);
        margin-buttom
      }}
      .card-title::before {{
        content: ""; display: inline-block;
        width: 4px; height: 20px;
        background: var(--primary); border-radius: 2px;
      }}
      .card-badge {{ font-size: 11px; padding: 4px 10px; border-radius: 20px; font-weight: 700; background: var(--bg-elevated); color: var(--text-muted); }}

      /* Panorama */
      .panorama-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }}
      @media (max-width: 500px) {{ .panorama-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
      .panorama-box {{ text-align: center; padding: 18px 10px; border-radius: var(--radius-md); background: var(--bg-elevated); transition: all 0.2s; border: 1px solid transparent; }}
      .panorama-box:hover {{ transform: translateY(-2px); border-color: var(--primary); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.1); }}
      .panorama-box.pulse {{ animation: boxPulse 2s ease-in-out; }}
      @keyframes boxPulse {{ 0%, 100% {{ box-shadow: none; }} 50% {{ box-shadow: 0 0 20px rgba(239, 68, 68, 0.3); }} }}
      .panorama-num {{ font-size: 30px; font-weight: 900; line-height: 1.1; margin-bottom: 6px; }}
      .panorama-label {{ font-size: 12px; color: var(--text-muted); font-weight: 600; }}

      /* Volume */
      .volume-info-box {{ background: var(--bg-elevated); border-radius: var(--radius-md); padding: 20px; display: flex; align-items: center; gap: 20px; margin-bottom: 20px; border: 1px solid var(--border); }}
      .volume-icon-circle {{ width: 48px; height: 48px; background: var(--bg-card); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 22px; box-shadow: var(--shadow-sm); flex-shrink: 0; }}
      .volume-main-val {{ flex: 1; }}
      .volume-label-row {{ display: flex; gap: 12px; font-size: 13px; color: var(--text-muted); margin-bottom: 4px; font-weight: 600; }}
      .volume-data-row {{ display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }}
      .volume-total {{ font-size: 26px; font-weight: 900; color: var(--text-primary); }}
      .volume-change {{ font-size: 16px; font-weight: 800; }}
      .volume-increase {{ font-size: 14px; font-weight: 600; }}

      /* Effect Grid */
      .effect-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }}
      @media (max-width: 600px) {{ .effect-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
      .effect-item {{ padding: 16px 12px; border-radius: var(--radius-md); text-align: center; border: 1px solid transparent; transition: all 0.2s; }}
      .effect-item:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-md); }}
      .effect-item.yellow-bg {{ background: linear-gradient(135deg, #fffbeb, #fef3c7); }}
      .effect-item.blue-bg {{ background: linear-gradient(135deg, #eff6ff, #dbeafe); }}
      .effect-item.green-bg {{ background: linear-gradient(135deg, #ecfdf5, #d1fae5); }}
      .effect-item.red-bg {{ background: linear-gradient(135deg, #fef2f2, #fee2e2); }}
      [data-theme="dark"] .effect-item.yellow-bg {{ background: rgba(245, 158, 11, 0.15); }}
      [data-theme="dark"] .effect-item.blue-bg {{ background: rgba(37, 99, 235, 0.15); }}
      [data-theme="dark"] .effect-item.green-bg {{ background: rgba(16, 185, 129, 0.15); }}
      [data-theme="dark"] .effect-item.red-bg {{ background: rgba(239, 68, 68, 0.15); }}
      .effect-val {{ font-size: 22px; font-weight: 900; margin-bottom: 4px; }}
      .effect-label {{ font-size: 11px; color: var(--text-secondary); line-height: 1.4; font-weight: 600; }}

      /* Fear Grid */
      .fear-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 16px; }}
      @media (max-width: 500px) {{ .fear-grid {{ grid-template-columns: 1fr; }} }}
      .fear-card {{ background: var(--bg-elevated); border-radius: var(--radius-md); padding: 14px 10px; text-align: center; border: 1px solid var(--border); transition: all 0.2s; }}
      .fear-card:hover {{ border-color: var(--primary); transform: translateY(-1px); }}
      .fear-val {{ font-size: 20px; font-weight: 800; margin-bottom: 4px; }}
      .fear-label {{ font-size: 11px; color: var(--text-muted); font-weight: 700; }}
      .fear-note {{ font-size: 10px; color: var(--text-muted); margin-top: 4px; line-height: 1.3; }}

      /* Ladder Table */
      .ladder-table {{ width: 100%; border-collapse: separate; border-spacing: 0 6px; font-size: 13.5px; }}
      .ladder-table th {{ padding: 10px 12px; text-align: center; font-weight: 700; color: var(--text-muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
      .ladder-table td {{ padding: 12px 12px; background: var(--bg-elevated); text-align: center; vertical-align: middle; transition: background 0.2s; }}
      .ladder-table tr:hover td {{ background: var(--bg-card); }}
      .ladder-table tr td:first-child {{ border-radius: var(--radius-sm) 0 0 var(--radius-sm); }}
      .ladder-table tr td:last-child {{ border-radius: 0 var(--radius-sm) var(--radius-sm) 0; }}
      .ladder-badge {{ display: inline-block; padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 800; min-width: 45px; }}
      .badge-6 {{ background: linear-gradient(135deg, #fee2e2, #fecaca); color: #b91c1c; }}
      .badge-5 {{ background: linear-gradient(135deg, #fee2e2, #fecaca); color: #dc2626; }}
      .badge-4 {{ background: linear-gradient(135deg, #ffedd5, #fed7aa); color: #9a3412; }}
      .badge-3 {{ background: linear-gradient(135deg, #dcfce7, #bbf7d0); color: #15803d; }}
      .badge-2 {{ background: linear-gradient(135deg, #dbeafe, #bfdbfe); color: #1d4ed8; }}
      .badge-1 {{ background: var(--bg-elevated); color: var(--text-muted); }}
      [data-theme="dark"] .badge-6 {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; }}
      [data-theme="dark"] .badge-5 {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; }}
      [data-theme="dark"] .badge-4 {{ background: rgba(245, 158, 11, 0.2); color: #fcd34d; }}
      [data-theme="dark"] .badge-3 {{ background: rgba(16, 185, 129, 0.2); color: #86efac; }}
      [data-theme="dark"] .badge-2 {{ background: rgba(37, 99, 235, 0.2); color: #93c5fd; }}
      [data-theme="dark"] .badge-1 {{ background: rgba(148, 163, 184, 0.2); color: #94a3b8; }}
      .stock-name-cell {{ font-weight: 700; color: var(--text-primary); }}

      /* Hot Topic */
      .hot-topic {{ padding: 16px; border-radius: var(--radius-md); margin-bottom: 12px; border-left: 4px solid; transition: all 0.2s; }}
      .hot-topic:hover {{ transform: translateX(4px); }}
      .hot-topic.good {{ background: var(--bg-elevated); border-color: var(--success); }}
      .hot-topic.caution {{ background: var(--bg-elevated); border-color: var(--warning); }}
      .hot-topic.fire {{ background: var(--bg-elevated); border-color: var(--danger); }}
      .topic-title {{ font-weight: 800; font-size: 14px; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; color: var(--text-primary); }}
      .topic-desc {{ font-size: 13px; color: var(--text-secondary); line-height: 1.65; }}
      .topic-tag {{ display: inline-block; font-size: 10px; padding: 2px 10px; border-radius: 20px; font-weight: 800; margin-left: auto; }}
      .tag-sustained {{ background: #dcfce7; color: #166534; }}
      .tag-caution {{ background: #fef3c7; color: #92400e; }}
      .tag-fire {{ background: #fee2e2; color: #b91c1c; }}
      [data-theme="dark"] .tag-sustained {{ background: rgba(16, 185, 129, 0.2); color: #86efac; }}
      [data-theme="dark"] .tag-caution {{ background: rgba(245, 158, 11, 0.2); color: #fcd34d; }}
      [data-theme="dark"] .tag-fire {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; }}

      /* Sector List */
      .sector-list {{ list-style: none; }}
      .sector-item {{ display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-radius: var(--radius-md); margin-bottom: 8px; background: var(--bg-elevated); border: 1px solid transparent; transition: all 0.2s; }}
      .sector-item:hover {{ background: var(--bg-card); border-color: var(--primary); transform: translateX(4px); }}
      .sector-rank {{ width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 900; color: #fff; flex-shrink: 0; }}
      .rank-1 {{ background: linear-gradient(135deg, #fbbf24, #f59e0b); }}
      .rank-2 {{ background: linear-gradient(135deg, #94a3b8, #64748b); }}
      .rank-3 {{ background: linear-gradient(135deg, #d97706, #b45309); }}
      .rank-n {{ background: var(--bg-card); color: var(--text-muted); }}
      [data-theme="dark"] .rank-n {{ background: rgba(148, 163, 184, 0.2); }}
      .sector-info {{ flex: 1; margin-left: 14px; }}
      .sector-name {{ font-weight: 700; font-size: 14px; color: var(--text-primary); }}
      .sector-detail {{ font-size: 11px; color: var(--text-muted); margin-top: 2px; font-weight: 500; }}
      .sector-pct {{ font-size: 15px; font-weight: 800; min-width: 55px; text-align: right; }}

      /* Action List */
      .action-list {{ list-style: none; }}
      .action-item {{ display: flex; gap: 14px; padding: 14px 0; border-bottom: 1px solid var(--border); }}
      .action-item:last-child {{ border: none; }}
      .action-dot {{ width: 10px; height: 10px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }}
      .dot-key {{ background: var(--primary); box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15); }}
      .dot-risk {{ background: var(--danger); box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15); }}
      .dot-watch {{ background: var(--warning); box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15); }}
      .dot-safe {{ background: var(--success); box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15); }}
      .action-text {{ font-size: 13.5px; color: var(--text-secondary); line-height: 1.65; font-weight: 500; }}

      /* Chart */
      .chart-container {{ width: 100%; height: 220px; margin-bottom: 16px; position: relative; }}
      .chart-legend {{ display: none; }} /* ECharts has its own legend or we use custom one */

      /* Verdict Box */
      .verdict-box {{ border-radius: var(--radius-md); padding: 18px; font-size: 13.5px; line-height: 1.75; margin-top: 14px; }}
      .verdict-warn {{ background: linear-gradient(135deg, #fffbeb, #fef3c7); color: #92400e; border: 1px solid #fde68a; }}
      .verdict-good {{ background: linear-gradient(135deg, #ecfdf5, #d1fae5); color: #166534; border: 1px solid #a7f3d0; }}
      .verdict-fire {{ background: linear-gradient(135deg, #fef2f2, #fee2e2); color: #b91c1c; border: 1px solid #fecaca; }}
      [data-theme="dark"] .verdict-warn {{ background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.3); }}
      [data-theme="dark"] .verdict-good {{ background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.3); }}
      [data-theme="dark"] .verdict-fire {{ background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); }}
      .verdict-box strong {{ font-size: 14px; display: block; margin-bottom: 4px; }}

      /* Summary Box */
      .summary-box {{ 
        background: var(--bg-elevated); 
        border-radius: var(--radius-md); 
        padding: 18px 20px; 
        border-left: 5px solid var(--warning); 
        margin-top: 16px; 
        box-shadow: inset 0 0 10px rgba(0,0,0,0.02);
      }}
      .summary-text {{ 
        font-size: 14.5px; 
        color: var(--text-primary); 
        line-height: 1.85; 
        font-weight: 500; 
      }}
      .summary-highlight {{ 
        color: var(--danger); 
        font-weight: 800; 
        padding: 0 2px;
      }}
      .summary-footer {{ 
        display: flex; 
        justify-content: flex-end; 
        align-items: center; 
        gap: 8px; 
        margin-top: 12px; 
        opacity: 0.45; 
        font-size: 11px; 
        font-weight: 700;
        color: var(--text-secondary);
      }}

      /* Section Header */
      .section-header {{ font-size: 12px; font-weight: 800; color: var(--text-muted); margin: 16px 0 10px; padding-left: 10px; border-left: 3px solid var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }}
      .red-text {{ color: var(--danger); }}
      .green-text {{ color: var(--success); }}
      .orange-text {{ color: var(--warning); }}
      .blue-text {{ color: var(--primary); }}
      .purple-text {{ color: var(--purple); }}

      /* Footer */
      .footer {{ text-align: center; padding: 32px 20px; color: var(--text-muted); font-size: 12px; font-weight: 500; }}
      .footer p {{ margin-bottom: 4px; }}

      @media (max-width: 600px) {{
        .hero {{ padding: 24px 20px; }}
        .hero-date {{ font-size: 22px; }}
        .card {{ padding: 18px 16px; }}
        .volume-info-box {{ flex-direction: column; text-align: center; }}
        .index-card {{ min-width: 100px; }}
        .index-val {{ font-size: 18px; }}
      }}

      @media print {{ .theme-toggle {{ display: none; }} body {{ background: #fff; color: #000; }} .card {{ box-shadow: none; border: 1px solid #e2e8f0; }} }}
    </style>
  </head>
  <body>
    <div class="container">
      <!-- Hero -->
      <div class="hero">
        <div class="hero-controls">
          <button class="theme-toggle" onclick="toggleTheme()">🌙 深色</button>
        </div>
        <div class="hero-top">
          <div class="cycle-tag"><span class="cycle-dot"></span>短线复盘 · 情绪监控</div>
          <div class="hero-date">{DATE.replace('-', '年', 1).replace('-', '月', 1)}收盘简报</div>
          <div class="hero-subtitle">数据来源：必盈API | 自动生成报告</div>
        </div>
        <div class="index-row">
{idx_cards_html}
        </div>
      </div>

      <!-- 市场全景 -->
      <div class="card">
        <div class="card-header"><div class="card-title">市场全景</div><div class="card-badge">非ST股</div></div>
        <div class="panorama-grid">
{panorama_html}
        </div>
      </div>

      <!-- 市场量能 -->
      <div class="card">
        <div class="card-header"><div class="card-title">市场量能</div></div>
        <div class="volume-info-box">
          <div class="volume-icon-circle">⇄</div>
          <div class="volume-main-val">
            <div class="volume-label-row"><span>沪深合计 · 实际量能</span><span>较昨日</span></div>
            <div class="volume-data-row">
              <span class="volume-total" id="volTotal">{today_total_vol:.2f}亿</span>
              <span class="volume-change {pct_class(vol_chg_pct)}" id="volChange">{vol_chg_pct:+.2f}%</span>
              <span class="volume-increase orange-text" id="volIncrease">{'增量' if vol_diff>=0 else '缩量'} {abs(vol_diff):+.2f}亿</span>
            </div>
          </div>
        </div>

        <div class="chart-container">
          <div id="volume-trend-echart" style="width: 100%; height: 100%;"></div>
        </div>

        <div class="summary-box">
          <div class="summary-text" id="summaryText">{summary_text}</div>
          
        </div>
      </div>

      <!-- 赚钱效应四维判断 -->
      <div class="card">
        <div class="card-title">赚钱效应四维判断</div>
        <div class="effect-grid">
{effect_grid_html}
        </div>
        <div class="verdict-box verdict-{effect_verdict_type}" id="effectVerdict">
          <strong>{effect_verdict_title}</strong>
          {effect_verdict_detail}
        </div>
      </div>

      <!-- 恐惧指标 -->
      <div class="card">
        <div class="card-title">恐惧指标 & 赚钱效应量化</div>

        <div class="section-header">大面股 / 核按钮</div>
        <div class="fear-grid">
{fear_grid1}
        </div>

        <div class="section-header">炸板率 & 昨涨停表现</div>
        <div class="fear-grid">
{fear_grid2}
        </div>
      </div>

      <!-- 今日热点板块解读 -->
      <div class="card">
        <div class="card-title">今日热点板块解读</div>
{topics_html}
      </div>

      <!-- 近7日高度趋势 -->
      <div class="card">
        <div class="card-title">近7日高度趋势</div>
        <div class="chart-container" style="height: 260px;">
          <div id="height-trend-echart" style="width: 100%; height: 100%;"></div>
        </div>
      </div>

      <!-- 连板天梯 -->
      <div class="card">
        <div class="card-header"><div class="card-title">连板天梯</div><div class="card-badge">非ST</div></div>
        <table class="ladder-table">
          <thead><tr><th>高度</th><th>股票名称</th><th>状态</th><th>备注</th></tr></thead>
          <tbody id="ladderBody">
{ladder_body}
          </tbody>
        </table>
        <div style="margin-top: 12px; padding: 10px 14px; background: rgba(239, 68, 68, 0.08); border-radius: var(--radius-sm); font-size: 12px; color: var(--danger); font-weight: 600" id="brokenList">
          {broken_text}
        </div>
      </div>

      <!-- 板块强度TOP5 -->
      <div class="card">
        <div class="card-title">板块强度 TOP5</div>
        <ul class="sector-list" id="sectorList">
{sector_list_html}
        </ul>
      </div>

      <!-- 成交额TOP10 -->
      <div class="card">
        <div class="card-title">成交额 TOP10</div>
        <table class="ladder-table">
          <thead><tr><th>#</th><th>个股</th><th>涨幅</th><th>成交额</th><th>板块</th></tr></thead>
          <tbody id="top10Body">
{top10_body}
          </tbody>
        </table>
        <div style="margin-top: 10px; font-size: 12px; color: var(--text-muted)">
          TOP5合计：<strong style="color: var(--text-primary)">{sum(t['cje'] for t in top10_with_theme[:5])/1e8:.0f}亿</strong>
          | {', '.join([t['sector'] for t in top10_with_theme[:5]])}
        </div>
      </div>

      <!-- 明日行动指南 -->
      <div class="card">
        <div class="card-title">明日行动指南</div>
        <ul class="action-list">
{action_items}
        </ul>
      </div>

      <div class="footer">
        <p>📊 生成时间：{DATE} 收盘</p>
        <p>数据来源：biyingapi 实时查询 | Claw Daily v11</p>
        <p>K线为王 · 数据即事实 · 零ST · 不编造不猜测</p>
      </div>
    </div>

    <script>
      // 核心数据对象
      const marketData = {{
        date: "{DATE}",
        indices: [
          {{ name: "{indices_data[0]['name']}", val: "{indices_data[0]['close']:.2f}", chg: "{indices_data[0]['pct']:+.2f}%", up: true }},
          {{ name: "{indices_data[1]['name']}", val: "{indices_data[1]['close']:.2f}", chg: "{indices_data[1]['pct']:+.2f}%", up: true }},
          {{ name: "{indices_data[2]['name']}", val: "{indices_data[2]['close']:.2f}", chg: "{indices_data[2]['pct']:+.2f}%", up: true, highlight: {"true" if indices_data[2]["pct"] > 2 else "false"} }},
          {{ name: "{indices_data[3]['name']}", val: "{indices_data[3]['close']:.2f}", chg: "{indices_data[3]['pct']:+.2f}%", up: true }},
        ],
        panorama: {{ limitUp: {zt_count}, broken: {zb_count}, limitDown: {dt_count}, ratio: "{fb_rate:.1f}%" }},
        volume: {{
          total: "{today_total_vol:.2f}亿",
          change: "{vol_chg_pct:+.2f}%",
          increase: "{'增量' if vol_diff>=0 else '缩量'} {abs(vol_diff):+.2f}亿",
          dates: [{','.join(['"'+v['date']+'"' for v in vol_history])}],
          values: [{','.join([str(round(v['vol'],2)) for v in vol_history])}],
        }},
        effect: {{
          ratio: "{effect_ratio_val}",
          ratioDetail: "{effect_ratio_detail}",
          prop: "{effect_prop_val}",
          propDetail: "{effect_prop_detail}",
          ladder: "{effect_ladder_val}",
          ladderDetail: "{effect_ladder_detail}",
          limit: "{limit_ratio}",
          limitDetail: "{limit_ratio_detail}",
          verdict: "{effect_verdict_title}",
          verdictDetail: "{effect_verdict_detail}",
          verdictType: "{effect_verdict_type}",
        }},
        fear: {{
          bigFace: "{bf_count}只",
          bigFaceNote: "{bf_names}",
          limitDown: "{dt_count}只",
          limitDownNote: "{dt_names}",
          risk: "{fear_risk}",
          broken: "{zb_rate:.1f}%",
          brokenNote: "{zb_count}/({zt_count}+{zb_count})={zb_rate:.1f}%",
          success: "{fb_rate:.1f}%",
          successNote: "封板质量{'极高' if fb_rate>=80 else ('尚可' if fb_rate>=70 else '偏低')}",
          yesterday: "{yesterday_perf}",
        }},
        heightTrend: {{
          dates: [{','.join(['"'+d+'"' for d in height_trend['dates']])}],
          main: [{','.join(str(x) for x in height_trend['main'])}],
          sub: [{','.join(str(x) for x in height_trend['sub'])}],
          gem: [{','.join(str(x) for x in height_trend['gem'])}],
          labels: {{
            main: [{','.join(['"'+l+'"' for l in height_trend['labels_main']])}],
            sub: [{','.join(['"'+l+'"' for l in height_trend['labels_sub']])}],
            gem: [{','.join(['"'+l+'"' for l in height_trend['labels_gem']])}],
          }},
        }},
        ladder: [
{', '.join([f'\n          {{ badge: {r["badge"]}, name: "{r["name"]}", status: "{r["status"]}", note: "{r["note"]}" }}' for r in ladder_rows])}
        ],
        broken: "{broken_text.replace('❌ 昨日断板：','').replace('✅ 昨日无断板','')}",
      }};

      // 核心图表实例
      let volumeChart, heightChart;

      /**
       * 渲染量能趋势图 (ECharts 实现)
       * @param {{Object}} data 量能数据
       */
      const renderVolumeTrend = (data) => {{
        const chartDom = document.getElementById('volume-trend-echart');
        if (!chartDom) return;
        if (volumeChart) volumeChart.dispose();
        volumeChart = echarts.init(chartDom, document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : null);
        
        const vals = data.values.map(v => Number(v));
        const isUp = (i) => i === 0 || vals[i] >= vals[i-1];
        
        const option = {{
          backgroundColor: 'transparent',
          tooltip: {{ 
            trigger: 'axis', 
            axisPointer: {{ type: 'shadow' }},
            formatter: (params) => {{
              let res = `<div style="font-weight:800;margin-bottom:4px">${{params[0].name}}</div>`;
              params.forEach(p => {{
                res += `<div style="display:flex;justify-content:space-between;gap:12px;font-size:12px">
                  <span>${{p.seriesName}}</span>
                  <span style="font-weight:800;color:${{p.color}}">${{p.value.toFixed(0)}}亿</span>
                </div>`;
              }});
              return res;
            }}
          }},
          grid: {{ top: '15%', left: '3%', right: '3%', bottom: '15%', containLabel: true }},
          xAxis: {{
            type: 'category',
            data: data.dates,
            axisLine: {{ lineStyle: {{ color: 'var(--text-muted)' }} }},
            axisLabel: {{ color: 'var(--text-muted)', fontWeight: 700, fontSize: 10 }}
          }},
          yAxis: {{
            type: 'value',
            max: 40000,
            splitLine: {{ lineStyle: {{ type: 'dashed', color: 'var(--border)' }} }},
            axisLabel: {{ 
              color: 'var(--text-muted)', 
              fontWeight: 700, 
              fontSize: 10,
              formatter: (v) => v.toFixed(0)
            }}
          }},
          series: [
            {{
              name: '两市成交额',
              type: 'bar',
              label: {{
                show: true,
                position: 'top',
                formatter: (params) => params.value.toFixed(0),
                color: 'var(--text-muted)',
                fontWeight: 800,
                fontSize: 10
              }},
              data: vals.map((v, i) => ({{
                value: v,
                itemStyle: {{ color: isUp(i) ? '#ef4444' : '#10b981', borderRadius: [4, 4, 0, 0] }}
              }})),
              barWidth: '45%'
            }},
            {{
              name: '成交趋势',
              type: 'line',
              data: vals,
              smooth: true,
              showSymbol: false,
              lineStyle: {{ width: 3, color: '#2563eb' }},
              areaStyle: {{
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  {{ offset: 0, color: 'rgba(37, 99, 235, 0.2)' }},
                  {{ offset: 1, color: 'rgba(37, 99, 235, 0)' }}
                ])
              }}
            }}
          ]
        }};
        volumeChart.setOption(option);
      }};

      /**
       * 渲染高度趋势图 (ECharts 实现)
       * @param {{Object}} data 高度趋势数据
       */
      const renderHeightTrend = (data) => {{
        const chartDom = document.getElementById('height-trend-echart');
        if (!chartDom) return;
        if (heightChart) heightChart.dispose();
        heightChart = echarts.init(chartDom, document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : null);

        const option = {{
          backgroundColor: 'transparent',
          tooltip: {{ trigger: 'axis' }},
          legend: {{
            data: ['最高板', '次高板', '创业板'],
            bottom: 0,
            textStyle: {{ color: 'var(--text-muted)', fontWeight: 600, fontSize: 11 }},
            icon: 'circle'
          }},
          grid: {{ top: '15%', left: '3%', right: '5%', bottom: '20%', containLabel: true }},
          xAxis: {{
            type: 'category',
            data: data.dates,
            boundaryGap: false,
            axisLine: {{ lineStyle: {{ color: 'var(--text-muted)' }} }},
            axisLabel: {{ color: 'var(--text-muted)', fontWeight: 700, fontSize: 10 }}
          }},
          yAxis: {{
            type: 'value',
            min: 0,
            max: 8,
            interval: 1,
            splitLine: {{ lineStyle: {{ type: 'dashed', color: 'var(--border)' }} }},
            axisLabel: {{ color: 'var(--text-muted)', fontWeight: 700, fontSize: 10 }}
          }},
          series: [
            {{
              name: '最高板',
              type: 'line',
              data: data.main,
              smooth: true,
              lineStyle: {{ width: 4, color: '#ef4444' }},
              itemStyle: {{ color: '#ef4444' }},
              areaStyle: {{
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  {{ offset: 0, color: 'rgba(239, 68, 68, 0.15)' }},
                  {{ offset: 1, color: 'rgba(239, 68, 68, 0)' }}
                ])
              }},
              symbolSize: 8,
              label: {{
                show: true,
                position: 'top',
                formatter: (params) => data.labels.main[params.dataIndex] || '',
                color: '#ef4444',
                fontWeight: 800,
                fontSize: 10,
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                padding: [2, 4],
                borderRadius: 4,
                borderColor: '#ef4444',
                borderWidth: 0.5
              }}
            }},
            {{
              name: '次高板',
              type: 'line',
              data: data.sub,
              smooth: true,
              lineStyle: {{ width: 3, color: '#f59e0b', type: 'dashed' }},
              itemStyle: {{ color: '#f59e0b' }},
              symbolSize: 6,
              label: {{
                show: true,
                position: 'top',
                formatter: (params) => data.labels.sub[params.dataIndex] || '',
                color: '#f59e0b',
                fontWeight: 800,
                fontSize: 10
              }}
            }},
            {{
              name: '创业板',
              type: 'line',
              data: data.gem,
              smooth: true,
              lineStyle: {{ width: 2, color: '#94a3b8' }},
              itemStyle: {{ color: '#94a3b8' }},
              symbolSize: 4,
              label: {{
                show: true,
                position: 'top',
                formatter: (params) => data.labels.gem[params.dataIndex] || '',
                color: '#94a3b8',
                fontWeight: 800,
                fontSize: 10
              }}
            }}
          ]
        }};
        heightChart.setOption(option);
      }};

      /**
       * 渲染连板天梯
       * @param {{Array}} data 天梯数据
       */
      const renderLadder = (data) => {{
        const tbody = document.getElementById("ladderBody"); 
        if(!tbody) return;
        tbody.innerHTML = data.map(row => `
          <tr>
            <td><span class="ladder-badge badge-${{row.badge}}">${{row.badge}}板</span></td>
            <td class="stock-name-cell">${{row.name}}</td>
            <td class="${{row.status === "晋级" ? "green-text" : "blue-text"}}">${{row.status}}</td>
            <td style="font-size:12px;color:var(--text-muted)">${{row.note}}</td>
          </tr>
        `).join("");
      }};

      /**
       * 切换主题 (支持 ECharts 重新渲染)
       */
      const toggleTheme = () => {{
        const html = document.documentElement;
        const isDark = html.getAttribute("data-theme") === "dark";
        isDark ? html.removeAttribute("data-theme") : html.setAttribute("data-theme", "dark");
        
        // 重新初始化图表以适配主题
        renderVolumeTrend(marketData.volume);
        renderHeightTrend(marketData.heightTrend);
      }};

      document.addEventListener("DOMContentLoaded", () => {{
        renderVolumeTrend(marketData.volume);
        renderHeightTrend(marketData.heightTrend);
        renderLadder(marketData.ladder);
        
        // 响应式处理
        window.addEventListener('resize', () => {{
          volumeChart && volumeChart.resize();
          heightChart && heightChart.resize();
        }});
      }});

    </script>
  </body>
</html>'''

if not os.path.exists("html"):
    os.makedirs("html")

output_path = os.path.join("html", f"复盘日记-{DATE.replace('-', '')}.html")
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ HTML已生成: {os.path.abspath(output_path) if 'os' in globals() else output_path}")
print(f"\n--- 报告摘要 ---")
print(f"日期: {DATE}")
print("指数: " + " ".join([f'{i["name"]}{i["close"]:.2f}({i["pct"]:+.2f}%)' for i in indices_data]))
print(f"全景: 涨停{zt_count} 炸板{zb_count} 跌停{dt_count} 封板{fb_rate:.1f}%")
print(f"量能: {today_total_vol:.0f}亿 ({vol_chg_pct:+.2f}%)")
print(f"赚钱效应: {effect_verdict_title}")
print(f"天梯: 最高{max_lb}板, {len(ladder_rows)}只连板, 晋级率{jj_rate:.0f}%")
print(f"题材TOP3: {', '.join([f'{t[0]}({t[1]}只)' for t in real_themes[:3]])}")
print(f"恐惧: 大面{bf_count}只, 亏钱{fear_risk}")
print(f"成交额TOP1: {top10_with_theme[0]['mc']} {top10_with_theme[0]['cje']/1e8:.0f}亿")
