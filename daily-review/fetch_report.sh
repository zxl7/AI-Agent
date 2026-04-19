#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# 在线取数 + 生成最新报告（会请求接口，有成本）
#
# 用法：
#   ./fetch_report.sh                # 默认取“最近交易日”，并生成 v1 HTML
#   ./fetch_report.sh 2026-04-17     # 指定日期（YYYY-MM-DD）
#
# 输出：
#   1) cache/market_data-YYYYMMDD.json（更新缓存）
#   2) html/复盘日记-YYYYMMDD-tab-v1.html（用最新模板离线渲染）
#
set -euo pipefail

DATE_ARG="${1:-}"

chmod +x ./run_report.sh ./review.sh 2>/dev/null || true

pick_latest_cache_date() {
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
  echo "${date8}"
}

cleanup_timestamp_html() {
  # 只保留 tab-v1，删除 gen_report_v4 生成的带时分秒版本（复盘日记-YYYYMMDD-HHMMSS.html）
  local yyyymmdd="$1"
  shopt -s nullglob
  local files=( "html/复盘日记-${yyyymmdd}-"[0-9][0-9][0-9][0-9][0-9][0-9].html )
  if ((${#files[@]})); then
    rm -f "${files[@]}"
  fi
  shopt -u nullglob
}

if [[ -z "${DATE_ARG}" ]]; then
  # gen_report_v4.py 会自动回退到最近交易日
  ./run_report.sh
  # 用缓存里最新的 market_data-*.json 再离线渲染一份 v1（不再取数）
  ./review.sh
  if yyyymmdd="$(pick_latest_cache_date)"; then
    cleanup_timestamp_html "${yyyymmdd}"
  fi
else
  ./run_report.sh "${DATE_ARG}"
  ./review.sh "${DATE_ARG}"
  yyyymmdd="$(echo "${DATE_ARG}" | tr -d '-' )"
  cleanup_timestamp_html "${yyyymmdd}"
fi
