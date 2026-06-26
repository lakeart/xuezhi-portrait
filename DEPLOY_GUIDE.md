# 学智画像 - 零风险安全部署指南

## 前置条件

1. **SSH访问权限**：确保可以SSH登录到服务器 `123.56.247.117`
2. **部署文件**：本目录下的以下文件
   - `safe_deploy.ps1` — 本地上传与调度脚本（Windows PowerShell）
   - `safe_deploy_remote.sh` — 服务器端安全部署脚本（Linux Bash）
3. **环境要求**：
   - 本地：Windows 10+，PowerShell 5.1+，`ssh`/`scp` 命令可用
   - 服务器：Docker + Docker Compose 已安装并运行

---

## 快速开始

### 方式一：使用SSH密钥

```powershell
.\safe_deploy.ps1 -ServerIP 123.56.247.117 -User root -KeyPath ~/.ssh/id_rsa
```

### 方式二：使用密码登录（交互式）

```powershell
.\safe_deploy.ps1 -ServerIP 123.56.247.117 -User root
```

> 注意：密码方式需要每次输入SSH密码，建议使用SSH密钥方式。

### 指定自定义参数

```powershell
.\safe_deploy.ps1 `
    -ServerIP 123.56.247.117 `
    -User ubuntu `
    -Port 2222 `
    -RemoteDir /home/ubuntu/xuezhi-portrait `
    -KeyPath C:\Users\admin\.ssh\server_key
```

---

## 部署流程说明

整个部署过程分为 **五个阶段**，全自动执行：

```
┌─────────────────────────────────────────────────┐
│ Phase 1  连接验证                                │
│ • 测试SSH连接 • Docker版本检查 • 磁盘空间检查     │
├─────────────────────────────────────────────────┤
│ Phase 2  打包上传                                │
│ • 本地源码打包(tar.gz) • SCP上传到服务器          │
├─────────────────────────────────────────────────┤
│ Phase 3  安全部署 (服务器端)                      │
│ ├─ 01 备份数据库 + 源码 + Docker配置              │
│ ├─ 02 停止现有服务 (graceful shutdown)            │
│ ├─ 03 解压新代码 + 恢复数据库                     │
│ ├─ 04 构建新Docker镜像                            │
│ ├─ 05 启动新服务                                  │
│ └─ 06 功能验证 (HTTP/容器/数据库)                 │
│     ├─ 通过 → 部署完成 ✓                          │
│     └─ 失败 → 自动回滚至备份版本 ✗                │
├─────────────────────────────────────────────────┤
│ Phase 4  结果验证                                │
│ • 容器状态 • HTTP 200检查 • 响应内容验证          │
├─────────────────────────────────────────────────┤
│ Phase 5  清理                                    │
│ • 删除服务器临时文件 • 输出部署报告               │
└─────────────────────────────────────────────────┘
```

---

## 备份与回滚

### 自动备份

每次部署前，系统会自动备份以下内容到 `{项目目录}_backup_{时间戳}/`：

| 备份项 | 内容 |
|--------|------|
| 数据库 | `instance/quiz_system.db`（含所有用户数据和答题记录） |
| 源码 | 完整项目源码（排除编译缓存） |
| 配置 | `docker-compose.yml`、`Dockerfile`、`nginx.conf`、`.env` |
| 镜像信息 | Docker镜像版本记录 |
| 回滚脚本 | 一键回滚脚本 `rollback.sh` |

### 自动回滚

部署后若功能验证失败（HTTP无法返回200），系统将**自动回滚**：

1. 停止当前服务
2. 恢复备份的数据库
3. 恢复备份的源码
4. 重建Docker镜像并启动
5. 验证回滚结果

### 手动回滚

如需手动回滚到某次部署前的版本：

```bash
# SSH登录服务器
ssh root@123.56.247.117

# 执行回滚
bash /opt/xuezhi-portrait_backup_20260626_120000/rollback.sh
```

---

## 故障排查

### 部署失败 - SSH连接问题

```
[ERROR] 连接验证失败
```
**解决**：检查服务器IP、端口、SSH密钥是否正确，确保服务器防火墙放行SSH端口。

### 部署失败 - Docker构建失败

```
[ERROR] Docker镜像构建失败
```
**解决**：
1. SSH登录服务器检查磁盘空间：`df -h`
2. 检查Docker日志：`docker system df`
3. 清理旧镜像：`docker system prune -a`
4. 重新部署

### 部署失败 - 服务启动但HTTP无响应

```bash
# 在服务器上检查
cd /opt/xuezhi-portrait
docker compose logs web --tail=50
docker compose ps
```

### 部署失败 - 数据库问题

```bash
# 检查数据库文件
docker compose exec web ls -la /app/instance/
# 手动初始化
docker compose exec web python set_db.py
```

---

## 安全注意事项

1. **禁止直接替换文件**：始终通过完整的备份-部署-验证流程
2. **不要在业务高峰期部署**：建议在凌晨或低流量时段执行
3. **保留最近3个备份**：磁盘空间允许的情况下，不要立即删除旧备份
4. **.env文件保护**：部署过程不会覆盖服务器上已有的 `.env` 文件
5. **数据库安全**：instance目录挂载为Docker volume，部署时会先备份后恢复

---

## 参数说明

| 参数 | 说明 | 默认值 | 必填 |
|------|------|--------|------|
| `-ServerIP` | 服务器IP地址 | `123.56.247.117` | 是 |
| `-User` | SSH登录用户名 | `root` | 是 |
| `-Port` | SSH端口 | `22` | 否 |
| `-KeyPath` | SSH私钥路径 | 空（使用密码） | 否 |
| `-RemoteDir` | 服务器项目目录 | `/opt/xuezhi-portrait` | 否 |
| `-SkipConfirmation` | 跳过确认步骤 | `false` | 否 |
