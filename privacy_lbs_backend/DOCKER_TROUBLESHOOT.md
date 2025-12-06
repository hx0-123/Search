# Docker Desktop 启动问题排查

## 问题：Docker Desktop is unable to start

### 检查步骤

#### 1. 检查 Docker Desktop 是否正在运行

**方法1：查看任务管理器**
- 按 `Ctrl + Shift + Esc` 打开任务管理器
- 查看是否有 `Docker Desktop` 进程在运行

**方法2：查看系统托盘**
- 查看系统托盘（右下角）是否有 Docker 图标
- 如果有，右键点击查看状态

**方法3：命令行检查**
```powershell
# 检查 Docker 服务状态
Get-Service -Name *docker*

# 或者
docker version
```

#### 2. 启动 Docker Desktop

**方法1：从开始菜单启动**
1. 点击 Windows 开始菜单
2. 搜索 "Docker Desktop"
3. 点击启动

**方法2：手动启动服务**
```powershell
# 以管理员身份运行 PowerShell
Start-Service -Name "com.docker.service"
```

**方法3：重启 Docker Desktop**
1. 右键点击系统托盘的 Docker 图标
2. 选择 "Restart Docker Desktop"
3. 等待启动完成（可能需要1-2分钟）

#### 3. 常见启动失败原因

**原因1：WSL 2 未启用或版本过旧**
```powershell
# 检查 WSL 版本
wsl --version

# 如果未安装或版本过旧，更新 WSL
wsl --update
```

**原因2：虚拟化未启用**
- 需要在 BIOS 中启用虚拟化（VT-x/AMD-V）
- 重启电脑进入 BIOS 设置

**原因3：Hyper-V 冲突**
- 如果启用了 Hyper-V，可能与 Docker 冲突
- 尝试禁用 Hyper-V 或使用 WSL 2 后端

**原因4：权限问题**
- 确保以管理员身份运行
- 或者将用户添加到 docker-users 组

#### 4. 检查 Docker Desktop 日志

Docker Desktop 日志位置：
```
%LOCALAPPDATA%\Docker\log.txt
```

查看日志：
```powershell
notepad "$env:LOCALAPPDATA\Docker\log.txt"
```

## 快速解决方案

### 方案1：重启 Docker Desktop

1. **完全关闭 Docker Desktop**
   - 右键系统托盘图标 → Quit Docker Desktop
   - 或任务管理器结束所有 Docker 进程

2. **重新启动**
   - 从开始菜单启动 Docker Desktop
   - 等待完全启动（看到 "Docker Desktop is running"）

3. **验证**
   ```powershell
   docker ps
   # 应该不报错
   ```

### 方案2：使用 WSL 2 后端

1. **打开 Docker Desktop 设置**
   - 右键系统托盘图标 → Settings

2. **切换到 WSL 2**
   - General → Use the WSL 2 based engine（勾选）
   - Apply & Restart

3. **确保 WSL 2 已安装**
   ```powershell
   wsl --update
   wsl --set-default-version 2
   ```

### 方案3：使用替代方案（如果 Docker 无法启动）

如果 Docker Desktop 无法启动，可以使用其他方式运行 Redis：

#### 选项A：使用 WSL 直接运行 Redis
```powershell
# 进入 WSL
wsl

# 安装 Redis
sudo apt update
sudo apt install redis-server -y

# 启动 Redis
sudo service redis-server start

# 验证
redis-cli ping
# 应该返回: PONG
```

#### 选项B：使用 Memurai（Windows 原生 Redis）
1. 下载：https://www.memurai.com/get-memurai
2. 安装后自动启动
3. 无需 Docker

#### 选项C：修改配置使用数据库（仅开发）
修改 `settings.py`：
```python
CELERY_BROKER_URL = 'db+sqlite:///celery.db'
CELERY_RESULT_BACKEND = 'db+sqlite:///celery_results.db'
```

## 验证 Docker 是否正常工作

运行以下命令：
```powershell
# 1. 检查 Docker 版本
docker version

# 2. 运行测试容器
docker run hello-world

# 3. 如果成功，启动 Redis
docker run -d --name redis -p 6379:6379 redis:latest
```

## 如果仍然无法启动

1. **查看详细错误信息**
   - 打开 Docker Desktop
   - 查看 Troubleshoot 标签页的错误信息

2. **重新安装 Docker Desktop**
   - 完全卸载
   - 重启电脑
   - 重新安装最新版本

3. **使用替代方案**
   - 推荐使用 WSL 直接运行 Redis（最简单）

