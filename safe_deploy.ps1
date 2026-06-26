<# 
.SYNOPSIS
    学智画像 - 零风险安全部署脚本（本地执行端）
.DESCRIPTION
    将当前项目代码安全部署到远程服务器，包含完整的备份/验证/回滚机制。
.PARAMETER ServerIP
    远程服务器IP地址
.PARAMETER User
    SSH登录用户名
.PARAMETER Port
    SSH端口（默认22）
.PARAMETER RemoteDir
    服务器上的项目目录（默认 /opt/xuezhi-portrait）
.EXAMPLE
    .\safe_deploy.ps1 -ServerIP 123.56.247.117 -User root -KeyPath ~/.ssh/id_rsa
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP = "123.56.247.117",
    
    [Parameter(Mandatory=$true)]
    [string]$User = "root",
    
    [int]$Port = 22,
    
    [string]$KeyPath = "",
    
    [string]$RemoteDir = "/opt/xuezhi-portrait",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipConfirmation = $false
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$PACKAGE_NAME = "deploy_package_${TIMESTAMP}.tar.gz"
$REMOTE_SCRIPT = "safe_deploy_remote.sh"

# 颜色函数
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[OK]   $args" -ForegroundColor Green }
function Write-Warn { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Error { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Step { Write-Host "`n============================================" -ForegroundColor Blue; Write-Host ">>> $args" -ForegroundColor Blue; Write-Host "============================================" -ForegroundColor Blue }

# SSH命令构建
$SSH_OPTS = @("-p", "$Port", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=10", "-o", "ServerAliveInterval=30")
if ($KeyPath) {
    $SSH_OPTS += @("-i", $KeyPath)
}
$SCP_OPTS = $SSH_OPTS

function Invoke-SSH {
    param([string]$Command)
    $fullCmd = "ssh $($SSH_OPTS -join ' ') ${User}@${ServerIP} '$Command'"
    Write-Host "  [EXEC] $Command" -ForegroundColor DarkGray
    $result = Invoke-Expression $fullCmd 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "SSH命令执行失败 (exit=$LASTEXITCODE): $result"
        throw "SSH_ERROR"
    }
    return $result
}

function Invoke-SCP {
    param([string]$Source, [string]$Dest)
    $fullCmd = "scp $($SCP_OPTS -join ' ') '$Source' '${User}@${ServerIP}:${Dest}'"
    Write-Host "  [SCP] $Source -> ${Dest}" -ForegroundColor DarkGray
    Invoke-Expression $fullCmd 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "SCP传输失败 (exit=$LASTEXITCODE)"
        throw "SCP_ERROR"
    }
}

# =====================================================
#  主流程
# =====================================================

Write-Host @"
╔══════════════════════════════════════════════════════╗
║       学智画像 - 零风险安全部署工具 v2.0              ║
║       目标: ${ServerIP}:${Port}                           ║
║       路径: ${RemoteDir}                         ║
╚══════════════════════════════════════════════════════╝
"@

# --- 部署前确认 ---
if (-not $SkipConfirmation) {
    Write-Warn "即将部署到生产服务器 ${ServerIP}，请确认以下信息："
    Write-Host "  项目目录: $RemoteDir"
    Write-Host "  备份位置: ${RemoteDir}_backup_${TIMESTAMP}"
    Write-Host "  部署时间戳: $TIMESTAMP"
    Write-Host ""
    $confirm = Read-Host "输入 'DEPLOY' 确认继续部署"
    if ($confirm -ne "DEPLOY") {
        Write-Error "部署已取消"
        exit 1
    }
}

# ==================== Phase 1: 连接验证 ====================
Write-Step "Phase 1/5: 连接验证与服务器健康检查"

try {
    Write-Info "测试SSH连接..."
    $hostname = Invoke-SSH -Command "hostname && uname -a"
    Write-Success "SSH连接成功: $hostname"
    
    Write-Info "检查Docker环境..."
    $dockerInfo = Invoke-SSH -Command "docker --version && docker compose version 2>/dev/null || docker-compose --version"
    Write-Success "Docker: $dockerInfo"
    
    Write-Info "检查目标目录..."
    $dirCheck = Invoke-SSH -Command "if [ -d '$RemoteDir' ]; then echo 'EXISTS'; ls -la '$RemoteDir'/docker-compose.yml 2>/dev/null; else echo 'NOT_FOUND'; fi"
    if ($dirCheck -match "NOT_FOUND") {
        Write-Error "目标目录 $RemoteDir 不存在！请确认服务器上的项目路径。"
        exit 1
    }
    Write-Success "目标目录已存在"
    
    Write-Info "检查磁盘空间..."
    $diskInfo = Invoke-SSH -Command "df -h / | tail -1"
    Write-Success "磁盘空间: $diskInfo"
    
} catch {
    Write-Error "连接验证失败: $_"
    Write-Error "请检查: 1)服务器是否可访问 2)SSH密钥是否正确 3)防火墙是否放行端口"
    exit 1
}

# ==================== Phase 2: 打包上传 ====================
Write-Step "Phase 2/5: 打包项目代码并上传"

# 构建排除列表
$excludeList = @(
    "__pycache__", "*.pyc", "*.pyo", ".git", ".vscode", ".idea",
    "node_modules", "instance", "logs", "outputs/**/*.pptx", "outputs/**/preview/**",
    "*.db", "*.sqlite", "*.sqlite3",
    "_competition_package", "screenshots/*.png",
    # 保留部署相关文件
    # 排除大型输出和截图（不影响运行）
    "xuezhi-portrait-source.zip",
    "*.egg-info"
)

$tarExclude = ($excludeList | ForEach-Object { "--exclude='$_'" }) -join " "

Write-Info "创建部署包（排除编译/数据/缓存文件）..."
# 使用 tar 打包（Windows 10 1803+ 内置）
$tarCmd = "tar $tarExclude -czf '$PACKAGE_NAME' -C '$scriptDir' ."
Write-Host "  [TAR] $tarCmd" -ForegroundColor DarkGray
Invoke-Expression $tarCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "打包失败"
    exit 1
}

$pkgSize = [math]::Round((Get-Item $PACKAGE_NAME).Length / 1MB, 2)
Write-Success "部署包已创建: $PACKAGE_NAME ($pkgSize MB)"

Write-Info "上传部署包到服务器..."
Invoke-SCP -Source "$scriptDir\$PACKAGE_NAME" -Dest "/tmp/$PACKAGE_NAME"
Write-Success "部署包上传完成"

Write-Info "上传远程部署脚本..."
Invoke-SCP -Source "$scriptDir\$REMOTE_SCRIPT" -Dest "/tmp/$REMOTE_SCRIPT"
Write-Success "远程脚本上传完成"

# 清理本地临时包
Remove-Item "$scriptDir\$PACKAGE_NAME" -Force

# ==================== Phase 3: 远程执行部署 ====================
Write-Step "Phase 3/5: 服务器端执行安全部署"

Write-Info "在服务器上执行安全部署流程..."
Write-Warn "此阶段将在服务器上自动完成：备份现有版本 -> 停止服务 -> 部署新版本 -> 功能验证 -> (必要时回滚)"
Write-Host ""

try {
    $deployOutput = Invoke-SSH -Command @"
bash /tmp/$REMOTE_SCRIPT deploy '$RemoteDir' '/tmp/$PACKAGE_NAME' '$TIMESTAMP'
"@
    Write-Host $deployOutput
    
} catch {
    Write-Error "远程部署脚本执行失败: $_"
    Write-Error "请SSH登录服务器手动检查: ssh ${User}@${ServerIP}"
    exit 1
}

# ==================== Phase 4: 验证 ====================
Write-Step "Phase 4/5: 部署结果验证"

Write-Info "检查服务状态..."
$dockerPs = Invoke-SSH -Command "cd '$RemoteDir' && docker compose ps --format 'table {{.Name}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || docker-compose ps"
Write-Host $dockerPs

Write-Info "HTTP健康检查..."
$healthCheck = Invoke-SSH -Command "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 10 http://localhost:80/ || echo 'FAILED'"
if ($healthCheck -eq "200") {
    Write-Success "HTTP 200 - 服务正常响应"
} else {
    Write-Warn "HTTP返回: $healthCheck"
    Write-Warn "服务可能仍在启动中，等待30秒后重试..."
    Start-Sleep -Seconds 30
    $healthCheck2 = Invoke-SSH -Command "curl -s -o /dev/null -w '%{http_code}' --connect-timeout 10 http://localhost:80/ || echo 'FAILED'"
    if ($healthCheck2 -eq "200") {
        Write-Success "HTTP 200 - 服务已就绪"
    } else {
        Write-Error "HTTP检查失败: $healthCheck2"
    }
}

# ==================== Phase 5: 清理 ====================
Write-Step "Phase 5/5: 清理临时文件"

Write-Info "清理服务器临时文件..."
Invoke-SSH -Command "rm -f /tmp/$PACKAGE_NAME /tmp/$REMOTE_SCRIPT"
Write-Success "临时文件已清理"

# ==================== 最终报告 ====================
Write-Host @"

╔══════════════════════════════════════════════════════╗
║              部署完成！                                 ║
╠══════════════════════════════════════════════════════╣
║  访问地址 : http://${ServerIP}                         ║
║  备份位置 : ${RemoteDir}_backup_${TIMESTAMP}           ║
╠══════════════════════════════════════════════════════╣
║  如需回滚，请在服务器上执行:                             ║
║  ssh ${User}@${ServerIP}                                ║
║  bash ${RemoteDir}_backup_${TIMESTAMP}/rollback.sh    ║
╠══════════════════════════════════════════════════════╣
║  查看日志:                                              ║
║  ssh ${User}@${ServerIP} "cd ${RemoteDir} && docker compose logs -f web" ║
╚══════════════════════════════════════════════════════╝

"@

Write-Success "安全部署流程全部完成！"
Write-Info "建议立即在浏览器中访问 http://${ServerIP} 进行人工验证。"
