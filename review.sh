#!/bin/bash

# ==============================================================================
# Alpha Agent 短线一键复盘脚本
# 功能：自动采集收盘数据，生成文本报告，并同步更新 HTML 可视化报告
# 用法：./review.sh              # 默认复盘今天
#      ./review.sh 2026-04-16   # 指定日期复盘
# ==============================================================================

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
# 核心逻辑所在的子目录
WORK_DIR="${SCRIPT_DIR}/daily-review"
GEN_SCRIPT="${WORK_DIR}/gen_report_v4.py"

# 定义颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. 确定复盘日期
TARGET_DATE=$1
if [ -z "$TARGET_DATE" ]; then
    # 获取当前日期 YYYY-MM-DD
    TARGET_DATE=$(date +%Y-%m-%d)
    echo -e "${BLUE}>> 未指定日期，默认复盘今天: ${TARGET_DATE}${NC}"
else
    # 简单的日期格式校验 (YYYY-MM-DD)
    if [[ ! $TARGET_DATE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo -e "${RED}❌ 错误: 日期格式必须为 YYYY-MM-DD (例如: 2026-04-17)${NC}"
        exit 1
    fi
    echo -e "${BLUE}>> 正在复盘指定日期: ${TARGET_DATE}${NC}"
fi

echo -e "${YELLOW}==================================================${NC}"
echo -e "${GREEN}🚀 启动 Alpha Agent 复盘自动化流程 (v4)${NC}"
echo -e "${YELLOW}==================================================${NC}"

# 2. 预检环境
if [ ! -f "$GEN_SCRIPT" ]; then
    echo -e "${RED}❌ 错误: 找不到核心生成脚本 ${GEN_SCRIPT}${NC}"
    exit 1
fi

# 3. 执行数据采集和报告生成
# 进入工作目录以确保生成的 html/ 文件夹位置正确
cd "$WORK_DIR" || exit 1
python3 "$GEN_SCRIPT" "$TARGET_DATE"

# 4. 检查执行结果
if [ $? -eq 0 ]; then
    # 非交易日可能会自动回退到最近交易日，这里取最新生成的报告文件
    HTML_PATH=$(ls -t "${WORK_DIR}"/html/复盘日记-*.html 2>/dev/null | head -n 1)
    
    echo -e "\n${GREEN}✅ 复盘流程执行成功！${NC}"
    echo -e "${BLUE}--------------------------------------------------${NC}"
    if [ -n "$HTML_PATH" ] && [ -f "$HTML_PATH" ]; then
        echo -e "🎨 网页报告: ${HTML_PATH}"
    fi
    echo -e "${BLUE}--------------------------------------------------${NC}"
    echo -e "${YELLOW}💡 提示: 报告已保存在 daily-review/html/ 目录下${NC}"
else
    echo -e "\n${RED}❌ 复盘流程执行失败，请检查上方错误日志。${NC}"
    exit 1
fi
