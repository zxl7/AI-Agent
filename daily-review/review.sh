#!/bin/bash

# ==============================================================================
# Alpha Agent 短线一键复盘脚本
# 功能：自动采集收盘数据，生成文本报告，并同步更新 HTML 可视化报告
# 用法：./review.sh              # 默认复盘今天
#      ./review.sh 2026-04-16   # 指定日期复盘
# ==============================================================================

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 定义颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 确定复盘日期
TARGET_DATE=$1
if [ -z "$TARGET_DATE" ]; then
    TARGET_DATE=$(date +%Y-%m-%d)
    echo -e "${BLUE}>> 未指定日期，默认复盘今天: ${TARGET_DATE}${NC}"
else
    echo -e "${BLUE}>> 正在复盘指定日期: ${TARGET_DATE}${NC}"
fi

echo -e "${YELLOW}==================================================${NC}"
echo -e "${GREEN}🚀 启动 Alpha Agent 复盘自动化流程...${NC}"
echo -e "${YELLOW}==================================================${NC}"

# 2. 执行数据采集和报告生成
# 由于 closing_report.py 已经集成了 update_report_html.py，只需调用这一个脚本即可
python3 "${SCRIPT_DIR}/closing_report.py" "$TARGET_DATE"

# 3. 检查执行结果
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ 复盘流程执行成功！${NC}"
    echo -e "${BLUE}--------------------------------------------------${NC}"
    echo -e "📄 文本报告: ${SCRIPT_DIR}/text/每日复盘${TARGET_DATE}.txt"
    echo -e "🎨 网页报告: ${SCRIPT_DIR}/短线复盘利器.html"
    echo -e "${BLUE}--------------------------------------------------${NC}"
else
    echo -e "\n❌ 复盘流程执行失败，请检查上方错误日志。"
    exit 1
fi
