#!/bin/bash
set -e

echo "=========================================="
echo "  学智画像 - 阿里云 ECS 一键部署脚本"
echo "=========================================="
echo ""

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取项目目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# 1. 检查 Docker
echo -e "${YELLOW}[1/7] 检查 Docker 环境...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker 未安装，正在安装...${NC}"
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
    usermod -aG docker $USER
    echo -e "${GREEN}Docker 安装完成，请重新登录后再次运行本脚本${NC}"
    exit 0
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}docker-compose 未安装，正在安装...${NC}"
    apt-get update && apt-get install -y docker-compose-plugin
    # 创建兼容别名
    echo 'docker compose "$@"' > /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo -e "${GREEN}Docker 环境检查通过 ✓${NC}"

# 2. 开放防火墙端口
echo -e "${YELLOW}[2/7] 配置防火墙...${NC}"
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp >/dev/null 2>&1 || true
    ufw allow 443/tcp >/dev/null 2>&1 || true
    ufw allow 5000/tcp >/dev/null 2>&1 || true
    echo -e "${GREEN}UFW 防火墙规则已添加 ✓${NC}"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=80/tcp >/dev/null 2>&1 || true
    firewall-cmd --permanent --add-port=443/tcp >/dev/null 2>&1 || true
    firewall-cmd --reload >/dev/null 2>&1 || true
    echo -e "${GREEN}Firewalld 防火墙规则已添加 ✓${NC}"
else
    echo -e "${YELLOW}未检测到防火墙工具，跳过配置${NC}"
fi

# 3. 构建并启动容器
echo -e "${YELLOW}[3/7] 构建 Docker 镜像...${NC}"
docker-compose down >/dev/null 2>&1 || true
docker-compose build --no-cache

echo -e "${YELLOW}[4/7] 启动服务...${NC}"
docker-compose up -d

# 4. 等待服务就绪
echo -e "${YELLOW}[5/7] 等待服务启动...${NC}"
for i in {1..30}; do
    if docker-compose exec -T web curl -sf http://localhost:5000/ >/dev/null 2>&1; then
        echo -e "${GREEN}Web 服务已就绪 ✓${NC}"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 30 ]; then
        echo -e "\n${RED}服务启动超时，请检查日志: docker-compose logs${NC}"
        exit 1
    fi
done

# 5. 数据库初始化
echo -e "${YELLOW}[6/7] 数据库初始化...${NC}"
if [ ! -f "instance/quiz_system.db" ]; then
    echo "首次部署，正在初始化数据库并生成测试数据..."
    docker-compose exec -T web python set_db.py
    echo -e "${GREEN}数据库初始化完成 ✓${NC}"
else
    echo -e "${GREEN}检测到已有数据库，跳过初始化 ✓${NC}"
    read -p "是否重置数据库并重新生成测试数据？(y/N): " reset_db
    if [[ "$reset_db" =~ ^[Yy]$ ]]; then
        docker-compose exec -T web python set_db.py
        echo -e "${GREEN}数据库已重置并重新初始化 ✓${NC}"
    fi
fi

# 6. 显示访问信息
echo ""
echo "=========================================="
echo -e "${GREEN}        部署成功！${NC}"
echo "=========================================="
echo ""

# 获取公网 IP
PUBLIC_IP=$(curl -s -4 ifconfig.me 2>/dev/null || echo "你的服务器公网IP")
echo -e "  公网访问地址: ${GREEN}http://${PUBLIC_IP}${NC}"
echo ""
echo "  默认账号:"
echo "    管理员  admin     / admin123"
echo "    学生    student   / student123"
echo ""
echo "  常用命令:"
echo "    查看日志    : docker-compose logs -f"
echo "    重启服务    : docker-compose restart"
echo "    停止服务    : docker-compose down"
echo "    进入容器    : docker-compose exec web bash"
echo ""
echo "=========================================="
