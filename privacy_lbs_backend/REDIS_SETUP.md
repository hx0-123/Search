# Redis 安装和启动指南

## 问题说明

Celery Worker 报错：`Error 10061 connecting to localhost:6379. 由于目标计算机积极拒绝，无法连接。`

**原因：** Redis 服务器没有运行。Celery 需要 Redis 作为消息代理来传递任务。

## 解决方案

### 方案1：安装并启动 Redis（推荐）

#### Windows 安装 Redis

**方法1：使用 WSL (Windows Subsystem for Linux)**
```powershell
# 在 WSL 中安装 Redis
wsl
sudo apt update
sudo apt install redis-server
redis-server
```

**方法2：使用 Memurai（Windows Redis 替代品）**
1. 下载 Memurai：https://www.memurai.com/
2. 安装后会自动启动服务
3. 默认端口也是 6379

**方法3：使用 Docker**
```powershell
# 安装 Docker Desktop 后运行
docker run -d -p 6379:6379 redis:latest
```

**方法4：使用 Chocolatey**
```powershell
# 以管理员身份运行 PowerShell
choco install redis-64
# 启动 Redis
redis-server
```

#### 验证 Redis 是否运行

```powershell
# 测试连接
redis-cli ping
# 应该返回: PONG
```

### 方案2：使用其他消息代理（如果不想用 Redis）

可以修改 `settings.py` 使用其他消息代理：

#### 使用 RabbitMQ
```python
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'rpc://'
```

#### 使用数据库（SQLite，仅用于开发）
```python
CELERY_BROKER_URL = 'db+sqlite:///celery.db'
CELERY_RESULT_BACKEND = 'db+sqlite:///celery_results.db'
```

### 方案3：临时禁用 Celery（仅用于测试 API）

如果只是想测试 API 而不需要异步任务，可以：

1. 修改 `fog_node/tasks.py`，将 `@shared_task` 改为同步函数
2. 或者先启动 Redis 再运行 Celery

## 快速启动步骤（推荐：Docker）

### 1. 安装 Docker Desktop
从 https://www.docker.com/products/docker-desktop 下载并安装

### 2. 启动 Redis 容器
```powershell
docker run -d --name redis -p 6379:6379 redis:latest
```

### 3. 验证 Redis 运行
```powershell
docker ps
# 应该看到 redis 容器在运行
```

### 4. 启动 Celery Worker
```powershell
cd D:\Search\privacy_lbs_backend
python -m celery -A privacy_lbs_backend worker --loglevel=info --pool=solo
```

## 常见问题

### Q: Redis 启动后仍然连接失败？
**A:** 检查以下几点：
1. Redis 是否真的在运行：`redis-cli ping`
2. 端口是否正确：默认 6379
3. 防火墙是否阻止了连接

### Q: 不想安装 Redis，有其他选择吗？
**A:** 可以使用：
- RabbitMQ（需要单独安装）
- 数据库作为消息代理（性能较差，仅用于开发）
- 或者修改代码，不使用异步任务

### Q: Windows 上 Redis 安装困难？
**A:** 推荐使用 Docker，这是最简单的方式：
```powershell
docker run -d --name redis -p 6379:6379 redis:latest
```

## 测试 Redis 连接

创建测试脚本 `test_redis.py`：
```python
import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print("✅ Redis 连接成功！")
except Exception as e:
    print(f"❌ Redis 连接失败: {e}")
```

运行：
```powershell
python test_redis.py
```


