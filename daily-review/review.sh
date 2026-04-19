#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# 离线渲染脚本（不取数、不请求接口）
# 用途：用现有缓存 cache/market_data-YYYYMMDD.json + 模板 templates/report_template.html 生成 v1 HTML
#
# 用法：
#   ./review.sh                # 默认用最近交易日（优先取 cache 里最新的 market_data-*.json）
#   ./review.sh 2026-04-17     # 指定日期（YYYY-MM-DD）
#
# 输出：
#   html/复盘日记-YYYYMMDD-tab-v1.html
#
set -euo pipefail

DATE_ARG="${1:-}"

pick_latest_cache_date() {
  # 从 cache/market_data-*.json 中找最新日期（按文件修改时间）
  local latest_file base date8
  latest_file="$(ls -1t cache/market_data-*.json 2>/dev/null | head -n 1 || true)"
  if [[ -z "${latest_file}" ]]; then
    return 1
  fi
  base="$(basename "${latest_file}")"               # market_data-YYYYMMDD.json
  date8="${base#market_data-}"                      # YYYYMMDD.json
  date8="${date8%.json}"                            # YYYYMMDD
  if [[ ! "${date8}" =~ ^[0-9]{8}$ ]]; then
    return 1
  fi
  echo "${date8:0:4}-${date8:4:2}-${date8:6:2}"
}

if [[ -z "${DATE_ARG}" ]]; then
  if ! DATE_ARG="$(pick_latest_cache_date)"; then
    echo "未找到 cache/market_data-*.json，请先运行：./run_report.sh （会取数）" >&2
    exit 2
  fi
fi

YYYYMMDD="$(echo "${DATE_ARG}" | tr -d '-' )"
MARKET_JSON="cache/market_data-${YYYYMMDD}.json"
TEMPLATE="templates/report_template.html"
OUT_HTML="html/复盘日记-${YYYYMMDD}-tab-v1.html"

if [[ ! -f "${MARKET_JSON}" ]]; then
  echo "未找到 ${MARKET_JSON}，请先运行：./run_report.sh ${DATE_ARG} （会取数）" >&2
  exit 2
fi

PYTHONPATH=. python3 daily_review/render/render_html.py \
  --template "${TEMPLATE}" \
  --market-data-json "${MARKET_JSON}" \
  --out "${OUT_HTML}" \
  --date "${DATE_ARG}"

echo "✅ 离线渲染完成: ${OUT_HTML}"
