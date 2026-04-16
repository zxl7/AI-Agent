import os
import re
import datetime
import sys

def parse_report(file_path):
    """
    解析文本复盘报告
    """
    if not os.path.exists(file_path):
        return None
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = {}
    # 提取日期
    date_match = re.search(r'📊 A股短线情绪收盘简报\s+(\d{4}-\d{2}-\d{2})', content)
    if date_match:
        data['date'] = date_match.group(1)
    else:
        date_match = re.search(r'📅 目标日期: (\d{4}-\d{2}-\d{2})', content)
        if date_match:
            data['date'] = date_match.group(1)
    
    # 提取指数
    indices = []
    index_section = re.search(r'一、四大指数\n-+\n(.*?)\n\n', content, re.S)
    if index_section:
        for line in index_section.group(1).strip().split('\n'):
            if not line.strip() or '成交额' in line: continue
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 3:
                name = parts[0]
                val = parts[1]
                pct = parts[2]
                indices.append({'name': name, 'val': val, 'pct': pct, 'up': '🔼' in pct})
    data['indices'] = indices

    # 提取量能信息 (包含环比和增量)
    vol_match = re.search(r'📊 量能：([\d.]+亿)\s+较昨日(.*?)\s+\(增量 (.*?)\)', content)
    if vol_match:
        data['total_volume'] = vol_match.group(1)
        data['vol_change_pct'] = vol_match.group(2).strip()
        data['vol_increment'] = vol_match.group(3).strip()
    else:
        vol_match = re.search(r'📊 量能：([\d.]+亿)', content)
        if vol_match:
            data['total_volume'] = vol_match.group(1)
            data['vol_change_pct'] = "—"
            data['vol_increment'] = "—"

    # 提取成交额历史 (用于量能折线图)
    volume_history = []
    vol_history_section = re.search(r'五、近5日两市成交额\n-+\n.*?\n(.*?)\n\n', content, re.S)
    if vol_history_section:
        for line in vol_history_section.group(1).strip().split('\n'):
            m = re.search(r'(\d{4}-\d{2}-\d{2})\s+([\d.]+)亿\s+(.*?)\s+(\d+)', line)
            if m:
                change_str = m.group(3).strip()
                # 提取纯百分比数字用于绘图
                pct_m = re.search(r'([+-][\d.]+)%', change_str)
                pct_val = float(pct_m.group(1)) if pct_m else 0.0
                volume_history.append({
                    'date': m.group(1),
                    'amount': float(m.group(2)),
                    'change': change_str,
                    'pct_val': pct_val,
                    'date_short': m.group(1)[5:]
                })
    data['volume_history'] = volume_history

    # 提取市场全景 (适配新模板)
    stats_match = re.search(r'上涨 (\d+) vs 下跌 (\d+)  \|  涨停 🔥(\d+)只\s+\|\s+炸板 💥(\d+)只\s+\|\s+跌停 ⬇️(\d+)只\s+\|\s+封板率 ([\d.]+)%', content)
    if stats_match:
        data['up_count'] = stats_match.group(1)
        data['down_count'] = stats_match.group(2)
        data['zt_count'] = stats_match.group(3)
        data['zb_count'] = stats_match.group(4)
        data['dt_count'] = stats_match.group(5)
        data['fbl'] = stats_match.group(6)
    else:
        # 兼容旧格式
        stats_match = re.search(r'涨停 🔥(\d+)只\s+\|\s+炸板 💥(\d+)只\s+\|\s+跌停 ⬇️(\d+)只\s+\|\s+强势 ⭐(\d+)只\s+\|\s+封板率 ([\d.]+)%', content)
        if stats_match:
            data['up_count'] = "0"
            data['down_count'] = "0"
            data['zt_count'] = stats_match.group(1)
            data['zb_count'] = stats_match.group(2)
            data['dt_count'] = stats_match.group(3)
            data['fbl'] = stats_match.group(5)

    # 提取连板天梯表格数据
    ladder_data = []
    ladder_section = re.search(r'三、连板天梯\n-+\n(.*?)\n\n', content, re.S)
    if ladder_section:
        lines = ladder_section.group(1).split('\n')
        current_lbc = ""
        for line in lines:
            line = line.strip()
            # 匹配高度行: ┌─🔴最高板 圣阳股份(6板) 或 ┌─⭐4板 博云新材(4板)
            m_h = re.search(r'┌─(.*?)\s+(.*)\((\d+)板\)', line)
            if m_h:
                current_lbc = f"{m_h.group(3)}板"
                stocks = m_h.group(2).split(' / ')
                for s in stocks:
                    s_name = s.strip().split('(')[0]
                    ladder_data.append({
                        'height': current_lbc,
                        'name': s_name,
                        'status': '晋级',
                        'detail': f'晋级{current_lbc}'
                    })
            # 匹配详情行: ✅圣阳股份 或 ❌华谊兄弟/锦鸡股份...
            elif line.startswith('✅') or line.startswith('❌'):
                is_ok = line.startswith('✅')
                stocks_part = line[1:].strip()
                # 我们只记录晋级的
                if not is_ok:
                    # 如果是❌，通常是断板的。但在当前的报告格式中，这些是"新涨停"或"首板"
                    pass

    data['ladder'] = ladder_data

    # 提取历史趋势 (5-7日)
    history = []
    trend_section = re.search(r'七、近7日情绪趋势\n-+\n.*?\n(.*?)\n\n', content, re.S)
    if trend_section:
        for line in trend_section.group(1).strip().split('\n'):
            m = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d+)\s+(\d+)', line)
            if m:
                history.append({
                    'date': m.group(1),
                    'zt': int(m.group(2)),
                    'dt': int(m.group(3)),
                    'date_short': m.group(1)[5:]
                })
    data['history'] = history

    # 提取连板高度历史
    height_history = []
    height_section = re.search(r'四、近5日连板高度\n-+\n.*?\n(.*?)\n\n', content, re.S)
    if height_section:
        for line in height_section.group(1).strip().split('\n'):
            m = re.search(r'(\d{4}-\d{2}-\d{2}).*?\((\d+)板\).*?\((\d+)板\)\s+(\d+)', line)
            if m:
                height_history.append({
                    'date': m.group(1),
                    'height': int(m.group(2)),
                    'gem_height': int(m.group(3))
                })
    data['height_history'] = height_history

    # 提取题材
    themes = []
    theme_section = re.search(r'九、最强题材TOP5\n-+\n(.*?)\n\n', content, re.S)
    if theme_section:
        for line in theme_section.group(1).strip().split('\n'):
            m = re.search(r'\d+\. 【(.*?)】 (\d+)只', line)
            if m:
                themes.append({'name': m.group(1), 'count': m.group(2)})
    data['themes'] = themes

    # 提取核心判断
    verdict_section = re.search(r'十一、核心判断\n-+\n(.*?)\n\n', content, re.S)
    if verdict_section:
        data['verdict'] = verdict_section.group(1).strip()
    
    return data

def generate_trend_svg(data):
    """
    生成趋势图 SVG (整合涨停、跌停和高度)
    """
    history = data['history']
    height_hist = {h['date']: h['height'] for h in data['height_history']}
    
    width = 500
    height = 240
    padding_x = 50
    padding_y = 40
    
    if not history: return ""
    
    # X 轴刻度
    x_step = (width - 2 * padding_x) / (len(history) - 1) if len(history) > 1 else 0
    
    # 涨停折线
    max_zt = max(h['zt'] for h in history) if history else 100
    y_scale = (height - 2 * padding_y) / max(max_zt, 150)
    
    zt_points = []
    dt_points = []
    h_points = []
    
    for i, h in enumerate(history):
        x = padding_x + i * x_step
        # 涨停
        y_zt = height - padding_y - h['zt'] * y_scale
        zt_points.append(f"{x},{y_zt}")
        # 跌停
        y_dt = height - padding_y - h['dt'] * y_scale
        dt_points.append(f"{x},{y_dt}")
        # 高度 (使用单独的右侧轴或叠加)
        h_val = height_hist.get(h['date'], 0)
        y_h = height - padding_y - h_val * (height - 2 * padding_y) / 10 # 假设最高10板
        h_points.append(f"{x},{y_h}")

    svg = f"""
    <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
      <rect x="{padding_x}" y="{padding_y}" width="{width-2*padding_x}" height="{height-2*padding_y}" fill="#fafafa" rx="8"/>
      
      <!-- 涨停折线 -->
      <polyline points="{" ".join(zt_points)}" fill="none" stroke="#ef4444" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      <!-- 跌停折线 -->
      <polyline points="{" ".join(dt_points)}" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4,2"/>
      <!-- 高度折线 -->
      <polyline points="{" ".join(h_points)}" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      
      <!-- 数据点和标签 -->
    """
    for i, h in enumerate(history):
        x = padding_x + i * x_step
        y_zt = height - padding_y - h['zt'] * y_scale
        svg += f'<circle cx="{x}" cy="{y_zt}" r="4" fill="#ef4444"/>'
        svg += f'<text x="{x}" y="{y_zt-8}" text-anchor="middle" fill="#ef4444" font-size="10" font-weight="700">{h["zt"]}</text>'
        
        y_h = height - padding_y - height_hist.get(h['date'], 0) * (height - 2 * padding_y) / 10
        svg += f'<circle cx="{x}" cy="{y_h}" r="4" fill="#2563eb"/>'
        svg += f'<text x="{x}" y="{y_h-8}" text-anchor="middle" fill="#2563eb" font-size="10" font-weight="700">{height_hist.get(h["date"], 0)}板</text>'
        
        svg += f'<text x="{x}" y="{height-15}" text-anchor="middle" fill="#64748b" font-size="10">{h["date_short"]}</text>'
        
    svg += """
      <g transform="translate(100, 230)">
        <line x1="0" y1="0" x2="15" y2="0" stroke="#ef4444" stroke-width="2"/>
        <text x="20" y="4" fill="#64748b" font-size="10">涨停</text>
        <line x1="70" y1="0" x2="85" y2="0" stroke="#2563eb" stroke-width="2"/>
        <text x="90" y="4" fill="#64748b" font-size="10">高度</text>
        <line x1="140" y1="0" x2="155" y2="0" stroke="#10b981" stroke-width="2" stroke-dasharray="3,1"/>
        <text x="160" y="4" fill="#64748b" font-size="10">跌停</text>
      </g>
    </svg>
    """
    return svg

def generate_volume_chart_svg(history):
    """
    生成成交额环比趋势折线图 SVG
    """
    if not history: return ""
    width, height = 500, 140
    px, py = 50, 30
    
    # 使用百分比变化作为 Y 轴
    # 为保证 0 轴在中间，我们取最大绝对值
    max_abs_pct = max([abs(h['pct_val']) for h in history] + [3.0])
    y_range = max_abs_pct * 1.2
    
    x_step = (width - 2 * px) / (len(history) - 1) if len(history) > 1 else 0
    y_scale = (height - 2 * py) / (2 * y_range)
    y_zero = height / 2
    
    points = []
    for i, h in enumerate(history):
        x = px + i * x_step
        y = y_zero - h['pct_val'] * y_scale
        points.append(f"{x},{y}")
    
    polyline = f'<polyline points="{" ".join(points)}" fill="none" stroke="#f59e0b" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
    
    nodes = ""
    labels = ""
    x_axis = ""
    for i, h in enumerate(history):
        x = px + i * x_step
        y = y_zero - h['pct_val'] * y_scale
        nodes += f'<circle cx="{x}" cy="{y}" r="4" fill="#f59e0b" stroke="#fff" stroke-width="2"/>'
        # 只有最后一个点显示“今”
        label_text = "今" if i == len(history)-1 else ""
        if label_text:
            labels += f'<text x="{x}" y="{y-10}" text-anchor="middle" fill="#f59e0b" font-size="12" font-weight="700">{label_text}</text>'
        x_axis += f'<text x="{x}" y="{height-5}" text-anchor="middle" fill="#94a3b8" font-size="10">{h["date_short"]}</text>'

    # Y 轴刻度
    y_ticks = ""
    for p in [-3, 0, 3]:
        if abs(p) > y_range: continue
        y = y_zero - p * y_scale
        y_ticks += f'<line x1="{px}" y1="{y}" x2="{width-px}" y2="{y}" stroke="#e2e8f0" stroke-dasharray="4,4"/>'
        y_ticks += f'<text x="{px-5}" y="{y+4}" text-anchor="end" fill="#94a3b8" font-size="9">{p:+}%%</text>'

    return f"""
    <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
      {y_ticks}
      {polyline}
      {nodes}
      {labels}
      {x_axis}
    </svg>
    """

def generate_html(data, template_path, output_path):
    """
    基于模板生成最终 HTML
    """
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return
        
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    css_match = re.search(r'<style>(.*?)</style>', template, re.S)
    css = css_match.group(1) if css_match else ""
    
    # 1. 指数卡片
    index_html = ""
    for idx in data['indices']:
        color_class = "up" if idx['up'] else "down"
        index_html += f"""
        <div class="index-card">
          <div class="index-name">{idx['name']}</div>
          <div class="index-val">{idx['val']}</div>
          <div class="index-pct {color_class}">{idx['pct']}</div>
        </div>"""
        
    # 2. 板块 TOP5
    sector_html = ""
    for i, theme in enumerate(data['themes'], 1):
        rank_class = f"rank-{i}" if i <= 3 else "rank-n"
        sector_html += f"""
        <li class="sector-item">
          <span class="sector-rank {rank_class}">{i}</span>
          <div class="sector-info">
            <div class="sector-name">{theme['name']}</div>
            <div class="sector-detail">{theme['count']}只涨停</div>
          </div>
          <div class="sector-pct" style="color:#f59e0b;">—</div>
        </li>"""
        
    # 3. 连板天梯
    ladder_html = ""
    for item in data['ladder']:
        badge_class = f"badge-{item['height'].replace('板','')}" if item['height'].replace('板','').isdigit() else "badge-1"
        ladder_html += f"""
        <tr>
          <td><span class="ladder-badge {badge_class}">{item['height']}</span></td>
          <td class="stock-name-cell">{item['name']}</td>
          <td>{item['status']}</td>
          <td class="dest-good">✅ {item['detail']}</td>
          <td style="font-size:11.5px;color:#64748b;">-</td>
        </tr>"""

    # 4. 趋势图
    trend_svg = generate_trend_svg(data)
    vol_chart_svg = generate_volume_chart_svg(data['volume_history'])
    
    # 组装最终 HTML
    final_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A股收盘简报 | {data['date']}</title>
<style>{css}</style>
<style>
  .market-vol-box {{ background:#f8fafc; border-radius:16px; padding:20px; margin-bottom:16px; border:1px solid #e2e8f0; }}
  .vol-header-row {{ display:flex; align-items:center; gap:12px; margin-bottom:12px; }}
  .vol-icon {{ font-size:24px; color:#1e293b; opacity:0.7; }}
  .vol-main-info {{ display:flex; flex-direction:column; }}
  .vol-label-top {{ font-size:12px; color:#94a3b8; margin-bottom:2px; }}
  .vol-value-row {{ display:flex; align-items:baseline; gap:12px; }}
  .vol-total {{ font-size:24px; font-weight:800; color:#1e293b; }}
  .vol-change {{ font-size:16px; font-weight:700; color:#ef4444; }}
  .market-summary-box {{ background:#f8fafc; border-radius:12px; padding:16px; border-left:4px solid #f59e0b; font-size:14px; line-height:1.6; color:#334155; margin-bottom:20px; }}
  
  /* 市场全景四格卡片 */
  .overview-grid {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; margin-bottom:20px; }}
  .overview-card {{ background:#f8fafc; border-radius:12px; padding:16px 8px; text-align:center; }}
  .overview-num {{ font-size:28px; font-weight:800; margin-bottom:4px; }}
  .overview-label {{ font-size:12px; color:#94a3b8; }}
</style>
</head>
<body>
<div class="container">
  <div class="hero">
    <div class="hero-top">
      <div>
        <div class="cycle-tag"><span class="cycle-dot"></span>短线复盘 · 情绪监控</div>
        <div class="hero-date">{data['date'].replace('-','年')+'日'}收盘简报</div>
        <div class="hero-subtitle">数据来源：必盈API | 自动生成报告</div>
      </div>
    </div>
    <div class="index-row">{index_html}</div>
  </div>

  <div class="card">
    <div class="card-title"><div class="card-icon" style="background:#2563eb;">📈</div>市场量能</div>
    
    <div class="market-vol-box">
      <div class="vol-header-row">
        <div class="vol-icon">⇄</div>
        <div class="vol-main-info">
          <div class="vol-label-top">沪深 | 实际量能 较昨日</div>
          <div class="vol-value-row">
            <span class="vol-total">{data['total_volume']}</span>
            <span class="vol-change">{data['vol_change_pct']} · 增量 {data['vol_increment']}</span>
          </div>
        </div>
      </div>
      <div class="chart-container" style="height:140px; margin-bottom:0;">
        {vol_chart_svg}
      </div>
    </div>

    <div class="market-summary-box">
      📊 {'涨多跌少' if int(data['up_count']) > int(data['down_count']) else '涨少跌多'} ({data['up_count']} vs {data['down_count']})，
      但涨停{data['zt_count']}家、封板率{data['fbl']}%显示短线情绪{'良好' if float(data['fbl']) > 70 else '一般'}。
      <strong style="color:#ef4444;">量能增量{data['vol_increment']}({data['vol_change_pct']})</strong>，资金仍在博弈。
    </div>

    <div class="card-title" style="margin-top:20px;"><div class="card-icon" style="background:#3b82f6;">📊</div>市场全景</div>
    <div class="overview-grid">
      <div class="overview-card">
        <div class="overview-num" style="color:#ef4444;">{data['zt_count']}</div>
        <div class="overview-label">涨停(非ST)</div>
      </div>
      <div class="overview-card">
        <div class="overview-num" style="color:#f59e0b;">{data['zb_count']}</div>
        <div class="overview-label">炸板</div>
      </div>
      <div class="overview-card">
        <div class="overview-num" style="color:#10b981;">{data['dt_count']}</div>
        <div class="overview-label">跌停(非ST)</div>
      </div>
      <div class="overview-card">
        <div class="overview-num" style="color:#f59e0b;">{data['fbl']}%</div>
        <div class="overview-label">封板率</div>
      </div>
    </div>
    
    <div class="section-header" style="border-left-color:#6366f1;">情绪趋势跟踪</div>
    <div class="chart-container">{trend_svg}</div>
  </div>

  <div class="card">
    <div class="card-title"><div class="card-icon" style="background:#f59e0b;">🏆</div>连板天梯</div>
    <table class="ladder-table">
      <thead><tr><th>高度</th><th>股票名称</th><th>状态</th><th>今日去向</th><th>备注</th></tr></thead>
      <tbody>{ladder_html}</tbody>
    </table>
  </div>

  <div class="card">
    <div class="card-title"><div class="card-icon" style="background:#ec4899;">🏅</div>板块强度 TOP5</div>
    <ul class="sector-list">{sector_html}</ul>
  </div>

  <div class="card">
    <div class="card-title"><div class="card-icon" style="background:#10b981;">📋</div>核心判断</div>
    <div class="verdict-box verdict-warn">
      {data['verdict'].replace('\n', '<br/>')}
    </div>
  </div>

  <div class="footer">
    <p>📊 生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <p>本报告由自动化系统生成，仅供参考。</p>
  </div>
</div>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    print(f"✅ HTML 报告已重新生成: {output_path}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    text_dir = os.path.join(base_dir, "text")
    template_path = os.path.join(base_dir, "复盘.html")
    output_path = os.path.join(base_dir, "短线复盘利器.html")
    
    files = [f for f in os.listdir(text_dir) if f.startswith("每日复盘") and f.endswith(".txt")]
    if not files: return
    files.sort(reverse=True)
    latest_report = os.path.join(text_dir, files[0])
    
    data = parse_report(latest_report)
    if data:
        generate_html(data, template_path, output_path)

if __name__ == "__main__":
    main()
