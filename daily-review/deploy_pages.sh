#!/usr/bin/env bash
set -euo pipefail

# 用途：
# 1) 选择“已生成”的最新复盘 HTML（默认从 ./html/ 找最新）
# 2) 切到 gh-pages 分支
# 3) 直接覆盖 index.html（你要求“直接覆盖 index”）
# 4) commit + push
#
# 可选环境变量：
#   REPORT_HTML     指定要发布的 HTML 文件路径（跳过自动查找）
#   PAGES_BRANCH    Pages 分支（默认 gh-pages）
#   PAGES_FILE      覆盖的文件名（默认 index.html）
#   ALLOW_DIRTY     允许工作区有未提交修改（默认 0；建议保持干净）
#
# 关键修复点：
# - 切换到 gh-pages 后，源文件（在 master 的 ./html/）会不存在
# - 所以：切分支前先把报告复制到临时文件，再切分支覆盖

PAGES_BRANCH="${PAGES_BRANCH:-gh-pages}"
PAGES_FILE="${PAGES_FILE:-index.html}"
ALLOW_DIRTY="${ALLOW_DIRTY:-0}"

require_clean_git() {
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "❌ 当前工作区有未提交修改，请先提交/暂存/清理后再发版。"
    git status --porcelain
    exit 1
  fi
}

latest_report_auto() {
  local f
  f="$(ls -t ./html/*tab-v1.html 2>/dev/null | head -n 1 || true)"
  if [ -z "$f" ]; then
    f="$(ls -t ./html/*.html 2>/dev/null | head -n 1 || true)"
  fi
  if [ -z "$f" ]; then
    echo "❌ 未找到可发布的报告文件：./html/*.html"
    echo "   你可以手动指定：REPORT_HTML=路径 ./deploy_pages.sh"
    exit 1
  fi
  echo "$f"
}

abs_path() {
  # mac/linux 通用的绝对路径
  python3 - <<'PY' "$1"
import os,sys
print(os.path.abspath(sys.argv[1]))
PY
}

main() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "❌ 请在 Git 仓库根目录执行此脚本。"
    exit 1
  fi

  local current_branch
  current_branch="$(git branch --show-current)"
  if [ -z "$current_branch" ]; then
    echo "❌ 当前不在任何分支（detached HEAD），请先切回 master/main。"
    exit 1
  fi

  echo "==> [1/3] 检查工作区"
  if [ "$ALLOW_DIRTY" != "1" ]; then
    require_clean_git
  else
    echo "⚠️  ALLOW_DIRTY=1：将尝试在有未提交修改的情况下切换分支（可能失败）"
  fi

  local report_html
  report_html="${REPORT_HTML:-}"
  if [ -z "$report_html" ]; then
    report_html="$(latest_report_auto)"
  fi
  if [ ! -f "$report_html" ]; then
    echo "❌ REPORT_HTML 不存在：$report_html"
    exit 1
  fi
  echo "   将发布：$report_html"

  # 切分支前复制到临时文件，避免 gh-pages 分支下找不到源文件
  local report_abs tmp
  report_abs="$(abs_path "$report_html")"
  tmp="$(mktemp -t deploy_pages.XXXXXX.html)"
  cp -f "$report_abs" "$tmp"

  echo "==> [2/3] 切到 $PAGES_BRANCH 并覆盖 $PAGES_FILE"
  git switch "$PAGES_BRANCH"

  mkdir -p "$(dirname "$PAGES_FILE")" 2>/dev/null || true
  cp -f "$tmp" "./$PAGES_FILE"
  rm -f "$tmp"

  git add "./$PAGES_FILE"
  git commit -m "deploy: $(date '+%F %T')" || echo "（无变化，无需提交）"
  git push

  echo "==> [3/3] 切回 $current_branch"
  git switch "$current_branch"

  echo "✅ 发版完成：已覆盖 $PAGES_BRANCH/$PAGES_FILE"
}

main "$@"