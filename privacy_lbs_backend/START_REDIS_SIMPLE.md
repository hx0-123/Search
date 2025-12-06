# 最简单的 Redis 启动方法（无需 Docker）

## 问题
Docker Desktop 无法启动，但我们仍然需要 Redis 来运行 Celery。

## 解决方案：使用 WSL 直接运行 Redis（推荐）

### 方法1：手动在 WSL 中启动（最简单）

#### 步骤1：打开 WSL 终端
```powershell
wsl
```

#### 步骤2：安装 Redis（如果未安装）
```bash
sudo apt update
sudo apt install redis-server -y
```

#### 步骤3：启动 Redis
```bash
sudo service redis-server start
```

#### 步骤4：验证 Redis 运行
```bash
redis-cli ping
# 应该返回: PONG
```

#### 步骤5：保持 WSL 窗口打开，在 PowerShell 中启动 Celery
```powershell
# 新开一个 PowerShell 窗口
cd D:\Search\privacy_lbs_backend
python -m celery -A privacy_lbs_backend worker --loglevel=info --pool=solo
```

### 方法2：使用批处理脚本（一键启动）

我已经创建了 `start_redis_wsl.bat`，直接双击运行即可：

```powershell
cd D:\Search\privacy_lbs_backend
.\start_redis_wsl.bat
```

### 方法3：修改 WSL 路径（如果路径不同）

如果项目路径不是 `/mnt/d/Search/privacy_lbs_backend`，请修改 `start_redis_wsl.bat` 中的路径。

## 验证 Redis 连接

在 PowerShell 中运行：
```powershell
cd D:\Search\privacy_lbs_backend
python test_redis.py
```

应该显示：✅ Redis 连接成功！

## 启动 Celery Worker

Redis 运行后，启动 Celery：
```powershell
cd D:\Search\privacy_lbs_backend
python -m celery -A privacy_lbs_backend worker --loglevel=info --pool=solo
```

## 停止 Redis

在 WSL 中：
```bash
sudo service redis-server stop
```

## 如果 WSL 未安装

### 安装 WSL
```powershell
# 以管理员身份运行 PowerShell
wsl --install
```

安装后重启电脑。

## 其他替代方案

### 方案A：使用 Memurai（Windows 原生，无需 Docker/WSL）
1. 下载：https://www.memurai.com/get-memurai
2. 安装后自动启动
3. 无需任何配置

### 方案B：临时使用数据库（仅开发测试）
修改 `privacy_lbs_backend/settings.py`：
```python
# 注释掉 Redis
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# 使用数据库
CELERY_BROKER_URL = 'db+sqlite:///celery.db'
CELERY_RESULT_BACKEND = 'db+sqlite:///celery_results.db'
```

**注意：** 需要安装额外依赖：
```powershell
pip install kombu[sqlalchemy]
```

