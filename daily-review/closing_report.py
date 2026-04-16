#!/usr/bin/env python3
"""
A股短线情绪收盘数据采集 — 短线复盘版本一（2026-04-16 锁定）
用法：python3 closing_report.py              # 默认今天
      python3 closing_report.py 2026-04-16    # 指定日期
"""
import urllib.request
import json
import ssl
import datetime
import sys
import os
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# ══════════════════════════════════════════════════════
# 配置
# ══════════════════════════════════════════════════════
BASE = "https://api.biyingapi.com"
TOKEN = "60D084A7-FF4A-4B42-9E1C-45F0B719F33C"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 日期参数：命令行指定 或 自动取今天
DATE = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y-%m-%d")

# 报告收集器
report_lines = []

def log(msg=""):
    """
    打印消息并收集到报告列表中
    """
    print(msg)
    report_lines.append(msg)

EXCLUDE_PREFIXES = (
    'A股-分类', 'A股-指数成分', 'A股-证监会行业',
    'A股-申万行业', 'A股-申万二级', 'A股-地域板块',
    '基金-', '港股-', '美股-'
)
def is_noise_tag(name):
    """判断是否为噪音标签"""
    if any(name.startswith(p) for p in EXCLUDE_PREFIXES):
        return True
    # 取最后一段判断（如 "A股-热门概念-小盘" → "小盘"）
    short = name.split('-')[-1] if '-' in name else name
    return short.strip() in NOISE_TAGS

NOISE_TAGS = {
    '小盘', '中盘', '大盘', '融资融券', '富时罗素',
    'MSCI中国', '标普道琼斯', '深股通', '沪股通',
    '预增', '预减', '扭亏', '续亏', '增持', '回购',
}

INDEX_CODES = [
    ("上证指数", "000001", "SH"),
    ("深证成指", "399001", "SZ"),
    ("创业板指", "399006", "SZ"),
    ("科创50",  "000688", "SH"),
]


# ══════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════
def api(path, allow_404=False):
    """必盈API请求"""
    url = f"{BASE}/{path}/{TOKEN}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404 and allow_404:
            return []
        raise


def api_fin(api_name, params, fields=""):
    """finance-data 接口"""
    body = json.dumps({"api_name": api_name, "params": params, "fields": fields}).encode()
    req = urllib.request.Request(
        "https://www.codebuddy.cn/v2/tool/financedata",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        result = json.loads(r.read())
    if result.get("code") != 0:
        return {}
    data = result.get("data", {})
    fields_list = data.get("fields", [])
    items = data.get("items", [])
    if not items:
        return {}
    return dict(zip(fields_list, items[0]))


def parse_pool(raw):
    """解析涨停/跌停/炸板池"""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for k in ("data", "result", "list"):
            v = raw.get(k)
            if isinstance(v, list):
                return v
    return []


def filter_st(stocks):
    """过滤ST股"""
    return [s for s in stocks if 'ST' not in s.get('mc', '') and '*' not in s.get('mc', '')]


def yi(v):   # 元转亿
    v = float(v)
    if v >= 1e8:   return f"{v/1e8:.2f}亿"
    if v >= 1e4:    return f"{v/1e4:.0f}万"
    return f"{v:.0f}元"


def pct_chg(c, pc):
    try:
        c, pc = float(c), float(pc)
        return (c - pc) / pc * 100 if pc else 0.0
    except:
        return 0.0


def color_pct(v):
    """涨绿🔼 跌红🔽"""
    v = float(v)
    if v > 0:  return f"🔼+{v:.2f}%"
    if v < 0:  return f"🔽{v:.2f}%"
    return "➖ 0.00%"


def get_trading_days(end_date_str, count=5):
    """最近count个交易日（跳过周末）"""
    end = datetime.date.fromisoformat(end_date_str)
    days, d = [], end
    while len(days) < count:
        if d.weekday() < 5:
            days.append(d)
        d -= datetime.timedelta(days=1)
    return days


def fetch_theme(stock):
    """查询单只股票题材"""
    dm = stock.get('dm', '')
    mc = stock.get('mc', '')
    try:
        raw = api(f"hszg/zg/{dm}")
        data = []
        if isinstance(raw, dict):
            data = raw.get('data', []) or raw.get('result', []) or []
        elif isinstance(raw, list):
            data = raw
        themes = []
        for item in data:
            name = ''
            if isinstance(item, dict):
                name = item.get('name') or item.get('mc') or item.get('plate') or item.get('idea') or ''
            elif isinstance(item, str):
                name = item
            if name and not is_noise_tag(name):
                themes.append(name)
        return mc, dm, themes
    except:
        return mc, dm, []


# ══════════════════════════════════════════════════════
# 数据采集
# ══════════════════════════════════════════════════════
print(f"📅 目标日期: {DATE}")
print("-" * 50)

# ── 模块一：四大指数 ──
print("[1/9] 四大指数查询...")
indices = []; market_amount = 0
DATE_FMT = DATE.replace("-", "")
for name, code, mkt in INDEX_CODES:
    ts_code = f"{code}.{mkt}"
    # 使用 finance-data 接口获取指定日期的指数数据
    data = api_fin("index_daily", {"ts_code": ts_code, "trade_date": DATE_FMT})
    if data:
        c = float(data.get('close', 0))
        pc = float(data.get('pre_close', 0))
        amt = float(data.get('amount', 0)) * 1000
        indices.append((name, c, pct_chg(c, pc)))
        if code in ("000001", "399001"):
            market_amount += amt
    else:
        # 如果 finance-data 没查到，降级使用最新数据接口
        raw = api(f"hsindex/latest/{code}.{mkt}/d")
        klines = raw if isinstance(raw, list) else []
        if klines:
            latest = klines[0]
            c, pc = float(latest.get('c', 0)), float(latest.get('pc', 0))
            amt = float(latest.get('a', 0))
            indices.append((name, c, pct_chg(c, pc)))
            if code in ("000001", "399001"):
                market_amount += amt

# ── 模块二：市场全景 ──
print("[2/9] 市场全景查询...")
zt_raw = api(f"hslt/ztgc/{DATE}")
dt_raw = api(f"hslt/dtgc/{DATE}")
zb_raw = api(f"hslt/zbgc/{DATE}")
qs_raw = api(f"hslt/qsgc/{DATE}")

zt_list = filter_st(parse_pool(zt_raw))
dt_list = filter_st(parse_pool(dt_raw))
zb_list = filter_st(parse_pool(zb_raw))
qs_list = filter_st(parse_pool(qs_raw))

zt_count, dt_count, zb_count, qs_count = len(zt_list), len(dt_list), len(zb_list), len(qs_list)
fbl = zt_count / (zt_count + zb_count) * 100 if (zt_count + zb_count) > 0 else 0

# 获取全市场涨跌家数 (通过 api_fin 获取市场宽度)
up_count, down_count = 0, 0
breadth = api_fin("index_daily", {"ts_code": "000001.SH", "trade_date": DATE_FMT}, "advance,decline")
if breadth:
    up_count = int(breadth.get('advance', 0))
    down_count = int(breadth.get('decline', 0))

# ── 模块三：连板天梯 ──
print("[3/9] 连板天梯查询...")
by_lbc = defaultdict(list)
for s in zt_list:
    by_lbc[s.get('lbc', 1)].append(s)
max_lbc = max(by_lbc.keys()) if by_lbc else 1

# T-1涨停池（用于判断晋级）
yesterday_date = (datetime.date.fromisoformat(DATE) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
zt_y_raw = api(f"hslt/ztgc/{yesterday_date}", allow_404=True)
zt_y = filter_st(parse_pool(zt_y_raw))
zt_y_codes = {s['dm'] for s in zt_y}

lines = []
for lbc in sorted(by_lbc.keys(), reverse=True):
    stocks = sorted(by_lbc[lbc], key=lambda x: -float(x.get('zf', 0)))
    names = [f"{s['mc']}({s.get('lbc','?')}板)" for s in stocks]
    tag = "🔴最高板" if lbc == max_lbc else (f"⭐{lbc}板" if lbc > 1 else "首板")
    promoted = [s for s in stocks if s['dm'] in zt_y_codes]
    broken   = [s for s in stocks if s['dm'] not in zt_y_codes]
    p_str = "✅" + "/".join([s['mc'] for s in promoted]) if promoted else ""
    b_str = "❌" + "/".join([s['mc'] for s in broken]) if broken else ""
    lines.append((lbc, tag, names, p_str, b_str))

# ── 模块六：核按钮 ──
print("[4/9] 核按钮/大面股查询...")
dt_sorted = sorted(dt_list, key=lambda x: -float(x.get('zj', 0)))
zb_sorted = sorted(zb_list, key=lambda x: -float(x.get('zbc', 0)))

# ── 昨日涨停今表现数据准备 ──
print("[5/9] 昨日涨停表现查询...")
qs_codes = {s['dm'] for s in qs_list}

# ── 题材分析 ──
print(f"[6/9] 题材分析（{len(zt_list)}只并发查询）...")
theme_counter = Counter(); stock_themes = {}; theme_stocks = {}

with ThreadPoolExecutor(max_workers=20) as pool:
    futures = {pool.submit(fetch_theme, s): s for s in zt_list}
    done = 0
    for fut in as_completed(futures):
        mc, dm, themes = fut.result()
        done += 1
        if done % 20 == 0:
            print(f"       进度: {done}/{len(zt_list)}")
        stock_themes[mc] = themes
        seen = set()
        for t in themes:
            if t and t not in seen:
                theme_counter[t] += 1; seen.add(t)
                if t not in theme_stocks: theme_stocks[t] = []
                theme_stocks[t].append(mc)

top_themes = theme_counter.most_common(5)

# ── 近5日连板高度 & 量能 & 7日趋势 ──
print("[7/9] 历史趋势数据查询...")
trading_5 = get_trading_days(DATE, 5)
trading_7 = get_trading_days(DATE, 7)

height_days = []
volume_days = []
for day in trading_5:
    day_str = day.strftime("%Y-%m-%d"); day_fmt = day.strftime("%Y%m%d")
    
    # 连板高度
    raw_h = api(f"hslt/ztgc/{day_str}", allow_404=True)
    pool_h = filter_st(parse_pool(raw_h))
    if pool_h:
        mh = max(s.get('lbc', 1) for s in pool_h)
        gem_boards = [s.get('lbc', 1) for s in pool_h if '创业板' in s.get('mc','') or s.get('dm','').startswith('3')]
        gm = max(gem_boards) if gem_boards else 1
        height_days.append((day_str, mh, gm, len(pool_h)))
    else:
        height_days.append((day_str, 0, 0, 0))
    
    # 两市成交额
    sh_amt_d = api_fin("index_daily", {"ts_code":"000001.SH","trade_date":day_fmt}, "amount")
    sz_amt_d = api_fin("index_daily", {"ts_code":"399001.SZ","trade_date":day_fmt}, "amount")
    sh_amt = float(sh_amt_d.get('amount',0))*1000 if sh_amt_d.get('amount') else 0
    sz_amt = float(sz_amt_d.get('amount',0))*1000 if sz_amt_d.get('amount') else 0
    zt_n = len(pool_h)
    volume_days.append((day.strftime("%Y-%m-%d"), sh_amt+sz_amt, zt_n))

# 7日趋势
trend_days = []
for day in trading_7:
    ds = day.strftime("%Y-%m-%d")
    raw_t = api(f"hslt/ztgc/{ds}", allow_404=True)
    dt_r  = api(f"hslt/dtgc/{ds}", allow_404=True)
    trend_days.append((ds, len(filter_st(parse_pool(raw_t))), len(filter_st(parse_pool(dt_r)))))

# 统一反转顺序，使报告输出为从旧到新的时间线
height_days.reverse()
volume_days.reverse()
trend_days.reverse()

log("[8/9] 数据就绪整理...")

# ══════════════════════════════════════════════════════
# 输出报告
# ══════════════════════════════════════════════════════
log("\n")
log("=" * 70)
log(f"  📊 A股短线情绪收盘简报  {DATE}  |  短线复盘版本一")
log("=" * 70)

# 一、四大指数
log("\n一、四大指数"); log("-" * 50)
for name, close, chg in indices:
    log(f"  {name:<8s} {close:>10.2f}  {color_pct(chg)}")
if market_amount > 0:
    log(f"\n  两市总成交额  {yi(market_amount)}")

# 二、市场全景
log(f"\n二、市场全景"); log("-" * 50)
breadth_str = f"上涨 {up_count} vs 下跌 {down_count}" if up_count or down_count else ""
log(f"  {breadth_str}  |  涨停 🔥{zt_count}只  |  炸板 💥{zb_count}只  |  跌停 ⬇️{dt_count}只  |  封板率 {fbl:.1f}%")

# 三、连板天梯
log(f"\n三、连板天梯"); log("-" * 50)
for lbc, tag, names, p_str, b_str in lines:
    indent = "  " + ("│ " * (max_lbc - lbc))
    ns = " / ".join(names[:10]) + (f" ...(+{len(names)-10}只)" if len(names)>10 else "")
    log(f"{indent}┌─{tag} {ns}")
    if p_str or b_str:
        log(f"{indent}│  {p_str} {b_str}".strip())

# 四、近5日连板高度
log(f"\n四、近5日连板高度"); log("-" * 50)
log(f"  {'日期':<12s} {'全市场高度':>12s} {'创业板':>8s} {'涨停数':>6s}")
for ds, mh, gm, zn in height_days:
    m = " ◀今日" if ds == DATE else ""
    log(f"  {ds:<12s} {'🔴'*min(mh,6):>10s}({mh}板) {'🔺'*min(gm,6):>6s}({gm}板) {zn:>4d}{m}")

# 五、近5日量能
log(f"\n五、近5日两市成交额"); log("-" * 50)
log(f"  {'日期':<12s} {'成交额':>12s} {'日环比':>10s} {'涨停数':>6s}")
for i, (ds, amt, zn) in enumerate(volume_days):
    if i == 0:
        chg_s = "—"
    else:
        chg_s = color_pct((amt - volume_days[i-1][1]) / volume_days[i-1][1] * 100)
    m = " ◀今日" if ds == DATE else ""
    log(f"  {ds:<12s} {yi(amt):>12s} {chg_s:>10s} {zn:>4d}{m}")

# 六、核按钮
log(f"\n六、核按钮 / 大面股"); log("-" * 50)
if top_dt := dt_sorted[:5]:
    for s in top_dt:
        log(f"  ⬇️ {s['mc']:<10s} 封单 {yi(s.get('zj',0))}")
if zb_top := zb_sorted[:3]:
    for s in zb_top:
        log(f"  ⚠️ {s['mc']:<10s} 炸板{s.get('zbc',0)}次  成交{yi(s.get('fba','0'))}")

# 七、7日趋势
log(f"\n七、近7日情绪趋势"); log("-" * 50)
log(f"  {'日期':<12s} {'涨停':>6s} {'跌停':>6s} {'信号':>8s}")
for ds, zc, dc in trend_days:
    sig = "🔥升温" if zc>=60 else ("❄️降温" if zc<=30 else "➡️平稳")
    m = " ◀今日" if ds==DATE else ""
    log(f"  {ds:<12s} {zc:>6d} {dc:>6d} {sig:>8s}{m}")

# 八、昨日涨停今表现（简化）
log(f"\n八、昨日涨停今日表现"); log("-" * 50)
yzt_qs = len([s for s in zt_y if s['dm'] in qs_codes])
log(f"  昨日涨停{len(zt_y)}只 → 今日仍在强势池 {yzt_qs}只 ({yzt_qs/max(len(zt_y),1)*100:.0f}%)")
if yzt_in := [s for s in zt_y if s['dm'] in qs_codes]:
    yzt_sorted = sorted(yzt_in, key=lambda x: -float(x.get('zf',0)))
    top3 = yzt_sorted[:3]
    names = " / ".join([f"{s['mc']}({color_pct(float(s.get('zf',0))).strip()})" for s in top3])
    log(f"  表现最好TOP3: {names}")

# 九、最强题材TOP5
log(f"\n九、最强题材TOP5"); log("-" * 50)
for rank, (theme, cnt) in enumerate(top_themes, 1):
    stks = theme_stocks.get(theme, [])
    boards = [f"{s['mc']}({s['lbc']}板)" for s in zt_list if s['mc'] in stks and s.get('lbc',1)>1]
    bs = " │ "+"/".join(boards[:4]) if boards else ""
    log(f"  {rank}. 【{theme}】 {cnt}只{bs}")

# 十一、核心判断
log(f"\n十一、核心判断"); log("-" * 50)
today_v = volume_days[-1][1]
prev_v  = volume_days[-2][1] if len(volume_days)>1 else today_v
vd = (today_v - prev_v)/prev_v*100 if prev_v else 0
tt_name = top_themes[0][0] if top_themes else "未知"
tt_cnt  = top_themes[0][1] if top_themes else 0
sig = "🔴短线情绪良好" if zt_count>=60 and fbl>=75 else ("🟡情绪分化" if zt_count>=40 else "🔵情绪低迷")
log(f"  📌 信号：{sig}")
log(f"  📊 量能：{yi(today_v)}  较昨日{color_pct(vd)}")
log(f"  📋 封板率：{fbl:.1f}%  {'✅正常' if 65<=fbl<=80 else ('⚠️偏高' if fbl>80 else '⚠️偏低')}")
log(f"  🔥 最强题材：【{tt_name}】 {tt_cnt}只涨停")
if tt_cnt >= 15:
    log(f"  👉 看点：题材明确，{tt_name}为主线，关注龙头梯队完整度")
elif tt_cnt >= 8:
    log(f"  👉 看点：题材有所表现，跟随强势标的为主")
else:
    log(f"  👉 看点：题材散乱，缺乏明确主线，谨慎追高")

log("\n" + "=" * 70)
log(f"  ✅ 完成  |  {datetime.datetime.now().strftime('%H:%M:%S')}")
log("=" * 70)

# ══════════════════════════════════════════════════════
# 保存到文件
# ══════════════════════════════════════════════════════
file_name = f"每日复盘{DATE}.txt"
# 统一保存在 text 目录下
text_dir = os.path.join(os.path.dirname(__file__), "text")
if not os.path.exists(text_dir):
    os.makedirs(text_dir)

file_path = os.path.join(text_dir, file_name)
try:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\n💾 报告已自动保存至: {file_path}")
    
    # ══════════════════════════════════════════════════════
    # 自动更新 HTML 报告
    # ══════════════════════════════════════════════════════
    update_script = os.path.join(os.path.dirname(__file__), "update_report_html.py")
    if os.path.exists(update_script):
        print("\n🎨 正在同步更新 HTML 可视化报告...")
        os.system(f'python3 "{update_script}"')
        
except Exception as e:
    print(f"\n❌ 处理报告失败: {e}")
