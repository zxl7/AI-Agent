#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
情绪模块（热度 vs 风险 + 阶段 + 卡片）

设计目标：
- FULL：gen_report_v4 负责准备 features.mood_inputs（可复用的中间输入）
- PARTIAL：只改这个文件/阈值，即可重算 mood/moodStage/moodCards 并重新渲染
"""

from __future__ import annotations

from typing import Any, Dict, List

from .scoring import HeatRiskScore, calc_heat_risk


def class_for_good_rate(rate: float, hi: float = 60, mid: float = 40) -> str:
    if rate >= hi:
        return "red-text"
    if rate >= mid:
        return "orange-text"
    return "green-text"


def class_for_bad_rate(rate: float, hi: float = 30, mid: float = 15) -> str:
    if rate >= hi:
        return "red-text"
    if rate >= mid:
        return "orange-text"
    return "green-text"


def calc_stage(*, heat_score: float, risk_score: float, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    复刻当前 gen_report_v4 的阶段判定逻辑（便于保持输出一致），后续你可以只改这里的规则。
    """
    fb_rate = float(inputs.get("fb_rate", 0) or 0)
    zb_rate = float(inputs.get("zb_rate", 0) or 0)
    dt_count = int(inputs.get("dt_count", 0) or 0)
    rate_2to3 = float(inputs.get("rate_2to3", 0) or 0)
    rate_3to4 = float(inputs.get("rate_3to4", 0) or 0)
    height_gap = int(inputs.get("height_gap", 0) or 0)
    broken_lb_rate = float(inputs.get("broken_lb_rate", 0) or 0)
    zb_high_ratio = float(inputs.get("zb_high_ratio", 0) or 0)
    zt_early_ratio = float(inputs.get("zt_early_ratio", 0) or 0)

    # 风险/退潮信号
    risk_hits = 0
    risk_hits += 1 if dt_count >= 10 else 0
    risk_hits += 1 if broken_lb_rate >= 35 else 0
    risk_hits += 1 if zb_high_ratio >= 20 else 0
    risk_hits += 1 if zb_rate >= 28 else 0
    risk_hits += 1 if height_gap >= 4 else 0
    risk_hits += 1 if risk_score >= 60 else 0

    # 强势/一致信号
    strong_hits = 0
    strong_hits += 1 if fb_rate >= 78 else 0
    strong_hits += 1 if rate_2to3 >= 55 else 0
    strong_hits += 1 if rate_3to4 >= 35 else 0
    strong_hits += 1 if zt_early_ratio >= 55 else 0
    strong_hits += 1 if heat_score >= 75 else 0

    if heat_score <= 35 or (fb_rate < 55 and dt_count >= 15) or risk_score >= 80:
        return {"title": "冰点", "type": "fire", "detail": "跌停与断板压力大，短线生态偏弱，等待情绪修复信号。"}
    if risk_hits >= 3 and strong_hits <= 1:
        return {"title": "退潮", "type": "fire", "detail": "高位/连板承接走弱，风险信号集中，优先防守，少做接力。"}
    if strong_hits >= 4 and risk_hits <= 1:
        if heat_score >= 85 and (risk_score >= 45 or height_gap >= 3 or zb_rate >= 22):
            return {"title": "高潮", "type": "good", "detail": "一致性强但易分化，注意高潮次日回撤与高位炸板风险。"}
        return {"title": "强修复", "type": "good", "detail": "封板与晋级偏强，短线生态健康，低位与核心接力都有机会。"}
    if risk_hits >= 2 and strong_hits >= 2:
        return {"title": "分歧", "type": "warn", "detail": "强弱并存，轮动加快，控制仓位，优先做确定性更高的方向。"}
    return {"title": "弱修复", "type": "warn", "detail": "有修复但承接一般，适合轻仓试错，重点观察2进3/3进4能否走强。"}


def build_cards(inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    复刻 gen_report_v4 当前的 moodCards 输出结构（值/label/note/valueClass）。
    """
    zt_count = int(inputs.get("zt_count", 0) or 0)
    zt_early_ratio = float(inputs.get("zt_early_ratio", 0) or 0)
    zt_early_count = int(inputs.get("zt_early_count", 0) or 0)

    avg_seal_fund_yi = float(inputs.get("avg_seal_fund_yi", 0) or 0)
    top_seal_names = str(inputs.get("top_seal_names", "") or "")

    hs_median = float(inputs.get("hs_median", 0) or 0)
    hs_ge15_ratio = float(inputs.get("hs_ge15_ratio", 0) or 0)

    rate_2to3 = float(inputs.get("rate_2to3", 0) or 0)
    yest_2b = int(inputs.get("yest_2b_count", 0) or 0)
    succ_2to3 = int(inputs.get("succ_2to3", 0) or 0)

    rate_3to4 = float(inputs.get("rate_3to4", 0) or 0)
    yest_3b = int(inputs.get("yest_3b_count", 0) or 0)
    succ_3to4 = int(inputs.get("succ_3to4", 0) or 0)

    height_gap = int(inputs.get("height_gap", 0) or 0)
    max_lb = int(inputs.get("max_lb", 0) or 0)
    second_lb = int(inputs.get("second_lb", 0) or 0)

    zb_high_ratio = float(inputs.get("zb_high_ratio", 0) or 0)
    zb_high_count = int(inputs.get("zb_high_count", 0) or 0)
    zb_count = int(inputs.get("zb_count", 0) or 0)
    zb_high_names = str(inputs.get("zb_high_names", "") or "")

    avg_zt_zbc = float(inputs.get("avg_zt_zbc", 0) or 0)
    zt_zbc_ge3_ratio = float(inputs.get("zt_zbc_ge3_ratio", 0) or 0)

    smallcap_ratio = float(inputs.get("smallcap_ratio", 0) or 0)
    smallcap_cnt = int(inputs.get("smallcap_cnt", 0) or 0)

    broken_lb_rate = float(inputs.get("broken_lb_rate", 0) or 0)
    yest_lb_count = int(inputs.get("yest_lb_count", 0) or 0)
    duanban_count = int(inputs.get("duanban_count", 0) or 0)

    return [
        {
            "value": f"{zt_early_ratio:.0f}%",
            "label": "早盘封板占比",
            "note": f"10点前首封 {zt_early_count} / 涨停 {zt_count}",
            "valueClass": class_for_good_rate(zt_early_ratio, hi=55, mid=35),
        },
        {
            "value": f"{avg_seal_fund_yi:.1f}亿",
            "label": "平均封板资金",
            "note": f"TOP3：{top_seal_names}",
            "valueClass": ("red-text" if avg_seal_fund_yi >= 2.0 else ("orange-text" if avg_seal_fund_yi >= 1.0 else "green-text")),
        },
        {
            "value": f"{hs_median:.1f}%",
            "label": "涨停换手(中位)",
            "note": f"高换手(≥15%) {hs_ge15_ratio:.0f}%",
            "valueClass": ("red-text" if hs_median >= 10 else ("orange-text" if hs_median >= 6 else "green-text")),
        },
        {
            "value": f"{rate_2to3:.0f}%",
            "label": "2进3成功率",
            "note": f"昨日2板 {yest_2b} → 今3板+ {succ_2to3}",
            "valueClass": class_for_good_rate(rate_2to3, hi=55, mid=35),
        },
        {
            "value": f"{rate_3to4:.0f}%",
            "label": "3进4成功率",
            "note": f"昨日3板 {yest_3b} → 今4板+ {succ_3to4}",
            "valueClass": class_for_good_rate(rate_3to4, hi=45, mid=25),
        },
        {
            "value": f"{height_gap}",
            "label": "高度差",
            "note": f"最高{max_lb}板 / 次高{second_lb}板",
            "valueClass": ("orange-text" if height_gap >= 3 else ("blue-text" if height_gap == 2 else "green-text")),
        },
        {
            "value": f"{zb_high_ratio:.1f}%",
            "label": "高位炸板占比(4板+)",
            "note": f"高位炸板 {zb_high_count} / 炸板 {zb_count}（{zb_high_names if zb_high_names else '无'}）",
            "valueClass": class_for_bad_rate(zb_high_ratio, hi=20, mid=8),
        },
        {
            "value": f"{avg_zt_zbc:.1f}",
            "label": "涨停炸板次数(均)",
            "note": f"高炸板(≥3次) {zt_zbc_ge3_ratio:.0f}%",
            "valueClass": class_for_bad_rate(zt_zbc_ge3_ratio, hi=18, mid=8),
        },
        {
            "value": f"{smallcap_ratio:.0f}%",
            "label": "小票活跃度(<50亿)",
            "note": f"小票 {smallcap_cnt} / 涨停 {zt_count}",
            "valueClass": class_for_good_rate(smallcap_ratio, hi=55, mid=35),
        },
        {
            "value": f"{broken_lb_rate:.0f}%",
            "label": "连板断板率",
            "note": f"昨日连板 {yest_lb_count} → 断板 {duanban_count}",
            "valueClass": class_for_bad_rate(broken_lb_rate, hi=35, mid=20),
        },
    ]


def rebuild_mood(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一输出：
    - mood
    - moodStage
    - moodCards
    """
    score: HeatRiskScore = calc_heat_risk(
        fb_rate=float(inputs.get("fb_rate", 0) or 0),
        jj_rate=float(inputs.get("jj_rate", 0) or 0),
        zt_count=int(inputs.get("zt_count", 0) or 0),
        zt_early_ratio=float(inputs.get("zt_early_ratio", 0) or 0),
        zb_rate=float(inputs.get("zb_rate", 0) or 0),
        dt_count=int(inputs.get("dt_count", 0) or 0),
        bf_count=int(inputs.get("bf_count", 0) or 0),
        zb_high_ratio=float(inputs.get("zb_high_ratio", 0) or 0),
        broken_lb_rate=float(inputs.get("broken_lb_rate", 0) or 0),
    )
    stage = calc_stage(heat_score=score.heat, risk_score=score.risk, inputs=inputs)
    cards = build_cards(inputs)
    return {
        "mood": {"heat": score.heat, "risk": score.risk, "score": score.sentiment},
        "moodStage": stage,
        "moodCards": cards,
    }

