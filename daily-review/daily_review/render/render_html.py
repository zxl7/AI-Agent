#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模板渲染器（A方案的第一步）

职责：
1) 读取 HTML 模板文件（report_template.html）
2) 注入 marketData JSON（替换模板中的 /*__MARKET_DATA_JSON__*/ null）
3) 替换 __REPORT_DATE__ / __DATE_NOTE__ 等占位符

说明：
- 该脚本只负责“渲染”，不负责任何数据抓取与指标计算。
- 这样可以保证原始 HTML/CSS/JS 结构不变，只替换数据，从而 1:1 保持视觉效果。
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict


def render_html_template(
    *,
    template_path: Path,
    output_path: Path,
    market_data: Dict[str, Any],
    report_date: str,
    date_note: str = "",
) -> None:
    tpl = template_path.read_text(encoding="utf-8")

    market_data_js = json.dumps(market_data, ensure_ascii=False)

    # 1) 注入 marketData
    tpl = tpl.replace("/*__MARKET_DATA_JSON__*/ null", market_data_js)

    # 2) 注入日期类占位符
    tpl = tpl.replace("__REPORT_DATE__", report_date)
    tpl = tpl.replace("__DATE_NOTE__", date_note or "")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(tpl, encoding="utf-8")


def build_action_guide_v2(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    明日计划（行动指南）算法：只基于已有 market_data 推导，不做任何外部请求。
    输出结构与前端 actionGuideV2 保持一致：{observe:[], do:[], avoid:[]}
    """

    def to_num(v: Any, d: float = 0.0) -> float:
        try:
            if v is None:
                return d
            if isinstance(v, str):
                v = v.replace("%", "").strip()
            n = float(v)
            return n
        except Exception:
            return d

    def tag(text: str, cls: str = "") -> Dict[str, str]:
        return {"text": text, "cls": cls}

    def pick_theme() -> Dict[str, Any]:
        """
        主线识别（复盘版）：
        - 优先基于 strengthRows 的“净强-风险”来选主线（更稳，减少“涨停数虚胖”）
        - examples 优先从当日涨停池里抽样，确保举例与主线一致（避免不精准）
        """
        tp = market_data.get("themePanels") or {}
        rows = (tp.get("strengthRows") or [])[:10]
        best = None
        best_score = -1e9
        for r in rows:
            net = to_num(r.get("net"), 0)
            risk = to_num(r.get("risk"), 0)
            # 经验权重：净强优先，风险惩罚；避免“高净强但风险爆表”的误判
            score = net - risk * 0.6
            if score > best_score:
                best_score = score
                best = r

        # 兜底：无 strengthRows 时回退到涨停Top
        if not best:
            t = ((tp.get("ztTop") or [])[:1] or [None])[0]
            if not t:
                return {"name": "主线", "count": 0, "examples": ""}
            return t

        name = str(best.get("name") or "主线")
        count = int(to_num(best.get("zt"), 0))

        # 从涨停池抽样 examples（依赖渲染器注入 ztgc + zt_code_themes）
        ztgc = market_data.get("ztgc") or []
        code2themes = market_data.get("zt_code_themes") or {}
        picks: list[tuple[float, str]] = []
        for s in ztgc:
            code = str(s.get("dm") or s.get("code") or "")
            mc = str(s.get("mc") or "")
            if not code or not mc:
                continue
            ths = code2themes.get(code) or []
            if name not in ths:
                continue
            lbc = to_num(s.get("lbc"), 1)
            zj = to_num(s.get("zj"), 0)
            zbc = to_num(s.get("zbc"), 0)
            score = lbc * 100 + zj / 1e8 * 10 - zbc * 2
            picks.append((score, mc))
        picks.sort(reverse=True)
        examples = "·".join([mc for _, mc in picks[:3]]) if picks else str(((tp.get("ztTop") or [{}])[0] or {}).get("examples") or "")
        return {"name": name, "count": count, "examples": examples}

    def pick_leader(*, prefer_theme: str) -> Dict[str, Any]:
        """
        龙头识别（复盘版）：
        - 先取最高板组
        - 同板高度下：优先主线题材命中，其次封单更大、开板更少
        """
        rows = market_data.get("ladder") or []
        max_b = 0
        for r in rows:
            max_b = max(max_b, int(to_num(r.get("badge"), 0)))
        top = [r for r in rows if int(to_num(r.get("badge"), 0)) == max_b]
        if not top:
            return {"maxB": max_b, "names": "龙头", "count": 0}

        code2themes = market_data.get("zt_code_themes") or {}

        def rank_key(r: Dict[str, Any]) -> float:
            code = str(r.get("code") or r.get("dm") or "")
            ths = code2themes.get(code) or []
            is_main = 1 if (prefer_theme and prefer_theme in ths) else 0
            zj = to_num(r.get("zj"), 0)
            zbc = to_num(r.get("zbc"), 0)
            # 主线命中优先；封单大更好；开板多惩罚
            return is_main * 1e6 + (zj / 1e8) * 1000 - zbc * 10

        top_sorted = sorted(top, key=rank_key, reverse=True)
        names = [str(r.get("name") or "") for r in top_sorted]
        names = [n for n in names if n]
        return {"maxB": max_b, "names": "、".join(names[:3]) if names else "龙头", "count": len(top_sorted)}

    def pick_theme_strength(name: str) -> Dict[str, Any]:
        rows = ((market_data.get("themePanels") or {}).get("strengthRows") or [])
        for r in rows:
            if str(r.get("name")) == str(name):
                return r
        return {}

    mi = ((market_data.get("features") or {}).get("mood_inputs") or {})
    delta = market_data.get("delta") or {}

    stage = (market_data.get("moodStage") or {}).get("title") or "-"
    stage_type = (market_data.get("moodStage") or {}).get("type") or "warn"
    theme = pick_theme()
    leader = pick_leader(prefer_theme=str(theme.get("name") or ""))
    theme_row = pick_theme_strength(str(theme.get("name") or ""))
    theme_net = to_num(theme_row.get("net"), 0)
    theme_risk = to_num(theme_row.get("risk"), 0)
    overlap = ((market_data.get("themePanels") or {}).get("overlap") or {})
    overlap_score = to_num(overlap.get("score"), 0)

    fb = to_num(mi.get("fb_rate"), to_num((market_data.get("panorama") or {}).get("ratio"), 0))
    jj = to_num(mi.get("jj_rate"), 0)
    zb = to_num(mi.get("zb_rate"), to_num((market_data.get("fear") or {}).get("broken"), 0))
    early = to_num(mi.get("zt_early_ratio"), 0)
    loss = to_num(mi.get("bf_count"), 0) + to_num(mi.get("dt_count"), 0)
    heat = to_num((market_data.get("mood") or {}).get("heat"), 0)
    risk = to_num((market_data.get("mood") or {}).get("risk"), 0)
    zt_cnt = int(to_num((market_data.get("panorama") or {}).get("limitUp"), to_num(mi.get("zt_count"), 0)))
    vol_chg = to_num(((market_data.get("volume") or {}).get("change")), 0)  # %

    # 阈值容忍度：随阶段动态变化（避免写死绝对阈值）
    if stage_type == "good":
        tol = {"fb": 8, "jj": 10, "zb": 10, "loss": 3}
        stage_cls = "ladder-chip-strong red-text"
    elif stage_type == "fire":
        tol = {"fb": 6, "jj": 8, "zb": 8, "loss": 2}
        stage_cls = "ladder-chip-cool blue-text"
    else:
        tol = {"fb": 5, "jj": 8, "zb": 8, "loss": 2}
        stage_cls = "ladder-chip-warn orange-text"

    def dtag(key: str, unit: str = "") -> Dict[str, str] | None:
        v = delta.get(key)
        if v is None:
            return None
        n = to_num(v, None)  # type: ignore[arg-type]
        if n is None:
            return None
        cls = "ladder-chip-strong red-text" if n > 0 else ("ladder-chip-cool blue-text" if n < 0 else "")
        sign = "+" if n > 0 else ""
        # pp 用 1 位小数更像“百分点”
        if unit == "pp":
            text = f"Δ{sign}{n:.1f}{unit}"
        else:
            text = f"Δ{sign}{int(n) if float(n).is_integer() else n}{unit}"
        return tag(text, cls)

    # 盘面基调（给行动指南一个“像复盘”的总起）
    if stage_type == "good":
        regime = "强势偏高潮"
        verdict_type = "good"
    elif stage_type == "fire":
        regime = "弱势偏退潮"
        verdict_type = "fire"
    else:
        regime = "震荡分歧"
        verdict_type = "warn"

    stance = "均衡"
    if heat >= 70 and risk <= 40 and fb >= 70:
        stance = "进攻"
    elif risk >= 60 or loss >= 10 or fb <= 55:
        stance = "防守"

    # 模式选择（4态）：接力 / 套利 / 低位试错 / 休息
    mode = "低位试错"
    if stance == "防守" or stage_type == "fire" or overlap_score >= 70:
        mode = "休息"
    else:
        # 接力模式需要“承接确认 + 风险可控 + 有空间锚 + 主线净强不差”
        if fb >= 60 and jj >= 35 and zb <= 35 and loss <= 10 and leader["maxB"] >= 2 and theme_net >= 10:
            mode = "接力"
        # 套利态：风险不高但承接不足，更多做“回封/容量/趋势”，不做高位硬接
        elif risk <= 55 and zb <= 45 and loss <= 12:
            mode = "套利"
        else:
            mode = "低位试错"

    meta_title = f"🧩 盘面基调：{regime}｜主线：{theme.get('name','主线')}｜模式：{mode}｜建议：{stance}"
    meta_detail = (
        f"涨停{zt_cnt}，封板{fb:.1f}%（早封{early:.0f}%），晋级{jj:.0f}%；"
        f"炸板{zb:.1f}%、亏钱扩散{int(loss)}；量能变化{vol_chg:+.2f}%。"
    )

    # 文案模块化：尽量贴合盘面，不用固定话术
    def line_main_theme() -> str:
        nm = theme.get("name", "主线")
        ex = theme.get("examples") or ""
        if ex:
            return f"主线{nm}（样本：{ex}）"
        return f"主线{nm}"

    def line_leader() -> str:
        return f"空间锚定：{leader['names']}（{leader['maxB'] or '-'}板）"

    def style_hint() -> str:
        if stage_type == "good" and leader["maxB"] >= 6:
            return "高潮高位：更看“分歧回封/换手确认”，少追一致加速。"
        if stage_type == "warn":
            return "分歧震荡：以“主线辨识度+低位换手”为主，避免情绪硬接。"
        return "退潮弱势：以防守与模式内试错为主，等待拐点信号。"

    observe = [
        {
            "dot": "dot-key",
            "title": f"主线与龙头：{theme.get('name','主线')} · {leader['names']}（{leader['maxB'] or '-'}板）",
            "desc": f"{line_main_theme()}；{line_leader()}。{style_hint()}",
            "tags": [
                tag(f"情绪：{stage}", stage_cls),
                tag(f"主线：{theme.get('name','主线')} {theme.get('count',0)}家", "ladder-chip-cool blue-text"),
                tag(f"高度：{leader['maxB'] or '-'}板", "ladder-chip-strong red-text" if leader["maxB"] >= 6 else "ladder-chip-warn orange-text"),
                *(x for x in [dtag("max_lb")] if x),
            ],
        },
        {
            "dot": "dot-watch",
            "title": "承接与一致性：封板/晋级是否掉速",
            "desc": f"承接不掉速才谈接力：封板≥{max(0, fb - tol['fb']):.0f}%（今{fb:.1f}%），晋级≥{max(0, jj - tol['jj']):.0f}%（今{jj:.0f}%）。若早封占比走低，优先做回封确认。",
            "tags": [
                tag(f"封板 {fb:.1f}%", "ladder-chip-warn orange-text"),
                *(x for x in [dtag("fb_rate", "pp")] if x),
                tag(f"晋级 {jj:.0f}%", "ladder-chip-cool blue-text"),
                *(x for x in [dtag("jj_rate", "pp")] if x),
                tag(f"早封 {early:.0f}%", "ladder-chip-cool blue-text"),
                *(x for x in [dtag("zt_early_ratio", "pp")] if x),
            ],
        },
        {
            "dot": "dot-watch",
            "title": "分歧信号：炸板与亏钱扩散是否放大",
            "desc": f"风险先行：炸板≤{(zb + tol['zb']):.1f}%（今{zb:.1f}%）；扩散≤{int(loss + tol['loss'])}（今{int(loss)}）。若两者同步走高，明日以“观察”为主。",
            "tags": [
                tag(f"炸板 {zb:.1f}%", "ladder-chip-warn orange-text"),
                *(x for x in [dtag("zb_rate", "pp")] if x),
                tag(f"扩散 {int(loss)}只", "ladder-chip-strong red-text"),
                *(x for x in [dtag("loss")] if x),
            ],
        },
    ]

    # 双清单：确认门槛 & 撤退条件（把理念变成“可执行规则”）
    confirm = [
        {
            "dot": "dot-safe",
            "title": "确认门槛①：主线仍强（才谈集中火力）",
            "desc": (
                f"主线「{theme.get('name','主线')}」净强度参考今{theme_net:.1f}（风险{theme_risk:.1f}）；"
                "若明日开盘主线仍为涨停Top且出现分歧回封承接，才考虑集中出手。"
            ),
            "tags": [
                tag(f"主线净强 {theme_net:.1f}", "ladder-chip-warn orange-text" if theme_net >= 10 else "ladder-chip-cool blue-text"),
                tag(f"主线风险 {theme_risk:.1f}", "ladder-chip-warn orange-text" if theme_risk >= 4 else "ladder-chip-cool blue-text"),
                tag(f"重叠度 {overlap_score:.0f}", "ladder-chip-strong red-text" if overlap_score >= 60 else "ladder-chip-cool blue-text"),
            ],
        },
        {
            "dot": "dot-safe",
            "title": "确认门槛②：板块联动/共振（至少两只核心同向）",
            "desc": (
                f"不盯一只票：用“同题材两只辨识度”相互印证。"
                f"主线样本可先盯：{theme.get('examples') or '—'}。"
                "若同题材无法共振（强的强、弱的弱），宁可等待确认，不急于出手。"
            ),
            "tags": [
                tag("两股验证", "ladder-chip-cool blue-text"),
                tag("等确认", "ladder-chip-warn orange-text"),
            ],
        },
        {
            "dot": "dot-safe",
            "title": "确认门槛②：承接不掉速（关键点确认）",
            "desc": (
                f"封板≥{max(0, fb - tol['fb']):.0f}%（今{fb:.1f}%），"
                f"晋级≥{max(0, jj - tol['jj']):.0f}%（今{jj:.0f}%）；"
                "若不满足，默认降级到低位试错/观察。"
            ),
            "tags": [
                tag(f"封板 {fb:.1f}%", "ladder-chip-warn orange-text"),
                *(x for x in [dtag("fb_rate", "pp")] if x),
                tag(f"晋级 {jj:.0f}%", "ladder-chip-cool blue-text"),
                *(x for x in [dtag("jj_rate", "pp")] if x),
                tag(f"早封 {early:.0f}%", "ladder-chip-cool blue-text"),
            ],
        },
        {
            "dot": "dot-safe",
            "title": "确认门槛③：风险可控（先看亏钱效应）",
            "desc": (
                f"炸板≤{(zb + tol['zb']):.1f}%（今{zb:.1f}%），"
                f"扩散≤{int(loss + tol['loss'])}（今{int(loss)}）；"
                "若两者同步走高，优先休息，避免频繁交易。"
            ),
            "tags": [
                tag(f"炸板 {zb:.1f}%", "ladder-chip-warn orange-text"),
                tag(f"扩散 {int(loss)}只", "ladder-chip-strong red-text" if loss >= 8 else "ladder-chip-cool blue-text"),
            ],
        },
    ]

    retreat = [
        {
            "dot": "dot-risk",
            "title": "撤退条件①：炸板/扩散放大（先躲开）",
            "desc": f"当炸板率 > {(zb + tol['zb']):.1f}% 或 扩散 > {int(loss + tol['loss'])} 时，立即从接力降级为低位试错/观察。",
            "tags": [
                tag(f"阈值 炸板>{(zb + tol['zb']):.0f}%", "ladder-chip-warn orange-text"),
                tag(f"阈值 扩散>{int(loss + tol['loss'])}", "ladder-chip-strong red-text"),
            ],
        },
        {
            "dot": "dot-risk",
            "title": "撤退条件②：龙头断板/高位大分歧（不硬接）",
            "desc": f"若空间锚（{leader['names']}，{leader['maxB'] or '-'}板）出现断板或大幅放量分歧，停止追高，只做回封确认。",
            "tags": [
                tag(f"高度 {leader['maxB'] or '-'}板", "ladder-chip-strong red-text" if leader["maxB"] >= 6 else "ladder-chip-warn orange-text"),
                tag("只做确认", "ladder-chip-cool blue-text"),
            ],
        },
        {
            "dot": "dot-risk",
            "title": "撤退条件③：主线与杀跌重叠升高（防内卷）",
            "desc": "主线与杀跌题材重叠度升高时，说明内卷与补跌风险增大；此时减少题材发散，回到主线最强辨识度或休息。",
            "tags": [
                tag(f"重叠度 {overlap_score:.0f}", "ladder-chip-strong red-text" if overlap_score >= 60 else "ladder-chip-cool blue-text"),
            ],
        },
        {
            "dot": "dot-risk",
            "title": "撤退条件④：仓位纪律（不摊平/快认错）",
            "desc": "原则：不摊平亏损；买入后2-3天仍无正反馈则退出。单笔/单日亏损设上限（例如 10%），触发就先撤。",
            "tags": [
                tag("不摊平", "ladder-chip-strong red-text"),
                tag("快认错", "ladder-chip-warn orange-text"),
                tag("止损上限", "ladder-chip-cool blue-text"),
            ],
        },
    ]

    do_list = [
        {
            "dot": "dot-safe",
            "title": "计划A（主线核心）：先做确认再加速" if mode == "接力" else ("计划A（套利态）：回封/容量优先" if mode == "套利" else "计划A（低位试错）：换手确认优先"),
            "desc": (
                f"接力模式：承接达标后围绕{line_main_theme()}做核心辨识度，以2板确认/分歧回封为主，避免尾盘一致追涨。"
                if mode == "接力"
                else (
                    f"套利态：围绕{line_main_theme()}做回封/容量/趋势的确定性，不做高位情绪硬接，优先“回封确认→隔日兑现”。"
                    if mode == "套利"
                    else f"低位试错：当承接一般时，围绕{line_main_theme()}只做低位换手确认与首板/1进2，小仓试错换信息。"
                )
            ),
            "tags": [
                tag(f"主线 {theme.get('name','主线')}", "ladder-chip-cool blue-text"),
                tag(f"封板≥{max(0, fb - tol['fb']):.0f}%", ""),
                tag(f"晋级≥{max(0, jj - tol['jj']):.0f}%", ""),
                tag(f"炸板≤{(zb + tol['zb']):.0f}%", ""),
            ],
        },
        {
            "dot": "dot-safe",
            "title": "计划B（低位试错）：分歧上升时切到低位换手",
            "desc": "若分歧上升（炸板/扩散走高），立即把注意力从高位接力切到“低位换手+首板/1进2”，用小仓试错换确定性。",
            "tags": [
                tag(f"扩散≤{int(loss + tol['loss'])}只", ""),
                tag(f"早封 {early:.0f}%", "ladder-chip-cool blue-text"),
            ],
        },
        {
            "dot": "dot-safe",
            "title": "仓位建议：用热度/风险配仓",
            "desc": f"热度{int(heat)}/风险{int(risk)}决定仓位：风险压过热度→防守为主；热度显著占优且承接达标→再进攻加仓。",
            "tags": [
                tag(f"热度 {int(heat)}", "ladder-chip-strong red-text" if heat >= 70 else "ladder-chip-warn orange-text"),
                tag(f"风险 {int(risk)}", "ladder-chip-strong red-text" if risk >= 60 else "ladder-chip-cool blue-text"),
                tag("分批进场", "ladder-chip-cool blue-text"),
                *(x for x in [dtag("heat"), dtag("risk")] if x),
            ],
        },
    ]

    avoid = [
        {
            "dot": "dot-risk",
            "title": "禁止追高：高潮/高位阶段不追一致末端",
            "desc": f"若处于「{stage}」且高度 {leader['maxB'] or '-'} 板偏高，次日更易分化与回撤：不追尾盘一致，不做高位情绪票补涨。",
            "tags": [
                tag(f"阶段 {stage}", stage_cls),
                tag(f"高度 {leader['maxB'] or '-'}板", "ladder-chip-strong red-text" if leader["maxB"] >= 6 else "ladder-chip-warn orange-text"),
            ],
        },
        {
            "dot": "dot-risk",
            "title": "禁止硬接分歧：炸板/扩散显著放大时先保命",
            "desc": f"当炸板率 > {(zb + tol['zb']):.1f}% 或 亏钱扩散 > {int(loss + tol['loss'])} 只，优先保命，不做情绪硬接力。",
            "tags": [
                tag(f"炸板>{(zb + tol['zb']):.0f}%", "ladder-chip-warn orange-text"),
                tag(f"扩散>{int(loss + tol['loss'])}只", "ladder-chip-strong red-text"),
            ],
        },
        {
            "dot": "dot-risk",
            "title": "禁止脱离主线：主线退潮时不做题材发散",
            "desc": f"若主线（{theme.get('name','主线')}）涨停家数明显缩减或板块内出现高位炸板扩散，减少题材发散，回到“主线核心/容量辨识度”。",
            "tags": [
                tag(f"主线 {theme.get('name','主线')}", "ladder-chip-cool blue-text"),
                tag(f"样本 {theme.get('examples') or '—'}", ""),
            ],
        },
    ]

    return {
        "meta": {"title": meta_title, "detail": meta_detail, "type": verdict_type},
        "confirm": confirm,
        "retreat": retreat,
        "observe": observe,
        "do": do_list,
        "avoid": avoid,
    }


def build_summary3(*, market_data: Dict[str, Any]) -> Dict[str, Any]:
    """全站三句话（复盘口径统一）：今天是什么盘 / 主线与龙头 / 明天模式与触发条件"""
    ag = (market_data.get("actionGuideV2") or {})
    meta = (ag.get("meta") or {})

    # 1) 今天是什么盘（取 meta.detail 的数字版 + stage）
    stage = (market_data.get("moodStage") or {}).get("title") or "-"
    line1 = f"今日：{stage}，{meta.get('detail','').strip()}"

    # 2) 主线与龙头
    theme = ((market_data.get("actionGuideV2") or {}).get("meta") or {}).get("title", "")
    # meta.title 内含“主线：xx”，这里再提取一次更直白
    main = (market_data.get("themePanels") or {}).get("ztTop") or []
    main_name = ""
    if "主线：" in str(meta.get("title", "")):
        try:
            main_name = str(meta.get("title")).split("主线：", 1)[1].split("｜", 1)[0].strip()
        except Exception:
            main_name = ""
    if not main_name:
        main_name = (main[0].get("name") if main else "主线")
    leader = "龙头"
    ladder = market_data.get("ladder") or []
    if ladder:
        maxb = max(int(float(r.get("badge", 0) or 0)) for r in ladder)
        tops = [r for r in ladder if int(float(r.get("badge", 0) or 0)) == maxb]
        leader = "、".join([str(r.get("name") or "") for r in tops[:2] if str(r.get("name") or "")]) or leader
        leader = f"{leader}（{maxb}板）"
    line2 = f"主线：{main_name}；空间锚：{leader}。"

    # 3) 明天怎么做（模式 + 关键触发）
    mode = ""
    if "模式：" in str(meta.get("title", "")):
        try:
            mode = str(meta.get("title")).split("模式：", 1)[1].split("｜", 1)[0].strip()
        except Exception:
            mode = ""
    if not mode:
        mode = "低位试错"

    # 从 confirm/retreat 抽一句最关键的阈值（尽量短）
    cf = (ag.get("confirm") or [])
    rt = (ag.get("retreat") or [])
    cf_hint = ""
    rt_hint = ""
    if cf:
        cf_hint = str((cf[1].get("desc") if len(cf) > 1 else cf[0].get("desc")) or "").strip()
        cf_hint = cf_hint.split("；", 1)[0]
    if rt:
        rt_hint = str(rt[0].get("desc") or "").strip().split("，", 1)[0]
    line3 = f"明日：{mode}。确认：{cf_hint or '承接确认'}；撤退：{rt_hint or '风险放大就降级'}。"

    return {"lines": [line1, line2, line3]}

def build_learning_notes(*, market_data: Dict[str, Any], cache_dir: Path) -> Dict[str, Any]:
    """
    学习短线的注意事项 + 1~2 句金句（偏复盘语气）。
    - 不引用外部 PDF 原文，避免版权风险；内容为归纳提炼。
    - 可随盘面阶段动态切换语气（更贴合每日复盘）。
    """
    date = str(market_data.get("date") or "").strip() or "unknown-date"
    stage_type = ((market_data.get("moodStage") or {}).get("type") or "warn").strip()

    # 展示强度 A：每天仅 1 条注意事项 + 1 句金句，并做近 7 日去重
    # 候选池尽量丰富，避免两三天就重复
    tips_general = [
        ("t001", "先活下来：单笔/单日都要有可执行的止损与撤退点，回撤不可失控。"),
        ("t002", "只做主线：分歧市做减法，优先“主线 + 辨识度 + 确认点”。"),
        ("t003", "先确认后加仓：不要用想象加仓，用回封/换手/承接数据加仓。"),
        ("t004", "轻仓试错，重仓在确定性：大赚来自少数几次，平时用小仓位换信息。"),
        ("t005", "复盘要可验证：写清入场理由、撤退条件、次日验证点，形成可复制模式。"),
        ("t006", "只做你统计过的形态：没复盘过、没验证过的，默认不做。"),
        ("t007", "一致与分歧要分开：一致吃溢价，分歧吃性价比，别混用打法。"),
        ("t008", "别拿消息当逻辑：题材只是壳，核心是强度、承接和情绪。"),
        ("t009", "仓位要跟随情绪：热度升、风险降才扩仓；反之先收缩。"),
        ("t010", "交易日只做两件事：等信号、执行纪律；不做“临盘改剧本”。"),
        # 来自你上传内容的归纳（利弗莫尔/关键点体系）
        ("t011", "价位是确认信号的核心：不等关键价位被市场确认，不轻举妄动。"),
        ("t012", "频繁交易是失败者的玩法：当市场缺乏大好机会，应缩手不动。"),
        ("t013", "集中火力做领先股：先确认谁是领头股，再集中，而不是分散。"),
        ("t014", "两股验证：用同题材两只辨识度相互印证，减少“单票误判”。"),
        ("t015", "先有盈利再加仓：没有浮盈，就不要谈格局与耐心。"),
        ("t016", "成交量是危险信号：放量不涨、趋势不延续，要优先防守。"),
        ("t017", "不靠消息下单：只看事实（强度、承接、联动、风险）。"),
    ]
    tips_good = [
        ("tg01", "高潮日更要克制：不追尾盘一致，优先分歧回封/换手确认。"),
        ("tg02", "高度打开≠随便追：盯龙头与主线扩散，别追补涨跟风。"),
        ("tg03", "高位一旦放量分歧，先减仓再谈接力。"),
        ("tg04", "重要趋势的利润多发生在最后阶段：但前提是你一直在场内、且仓位可控。"),
        ("tg05", "强市也要分批：先试错确认，再加仓扩大利润段。"),
    ]
    tips_warn = [
        ("tw01", "分歧市先做减法：宁可少做，也不乱做。"),
        ("tw02", "主线不强就不硬接：用低位换手试错换信息。"),
        ("tw03", "炸板与扩散同步走高时，宁可空仓观望。"),
        ("tw04", "最小阻力线不一致就不做：先让市场本身证实你的判断。"),
        ("tw05", "板块不联动就不强：同题材不共振，优先等待。"),
    ]
    tips_fire = [
        ("tf01", "退潮阶段先保命：不做高位接力，不做情绪硬接。"),
        ("tf02", "弱势只做模式内：小仓试错，错了就退。"),
        ("tf03", "亏钱效应不收敛前，优先休息而不是寻找机会。"),
        ("tf04", "看到危险信号就躲开：过几天再回来，省麻烦也省钱。"),
        ("tf05", "退潮期少做：休息也是交易的一部分。"),
    ]

    quotes_good = [
        ("qg01", "高潮不追一致，分歧回封才是性价比。"),
        ("qg02", "赚快钱的前提是：仓位可控、退出清晰。"),
        ("qg03", "空间来自龙头，但利润来自纪律。"),
        ("qg04", "强市也会杀人：别在最高点证明自己勇敢。"),
        ("qg05", "能赚到钱靠的不是想法，真正赚到钱的是坐在那里等待机会的出现。"),
        ("qg06", "趋势发动前的等待，胜过趋势发动后的追赶。"),
    ]
    quotes_warn = [
        ("qw01", "分歧市做减法：只做最强主线的最强辨识度。"),
        ("qw02", "看懂亏钱效应，比看懂赚钱效应更重要。"),
        ("qw03", "没有确认点的交易，都是情绪消费。"),
        ("qw04", "做对很难，少犯错更重要。"),
        ("qw05", "市场只有一个方向：不是多头也不是空头，而是做对的方向。"),
        ("qw06", "关键价位之上5%~10%才入场，往往已经错过最佳时机。"),
        ("qw07", "没有共振的强，只是单点的热。"),
    ]
    quotes_fire = [
        ("qf01", "退潮先保命：不亏钱就是赢。"),
        ("qf02", "只在模式内出手，别用情绪下单。"),
        ("qf03", "弱势里的机会，往往是强势里的陷阱。"),
        ("qf04", "等风来，不是赌风来。"),
        ("qf05", "当我看见危险信号时，我不跟它争执，我躲开。"),
        ("qf06", "绝不要平反亏损——亏损只会让判断失真。"),
        ("qf07", "先躲开危险信号，机会永远会再来。"),
    ]

    if stage_type == "good":
        tip_pool = tips_good + tips_general
        quote_pool = quotes_good
    elif stage_type == "fire":
        tip_pool = tips_fire + tips_general
        quote_pool = quotes_fire
    else:
        tip_pool = tips_warn + tips_general
        quote_pool = quotes_warn

    history_path = cache_dir / "learning_notes_history.json"
    history = {"tip_ids": [], "quote_ids": [], "last_date": ""}
    try:
        if history_path.exists():
            history = json.loads(history_path.read_text(encoding="utf-8")) or history
    except Exception:
        history = {"tip_ids": [], "quote_ids": [], "last_date": ""}

    tip_used = set((history.get("tip_ids") or [])[:7])
    quote_used = set((history.get("quote_ids") or [])[:7])

    def pick_one(pool: list[tuple[str, str]], used: set[str], seed_key: str) -> tuple[str, str]:
        if not pool:
            return ("", "")
        seed = int(hashlib.md5(seed_key.encode("utf-8")).hexdigest(), 16)
        start = seed % len(pool)
        for i in range(len(pool)):
            _id, _txt = pool[(start + i) % len(pool)]
            if _id not in used:
                return (_id, _txt)
        return pool[start]

    tip_id, tip_txt = pick_one(tip_pool, tip_used, f"{date}:{stage_type}:tip")
    quote_id, quote_txt = pick_one(quote_pool, quote_used, f"{date}:{stage_type}:quote")

    # 更新历史（同一天重复渲染不重复追加）
    try:
        if history.get("last_date") != date:
            history["tip_ids"] = [tip_id] + list(history.get("tip_ids") or [])
            history["quote_ids"] = [quote_id] + list(history.get("quote_ids") or [])
            history["tip_ids"] = (history["tip_ids"] or [])[:7]
            history["quote_ids"] = (history["quote_ids"] or [])[:7]
            history["last_date"] = date
            history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    return {"tips": [tip_txt] if tip_txt else [], "quotes": [quote_txt] if quote_txt else []}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True, help="HTML 模板路径")
    ap.add_argument("--market-data-json", required=True, help="marketData 的 JSON 文件路径")
    ap.add_argument("--out", required=True, help="输出 HTML 路径")
    ap.add_argument("--date", required=True, help="报告日期 YYYY-MM-DD")
    ap.add_argument("--note", default="", help="日期备注（非交易日回退提示等）")
    args = ap.parse_args()

    template_path = Path(args.template)
    market_json_path = Path(args.market_data_json)
    output_path = Path(args.out)

    market_data = json.loads(market_json_path.read_text(encoding="utf-8"))

    # 离线增强：把 pools_cache.json 中的当日涨停池注入到 market_data，供 HTML 做“涨停个股分析”
    # 注意：此处不做任何网络请求，只读取本地缓存文件
    try:
        pools_cache_path = market_json_path.parent / "pools_cache.json"
        if pools_cache_path.exists():
            pools_cache = json.loads(pools_cache_path.read_text(encoding="utf-8"))
            ztgc = (((pools_cache.get("pools") or {}).get("ztgc") or {}).get(args.date)) or []
            # 为避免与其他字段冲突，使用 ztgc 作为当日涨停池明细
            market_data["ztgc"] = ztgc
            # 同步注入题材映射（theme_cache.json）：为涨停个股分析提供“更细粒度题材”
            theme_cache_path = market_json_path.parent / "theme_cache.json"
            if theme_cache_path.exists():
                theme_cache = json.loads(theme_cache_path.read_text(encoding="utf-8"))
                code2themes = theme_cache.get("codes") or {}
                # 只注入当日涨停池涉及的代码，避免把整个题材库塞进 HTML
                zt_code_themes = {}
                for s in ztgc:
                    code = str(s.get("dm") or s.get("code") or "")
                    if code and code in code2themes:
                        zt_code_themes[code] = code2themes.get(code) or []
                market_data["zt_code_themes"] = zt_code_themes
    except Exception:
        # 缓存缺失或格式异常时忽略，不影响主页面渲染
        pass

    # 离线增强：用 Python 算法生成“明日计划”（避免前端出现“写死文案”的错觉）
    try:
        market_data.setdefault("actionGuideV2", build_action_guide_v2(market_data))
    except Exception:
        market_data.setdefault("actionGuideV2", {"observe": [], "do": [], "avoid": []})

    # 离线增强：全站三句话（口径统一）
    try:
        market_data.setdefault("summary3", build_summary3(market_data=market_data))
    except Exception:
        market_data.setdefault("summary3", {"lines": []})

    # 离线增强：学习短线提醒 + 金句（随情绪阶段动态切换）
    try:
        market_data.setdefault("learningNotes", build_learning_notes(market_data=market_data, cache_dir=market_json_path.parent))
    except Exception:
        market_data.setdefault("learningNotes", {"tips": [], "quotes": []})

    render_html_template(
        template_path=template_path,
        output_path=output_path,
        market_data=market_data,
        report_date=args.date,
        date_note=args.note,
    )
