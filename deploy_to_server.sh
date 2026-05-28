#!/bin/bash
set -e

echo "=========================================="
echo "  学智画像 - 阿里云 ECS 一键部署脚本 v2"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# 1. 检查 Docker
echo -e "${YELLOW}[1/5] 检查 Docker 环境...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker 未安装，正在安装...${NC}"
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
    usermod -aG docker $USER
    echo -e "${GREEN}Docker 安装完成，请重新登录后运行: bash deploy_to_server.sh${NC}"
    exit 0
fi

echo -e "${GREEN}Docker 已就绪 ✓${NC}"

# 2. 构建镜像
echo -e "${YELLOW}[2/5] 构建 Docker 镜像（使用阿里云 pip 源，约 2-5 分钟）...${NC}"
docker compose down 2>/dev/null || true
docker compose build --no-cache

# 3. 启动服务
echo -e "${YELLOW}[3/5] 启动容器...${NC}"
docker compose up -d

# 4. 等待并确认服务状态
echo -e "${YELLOW}[4/5] 等待服务启动（最多 60 秒）...${NC}"
for i in $(seq 1 30); do
    if docker compose ps web 2>/dev/null | grep -q 'Up'; then
        if curl -sf http://localhost:80/ >/dev/null 2>&1; then
            echo -e "${GREEN}服务就绪 ✓${NC}"
            break
        fi
    fi
    sleep 2
    echo -n "."
    if [ $i -eq 30 ]; then
        echo ""
        echo -e "${YELLOW}服务可能还在启动中，查看日志: docker compose logs web${NC}"
    fi
done

# 5. 初始化数据库
echo -e "${YELLOW}[5/5] 初始化数据库...${NC}"

# 先检查容器是否在运行
if docker compose ps web 2>/dev/null | grep -q 'Up'; then
    # 检查数据库是否已存在
    if docker compose exec -T web test -f /app/instance/quiz_system.db 2>/dev/null; then
        echo -e "${GREEN}数据库已存在，跳过初始化 ✓${NC}"
    else
        echo "首次部署，正在初始化数据库并生成测试数据..."
        docker compose exec -T web python set_db.py
        echo -e "${GREEN}数据库初始化完成 ✓${NC}"
    fi
else
    # 容器可能刚启动，用 run --rm 来执行
    echo "容器启动中，用临时容器执行数据库初始化..."
    docker compose run --rm web python set_db.py || true
fi

# 6. 显示结果
echo ""
echo "=========================================="
echo -e "${GREEN}        部署完成！${NC}"
echo "=========================================="
echo ""
PUBLIC_IP=$(curl -s -4 ifconfig.me 2>/dev/null || echo "你的服务器公网IP")
echo -e "  访问地址: ${GREEN}http://${PUBLIC_IP}${NC}"
echo ""
echo "  默认账号:"
echo "    管理员  admin     / admin123"
echo "    学生    student   / student123"
echo ""
echo "  常用命令:"
echo "    查看日志    : docker compose logs -f web"
echo "    重启服务    : docker compose restart"
echo "    停止服务    : docker compose down"
echo "    进入容器    : docker compose exec web bash"
echo ""
echo "=========================================="
