#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# 用途：一键生成复盘日记 HTML
# 用法：
#   ./run_report.sh                # 默认生成今天（脚本内部会自动回退到最近交易日）
#   ./run_report.sh 2026-04-17     # 指定日期

set -euo pipefail

DATE_ARG="${1:-}"

if [[ -z "${DATE_ARG}" ]]; then
  python3 gen_report_v4.py
else
  python3 gen_report_v4.py "${DATE_ARG}"
fi

