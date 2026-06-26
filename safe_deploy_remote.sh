#!/bin/bash
# ============================================================
#  学智画像 - 零风险远程部署脚本（服务器执行端）
# 
#  功能: 备份 -> 停止 -> 部署 -> 验证 -> (失败自动回滚)
#  使用: bash safe_deploy_remote.sh deploy /opt/xuezhi-portrait /tmp/deploy_package.tar.gz 20260626_120000
#  回滚: bash safe_deploy_remote.sh rollback /opt/xuezhi-portrait /opt/xuezhi-portrait_backup_20260626_120000
# ============================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}   $(date '+%H:%M:%S') $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $(date '+%H:%M:%S') $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%H:%M:%S') $1"; }
log_step()  { echo ""; echo "============================================"; echo -e "${BLUE}>>> $1${NC}"; echo "============================================"; }

# ============================================================
#  配置变量
# ============================================================
VERIFY_RETRIES=5          # 验证重试次数
VERIFY_INTERVAL=6         # 每次重试间隔（秒）
HEALTH_CHECK_URL="http://localhost:80/"
DOCKER_COMPOSE_CMD="docker compose"  # 或 docker-compose (旧版)

# 检测 docker compose 命令格式
detect_docker() {
    if docker compose version &>/dev/null; then
        DOCKER_COMPOSE_CMD="docker compose"
    elif docker-compose version &>/dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        log_error "未找到 docker compose 或 docker-compose 命令"
        exit 1
    fi
    log_info "使用命令: $DOCKER_COMPOSE_CMD"
}

# ============================================================
#  部署前检查
# ============================================================
preflight_check() {
    local PROJECT_DIR="$1"
    
    log_step "[部署前检查]"
    
    # 检查项目目录
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    log_ok "项目目录存在: $PROJECT_DIR"
    
    # 检查 docker-compose.yml
    if [ ! -f "$PROJECT_DIR/docker-compose.yml" ]; then
        log_error "docker-compose.yml 不存在"
        exit 1
    fi
    log_ok "docker-compose.yml 存在"
    
    # 检查磁盘空间 (至少需要2GB)
    local available_kb=$(df / | awk 'NR==2 {print $4}')
    local available_mb=$((available_kb / 1024))
    if [ "$available_mb" -lt 2048 ]; then
        log_warn "磁盘可用空间不足2GB (当前: ${available_mb}MB)，部署可能失败"
        log_warn "建议清理磁盘后再部署"
        read -p "是否继续? (y/N): " confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            exit 1
        fi
    fi
    log_ok "磁盘空间充足 (可用: ${available_mb}MB)"
    
    # 检查Docker状态
    if ! docker info &>/dev/null; then
        log_error "Docker 未运行，请先启动Docker服务"
        exit 1
    fi
    log_ok "Docker 服务运行中"
    
    # 记录当前运行的容器信息
    log_info "当前运行容器:"
    cd "$PROJECT_DIR" && $DOCKER_COMPOSE_CMD ps 2>/dev/null || log_warn "获取容器状态失败（可能未运行）"
}

# ============================================================
#  备份当前版本
# ============================================================
create_backup() {
    local PROJECT_DIR="$1"
    local TIMESTAMP="$2"
    local BACKUP_DIR="${PROJECT_DIR}_backup_${TIMESTAMP}"
    
    log_step "[创建备份]"
    log_info "备份目录: $BACKUP_DIR"
    
    mkdir -p "$BACKUP_DIR"
    
    cd "$PROJECT_DIR"
    
    # 1. 备份数据库 (SQLite instance目录)
    if [ -d "instance" ]; then
        log_info "备份数据库文件..."
        cp -r instance "$BACKUP_DIR/instance"
        if [ -f "instance/quiz_system.db" ]; then
            local db_size=$(du -h instance/quiz_system.db 2>/dev/null | cut -f1)
            log_ok "数据库已备份 (大小: $db_size)"
        fi
    else
        log_warn "instance 目录不存在，跳过数据库备份"
    fi
    
    # 2. 备份logs目录
    if [ -d "logs" ]; then
        cp -r logs "$BACKUP_DIR/logs" 2>/dev/null || true
    fi
    
    # 3. 备份docker-compose.yml和nginx.conf
    cp docker-compose.yml "$BACKUP_DIR/" 2>/dev/null || true
    cp nginx.conf "$BACKUP_DIR/" 2>/dev/null || true
    cp Dockerfile "$BACKUP_DIR/" 2>/dev/null || true
    cp .env "$BACKUP_DIR/" 2>/dev/null || true
    
    # 4. 保存当前Docker镜像信息
    log_info "保存Docker镜像信息..."
    docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" | grep -i xuezhi > "$BACKUP_DIR/docker_images.txt" 2>/dev/null || true
    docker images | grep -E "xuezhi|nginx" > "$BACKUP_DIR/docker_images_full.txt" 2>/dev/null || true
    
    # 5. 备份整个源码（含当前运行版本）
    log_info "备份当前源码..."
    # 排除大型文件和不必要的目录
    tar czf "$BACKUP_DIR/source_backup.tar.gz" \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='logs' \
        --exclude='outputs/**/*.pptx' \
        -C "$PROJECT_DIR" . 2>/dev/null || log_warn "源码备份部分文件可能失败"
    
    if [ -f "$BACKUP_DIR/source_backup.tar.gz" ]; then
        local src_size=$(du -h "$BACKUP_DIR/source_backup.tar.gz" | cut -f1)
        log_ok "源码已备份 (大小: $src_size)"
    fi
    
    # 6. 保存当前git commit信息（如果有）
    if [ -d "$PROJECT_DIR/.git" ]; then
        git rev-parse HEAD > "$BACKUP_DIR/git_commit.txt" 2>/dev/null || true
        git log --oneline -5 > "$BACKUP_DIR/git_log.txt" 2>/dev/null || true
    fi
    
    # 7. 生成回滚脚本
    log_info "生成回滚脚本..."
    cat > "$BACKUP_DIR/rollback.sh" << ROLLBACK_EOF
#!/bin/bash
# ============================================================
#  自动回滚脚本
#  生成时间: $(date '+%Y-%m-%d %H:%M:%S')
#  使用方法: bash ${BACKUP_DIR}/rollback.sh
# ============================================================
set -e

BACKUP_DIR="$BACKUP_DIR"
PROJECT_DIR="$PROJECT_DIR"

echo "============================================"
echo "  执行回滚操作"
echo "  备份时间: $TIMESTAMP"
echo "============================================"
echo ""

# 确认操作
read -p "确定要回滚到 $TIMESTAMP 的版本吗? 输入 'ROLLBACK' 确认: " confirm
if [ "\$confirm" != "ROLLBACK" ]; then
    echo "回滚已取消"
    exit 0
fi

echo "[1/5] 停止当前服务..."
cd "\$PROJECT_DIR"
$DOCKER_COMPOSE_CMD down --timeout 30 2>/dev/null || docker-compose down --timeout 30 2>/dev/null || true

echo "[2/5] 恢复数据库..."
if [ -d "\$BACKUP_DIR/instance" ]; then
    rm -rf "\$PROJECT_DIR/instance" 2>/dev/null || true
    cp -r "\$BACKUP_DIR/instance" "\$PROJECT_DIR/instance"
    echo "  数据库已恢复"
fi

echo "[3/5] 恢复源码..."
if [ -f "\$BACKUP_DIR/source_backup.tar.gz" ]; then
    cd "\$PROJECT_DIR"
    # 保留 instance 和 logs 目录
    if [ -d "instance" ]; then mv instance /tmp/instance_rollback; fi
    if [ -d "logs" ]; then mv logs /tmp/logs_rollback; fi
    
    # 清理并恢复源码
    find . -mindepth 1 -maxdepth 1 ! -name '.' ! -name '..' -exec rm -rf {} + 2>/dev/null || true
    tar xzf "\$BACKUP_DIR/source_backup.tar.gz" -C "\$PROJECT_DIR"
    
    # 恢复instance和logs
    if [ -d /tmp/instance_rollback ]; then 
        rm -rf "\$PROJECT_DIR/instance" 2>/dev/null || true
        mv /tmp/instance_rollback "\$PROJECT_DIR/instance"
    fi
    if [ -d /tmp/logs_rollback ]; then
        rm -rf "\$PROJECT_DIR/logs" 2>/dev/null || true
        mv /tmp/logs_rollback "\$PROJECT_DIR/logs"
    fi
    
    echo "  源码已恢复"
fi

echo "[4/5] 重建Docker镜像..."
cd "\$PROJECT_DIR"
$DOCKER_COMPOSE_CMD build --no-cache 2>/dev/null || docker-compose build --no-cache

echo "[5/5] 启动服务..."
$DOCKER_COMPOSE_CMD up -d 2>/dev/null || docker-compose up -d

echo ""
echo "回滚完成！请验证服务是否正常: curl $HEALTH_CHECK_URL"
echo ""
ROLLBACK_EOF

    chmod +x "$BACKUP_DIR/rollback.sh"
    
    # 8. 备份清单
    cat > "$BACKUP_DIR/BACKUP_INFO.txt" << EOF
========================================
  备份信息
========================================
备份时间: $(date '+%Y-%m-%d %H:%M:%S')
时间戳:   $TIMESTAMP
项目路径: $PROJECT_DIR
备份路径: $BACKUP_DIR

包含内容:
  - 数据库文件 (instance/)
  - 源码完整备份 (source_backup.tar.gz)
  - Docker 配置文件 (docker-compose.yml, Dockerfile, nginx.conf)
  - Docker 镜像信息 (docker_images.txt)
  - 自动回滚脚本 (rollback.sh)

回滚方法:
  bash $BACKUP_DIR/rollback.sh
========================================
EOF

    log_ok "备份完成: $BACKUP_DIR"
    echo "$BACKUP_DIR" > /tmp/xuezhi_last_backup
}

# ============================================================
#  停止现有服务
# ============================================================
stop_services() {
    local PROJECT_DIR="$1"
    
    log_step "[停止现有服务]"
    cd "$PROJECT_DIR"
    
    log_info "停止容器 (graceful shutdown, timeout=30s)..."
    if $DOCKER_COMPOSE_CMD down --timeout 30 2>/dev/null; then
        log_ok "服务已正常停止"
    else
        log_warn "docker compose down 失败，尝试强制停止..."
        docker-compose down --timeout 30 2>/dev/null || true
        # 强制清理残留容器
        docker ps -a | grep "$PROJECT_DIR" | awk '{print $1}' | xargs -r docker stop 2>/dev/null || true
        docker ps -a | grep "$PROJECT_DIR" | awk '{print $1}' | xargs -r docker rm 2>/dev/null || true
    fi
    
    # 确认所有容器已停止
    sleep 2
    local running=$(cd "$PROJECT_DIR" && $DOCKER_COMPOSE_CMD ps --services --filter "status=running" 2>/dev/null | wc -l)
    if [ "$running" -gt 0 ]; then
        log_warn "仍有 $running 个容器在运行"
    else
        log_ok "所有容器已停止"
    fi
}

# ============================================================
#  部署新版本
# ============================================================
deploy_new_version() {
    local PROJECT_DIR="$1"
    local PACKAGE_PATH="$2"
    
    log_step "[部署新版本]"
    
    # 1. 解压新代码
    log_info "解压新版本代码..."
    cd "$PROJECT_DIR"
    
    # 先清理旧代码（保留instance和logs）
    log_info "清理旧代码（保留 instance 和 logs）..."
    
    # 安全地保存 instance 和 logs
    if [ -d "$PROJECT_DIR/instance" ]; then
        cp -r "$PROJECT_DIR/instance" /tmp/instance_deploy_backup
        log_info "instance 已临时保存到 /tmp"
    fi
    if [ -d "$PROJECT_DIR/logs" ]; then
        cp -r "$PROJECT_DIR/logs" /tmp/logs_deploy_backup 2>/dev/null || true
    fi
    
    # 清理目录（保留隐藏文件如 .env）
    find "$PROJECT_DIR" -mindepth 1 -maxdepth 1 ! -name 'instance' ! -name 'logs' ! -name '.env' -exec rm -rf {} + 2>/dev/null || true
    # 也清理 instance 和 logs 目录本身（我们会恢复数据）
    rm -rf "$PROJECT_DIR/instance" "$PROJECT_DIR/logs" 2>/dev/null || true
    
    # 解压新包
    tar xzf "$PACKAGE_PATH" -C "$PROJECT_DIR"
    log_ok "新版本代码已解压"
    
    # 恢复 instance 和 logs
    if [ -d /tmp/instance_deploy_backup ]; then
        rm -rf "$PROJECT_DIR/instance" 2>/dev/null || true
        cp -r /tmp/instance_deploy_backup "$PROJECT_DIR/instance"
        rm -rf /tmp/instance_deploy_backup
        log_info "instance 数据已恢复"
    else
        mkdir -p "$PROJECT_DIR/instance"
        log_warn "未找到之前的 instance 数据，创建空目录"
    fi
    
    if [ -d /tmp/logs_deploy_backup ]; then
        rm -rf "$PROJECT_DIR/logs" 2>/dev/null || true
        cp -r /tmp/logs_deploy_backup "$PROJECT_DIR/logs"
        rm -rf /tmp/logs_deploy_backup
    else
        mkdir -p "$PROJECT_DIR/logs"
    fi
    
    # 确保文件权限正确
    chmod -R 755 "$PROJECT_DIR" 2>/dev/null || true
    
    # 2. 验证关键文件
    log_info "验证关键部署文件..."
    local missing_files=""
    for f in Dockerfile docker-compose.yml requirements.txt run.py wsgi.py; do
        if [ ! -f "$PROJECT_DIR/$f" ]; then
            missing_files="$missing_files $f"
        fi
    done
    if [ -n "$missing_files" ]; then
        log_error "缺少关键文件:$missing_files"
        return 1
    fi
    log_ok "关键文件验证通过"
    
    # 3. 构建Docker镜像
    log_info "构建Docker镜像 (这可能需要2-5分钟)..."
    cd "$PROJECT_DIR"
    
    if $DOCKER_COMPOSE_CMD build --no-cache 2>&1; then
        log_ok "Docker镜像构建成功"
    else
        log_error "Docker镜像构建失败！"
        return 2
    fi
    
    # 4. 启动服务
    log_info "启动新版本服务..."
    if $DOCKER_COMPOSE_CMD up -d 2>&1; then
        log_ok "服务启动命令执行成功"
    else
        log_error "服务启动失败！"
        return 3
    fi
    
    return 0
}

# ============================================================
#  功能验证
# ============================================================
verify_deployment() {
    local PROJECT_DIR="$1"
    
    log_step "[功能验证]"
    
    # 1. 容器状态检查
    log_info "检查容器运行状态..."
    sleep 5  # 等待容器完全启动
    
    cd "$PROJECT_DIR"
    local web_status=$($DOCKER_COMPOSE_CMD ps web --format "{{.Status}}" 2>/dev/null | head -1)
    local nginx_status=$($DOCKER_COMPOSE_CMD ps nginx --format "{{.Status}}" 2>/dev/null | head -1)
    
    if echo "$web_status" | grep -q "Up"; then
        log_ok "Web 容器运行中: $web_status"
    else
        log_error "Web 容器未运行: $web_status"
        return 1
    fi
    
    if echo "$nginx_status" | grep -q "Up"; then
        log_ok "Nginx 容器运行中: $nginx_status"
    else
        log_warn "Nginx 容器状态: $nginx_status"
    fi
    
    # 2. HTTP 健康检查（带重试）
    log_info "HTTP 健康检查 (URL: $HEALTH_CHECK_URL)..."
    local http_ok=false
    for i in $(seq 1 $VERIFY_RETRIES); do
        local http_code=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 10 "$HEALTH_CHECK_URL" 2>/dev/null || echo "000")
        
        if [ "$http_code" = "200" ] || [ "$http_code" = "302" ]; then
            log_ok "HTTP $http_code - 服务正常 (第${i}次尝试)"
            http_ok=true
            break
        elif [ "$http_code" = "000" ]; then
            log_warn "连接失败，等待 ${VERIFY_INTERVAL}s 后重试... (${i}/${VERIFY_RETRIES})"
        else
            log_warn "HTTP $http_code - 非预期状态码，等待重试... (${i}/${VERIFY_RETRIES})"
        fi
        
        if [ $i -lt $VERIFY_RETRIES ]; then
            sleep $VERIFY_INTERVAL
        fi
    done
    
    if [ "$http_ok" = false ]; then
        log_error "HTTP 健康检查失败！服务可能未正常启动。"
        log_info "最近的web容器日志:"
        $DOCKER_COMPOSE_CMD logs --tail=30 web 2>/dev/null || docker-compose logs --tail=30 web
        return 2
    fi
    
    # 3. 数据库检查
    log_info "检查数据库..."
    if $DOCKER_COMPOSE_CMD exec -T web test -f /app/instance/quiz_system.db 2>/dev/null; then
        log_ok "数据库文件存在"
    else
        log_info "数据库文件不存在，尝试初始化..."
        if $DOCKER_COMPOSE_CMD exec -T web python set_db.py 2>/dev/null; then
            log_ok "数据库已初始化"
        else
            log_warn "数据库初始化失败（可能已有数据）"
        fi
    fi
    
    # 4. 页面内容检查
    log_info "检查响应内容..."
    local page_content=$(curl -s --connect-timeout 10 "$HEALTH_CHECK_URL" 2>/dev/null | head -c 500)
    if echo "$page_content" | grep -qi "html"; then
        log_ok "页面包含有效HTML内容"
    else
        log_warn "页面内容检查异常"
    fi
    
    log_ok "功能验证全部通过"
    return 0
}

# ============================================================
#  回滚操作
# ============================================================
do_rollback() {
    local PROJECT_DIR="$1"
    local BACKUP_DIR="$2"
    
    log_step "[!! 开始回滚 !!]"
    log_error "部署验证失败，正在回滚到备份版本..."
    
    if [ ! -f "$BACKUP_DIR/rollback.sh" ]; then
        log_error "回滚脚本不存在: $BACKUP_DIR/rollback.sh"
        log_error "请手动回滚！备份目录: $BACKUP_DIR"
        exit 1
    fi
    
    # 自动执行回滚（不等待确认，因为已确认需要回滚）
    cd "$PROJECT_DIR"
    
    log_info "停止当前服务..."
    $DOCKER_COMPOSE_CMD down --timeout 30 2>/dev/null || docker-compose down --timeout 30 2>/dev/null || true
    
    log_info "恢复数据库..."
    if [ -d "$BACKUP_DIR/instance" ]; then
        rm -rf "$PROJECT_DIR/instance" 2>/dev/null || true
        cp -r "$BACKUP_DIR/instance" "$PROJECT_DIR/instance"
        log_ok "数据库已恢复"
    fi
    
    log_info "恢复源码..."
    if [ -f "$BACKUP_DIR/source_backup.tar.gz" ]; then
        if [ -d "$PROJECT_DIR/instance" ]; then mv "$PROJECT_DIR/instance" /tmp/instance_rollback_auto 2>/dev/null; fi
        if [ -d "$PROJECT_DIR/logs" ]; then mv "$PROJECT_DIR/logs" /tmp/logs_rollback_auto 2>/dev/null; fi
        
        find "$PROJECT_DIR" -mindepth 1 -maxdepth 1 ! -name '.' ! -name '..' -exec rm -rf {} + 2>/dev/null || true
        tar xzf "$BACKUP_DIR/source_backup.tar.gz" -C "$PROJECT_DIR"
        
        if [ -d /tmp/instance_rollback_auto ]; then mv /tmp/instance_rollback_auto "$PROJECT_DIR/instance"; fi
        if [ -d /tmp/logs_rollback_auto ]; then mv /tmp/logs_rollback_auto "$PROJECT_DIR/logs"; fi
        log_ok "源码已恢复"
    fi
    
    log_info "重建并启动服务..."
    $DOCKER_COMPOSE_CMD build --no-cache 2>/dev/null || docker-compose build --no-cache
    $DOCKER_COMPOSE_CMD up -d 2>/dev/null || docker-compose up -d
    
    log_info "验证回滚结果..."
    sleep 10
    local rollback_code=$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 10 "$HEALTH_CHECK_URL" 2>/dev/null || echo "000")
    if [ "$rollback_code" = "200" ] || [ "$rollback_code" = "302" ]; then
        log_ok "回滚成功！服务已恢复 (HTTP $rollback_code)"
    else
        log_error "回滚后服务仍未恢复正常 (HTTP $rollback_code)，请人工介入！"
        log_error "备份目录: $BACKUP_DIR"
        $DOCKER_COMPOSE_CMD logs --tail=50 web 2>/dev/null || docker-compose logs --tail=50 web
    fi
}

# ============================================================
#  主入口
# ============================================================
main_deploy() {
    local PROJECT_DIR="$1"
    local PACKAGE_PATH="$2"
    local TIMESTAMP="${3:-$(date +%Y%m%d_%H%M%S)}"
    
    log_info "============================================"
    log_info "  学智画像 - 零风险安全部署"
    log_info "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "  项目: $PROJECT_DIR"
    log_info "  版本: $TIMESTAMP"
    log_info "============================================"
    
    # 检测Docker命令
    detect_docker
    
    # Phase 1: 部署前检查
    preflight_check "$PROJECT_DIR"
    
    # Phase 2: 备份
    create_backup "$PROJECT_DIR" "$TIMESTAMP"
    BACKUP_DIR="${PROJECT_DIR}_backup_${TIMESTAMP}"
    
    # Phase 3: 停止服务
    stop_services "$PROJECT_DIR"
    
    # Phase 4: 部署新版本
    if ! deploy_new_version "$PROJECT_DIR" "$PACKAGE_PATH"; then
        log_error "部署新版本失败！"
        do_rollback "$PROJECT_DIR" "$BACKUP_DIR"
        exit 1
    fi
    
    # Phase 5: 验证
    if verify_deployment "$PROJECT_DIR"; then
        log_ok ""
        log_ok "============================================"
        log_ok "  部署成功！新版本已上线"
        log_ok "  备份位置: $BACKUP_DIR"
        log_ok "  访问地址: $HEALTH_CHECK_URL"
        log_ok "============================================"
        rm -f /tmp/xuezhi_last_backup
        exit 0
    else
        log_error "部署验证失败！"
        do_rollback "$PROJECT_DIR" "$BACKUP_DIR"
        exit 1
    fi
}

main_rollback() {
    local PROJECT_DIR="$1"
    local BACKUP_DIR="$2"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "备份目录不存在: $BACKUP_DIR"
        exit 1
    fi
    
    detect_docker
    do_rollback "$PROJECT_DIR" "$BACKUP_DIR"
}

# ============================================================
#  命令分发
# ============================================================
case "$1" in
    deploy)
        if [ $# -lt 3 ]; then
            echo "用法: $0 deploy <项目目录> <部署包路径> [时间戳]"
            echo "示例: $0 deploy /opt/xuezhi-portrait /tmp/deploy_package.tar.gz 20260626_120000"
            exit 1
        fi
        main_deploy "$2" "$3" "$4"
        ;;
    rollback)
        if [ $# -lt 3 ]; then
            echo "用法: $0 rollback <项目目录> <备份目录>"
            echo "示例: $0 rollback /opt/xuezhi-portrait /opt/xuezhi-portrait_backup_20260626_120000"
            exit 1
        fi
        main_rollback "$2" "$3"
        ;;
    *)
        echo "用法:"
        echo "  部署: $0 deploy <项目目录> <部署包路径> [时间戳]"
        echo "  回滚: $0 rollback <项目目录> <备份目录>"
        exit 1
        ;;
esac
