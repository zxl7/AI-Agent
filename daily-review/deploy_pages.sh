#!/usr/bin/env bash
set -euo pipefail

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
  python3 - <<'PY' "$1"
import os,sys
print(os.path.abspath(sys.argv[1]))
PY
}

main() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "❌ 请在 Git 仓库内执行此脚本。"
    exit 1
  fi

  # 强制回到仓库根目录（关键修复点）
  local repo_root
  repo_root="$(git rev-parse --show-toplevel)"
  cd "$repo_root"

  local current_branch
  current_branch="$(git branch --show-current)"
  if [ -z "$current_branch" ]; then
    echo "❌ 当前不在任何分支（detached HEAD）。"
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

  # 切分支前复制到临时文件，避免源文件随分支切换消失
  local report_abs tmp
  report_abs="$(abs_path "$report_html")"
  tmp="$(mktemp -t deploy_pages.XXXXXX.html)"
  cp -f "$report_abs" "$tmp"

  echo "==> [2/3] 切到 $PAGES_BRANCH 并覆盖 $PAGES_FILE"
  git switch "$PAGES_BRANCH"
  cd "$repo_root"

  # 确保目标目录存在（支持 PAGES_FILE=some/dir/index.html）
  mkdir -p "$(dirname "$PAGES_FILE")" 2>/dev/null || true

  # 用 install 更稳（没有文件也能创建）
  install -m 644 "$tmp" "$PAGES_FILE"
  rm -f "$tmp"

  git add "$PAGES_FILE"
  git commit -m "deploy: $(date '+%F %T')" || echo "（无变化，无需提交）"
  git push

  echo "==> [3/3] 切回 $current_branch"
  git switch "$current_branch"
  cd "$repo_root"

  echo "✅ 发版完成：已覆盖 $PAGES_BRANCH/$PAGES_FILE"
}

main "$@"