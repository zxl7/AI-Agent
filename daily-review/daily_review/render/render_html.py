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

    render_html_template(
        template_path=template_path,
        output_path=output_path,
        market_data=market_data,
        report_date=args.date,
        date_note=args.note,
    )

