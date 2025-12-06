# 快速启动指南

## 当前问题

Celery Worker 无法连接 Redis，错误信息：
```
Error 10061 connecting to localhost:6379. 由于目标计算机积极拒绝，无法连接。
```

**原因：** Redis 服务器没有运行。

## 解决方案（选择一种）

### 方案1：使用 Docker 启动 Redis（最简单，推荐）

#### 步骤1：安装 Docker Desktop
1. 下载：https://www.docker.com/products/docker-desktop
2. 安装并启动 Docker Desktop

#### 步骤2：启动 Redis 容器
```powershell
docker run -d --name redis -p 6379:6379 redis:latest
```

#### 步骤3：验证 Redis 运行
```powershell
docker ps
# 应该看到 redis 容器在运行
```

#### 步骤4：测试连接
```powershell
cd D:\Search\privacy_lbs_backend
python test_redis.py
# 应该显示：✅ Redis 连接成功！
```

#### 步骤5：启动 Celery Worker
```powershell
cd D:\Search\privacy_lbs_backend
python -m celery -A privacy_lbs_backend worker --loglevel=info --pool=solo
```

### 方案2：使用 WSL 安装 Redis

#### 步骤1：启用 WSL（如果未启用）
```powershell
# 以管理员身份运行 PowerShell
wsl --install
```

#### 步骤2：在 WSL 中安装 Redis
```powershell
wsl
sudo apt update
sudo apt install redis-server
redis-server
```

#### 步骤3：在另一个终端启动 Celery
```powershell
cd D:\Search\privacy_lbs_backend
python -m celery -A privacy_lbs_backend worker --loglevel=info --pool=solo
```

### 方案3：临时使用数据库作为消息代理（仅开发测试）

如果暂时不想安装 Redis，可以修改配置使用数据库：

#### 修改 `privacy_lbs_backend/settings.py`：
```python
# 注释掉 Redis 配置
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# 使用数据库（SQLite）
CELERY_BROKER_URL = 'db+sqlite:///celery.db'
CELERY_RESULT_BACKEND = 'db+sqlite:///celery_results.db'
```

**注意：** 这种方式性能较差，仅用于开发测试。

### 方案4：使用 Memurai（Windows Redis 替代品）

1. 下载：https://www.memurai.com/get-memurai
2. 安装后会自动启动服务
3. 默认端口 6379，无需修改配置

## 验证步骤

### 1. 测试 Redis 连接
```powershell
cd D:\Search\privacy_lbs_backend
python test_redis.py
```

### 2. 启动 Celery Worker
```powershell
cd D:\Search\privacy_lbs_backend
python -m celery -A privacy_lbs_backend worker --loglevel=info --pool=solo
```

成功启动后应该看到：
```
[INFO/MainProcess] Connected to redis://localhost:6379/0
[INFO/MainProcess] celery@hostname ready.
```

## 推荐方案

**对于 Windows 用户，强烈推荐使用 Docker：**
1. 安装简单
2. 一键启动
3. 不污染系统
4. 易于管理

```powershell
# 一条命令启动 Redis
docker run -d --name redis -p 6379:6379 redis:latest
```

## 停止 Redis（Docker）

```powershell
# 停止容器
docker stop redis

# 删除容器（可选）
docker rm redis
```


