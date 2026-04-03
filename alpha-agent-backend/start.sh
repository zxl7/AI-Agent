#!/bin/bash

# ==============================================================================
# Alpha Agent 后台一键启动脚本
# 功能：自动检查端口，启动 ChromaDB 向量数据库，并启动 NestJS 后台服务
# ==============================================================================

# 定义颜色输出
GREEN='\039[0;32m'
YELLOW='\039[1;33m'
RED='\039[0;31m'
NC='\039[0m' # No Color

# 添加常见的 Docker 路径到 PATH，防止终端没加载环境变量
export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin:~/.docker/bin:/usr/local/bin:/opt/homebrew/bin"

echo -e "${GREEN}=== 启动 Alpha Agent 后台服务 ===${NC}"

# 1. 检查 ChromaDB 端口 (8000) 是否被占用
echo -e "${YELLOW}>> 检查 ChromaDB 服务状态...${NC}"
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✅ ChromaDB (8000端口) 已在运行中，跳过启动。${NC}"
else
    echo -e "${YELLOW}>> 正在通过 Docker 启动 ChromaDB...${NC}"
    
    # 检查是否安装了 docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ 未检测到 Docker，请先安装 Docker Desktop。${NC}"
        exit 1
    fi

    # 使用 Docker Compose 启动后台服务
    docker compose up -d
    
    # 等待几秒钟让 Chroma 启动
    sleep 5
    
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✅ ChromaDB 启动成功！(Docker Container)${NC}"
    else
        echo -e "${RED}❌ ChromaDB 启动失败，请检查 Docker 日志 (docker compose logs)。${NC}"
        echo -e "${YELLOW}   提示: 确保 Docker 服务正在运行${NC}"
        exit 1
    fi
fi

# 2. 检查 NestJS 端口 (3000) 是否被占用
echo -e "\n${YELLOW}>> 检查 NestJS 后台服务状态...${NC}"
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}>> 发现 3000 端口已被占用，正在自动清理旧的 NestJS 进程...${NC}"
    lsof -Pi :3000 -sTCP:LISTEN -t | xargs kill -9
    sleep 2
    echo -e "${GREEN}✅ 端口清理完成！${NC}"
fi

# 3. 启动 NestJS 服务
echo -e "${YELLOW}>> 正在启动 NestJS 后台服务 (npm run start:dev)...${NC}"
echo -e "${GREEN}✅ 所有前置服务已就绪！${NC}"
echo -e "${YELLOW}--------------------------------------------------${NC}"
echo -e "${YELLOW}   提示: 按 Ctrl+C 可以停止 NestJS 服务${NC}"
echo -e "${YELLOW}   (ChromaDB 会继续在 Docker 中运行，若需停止请执行 docker compose down)${NC}"
echo -e "${YELLOW}--------------------------------------------------${NC}"

# 前台运行 nest 服务，这样能直接看到日志
npm run start:dev
