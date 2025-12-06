# Celery Worker 启动说明

## 错误原因

错误信息：`Module 'privacy_lbs_backend' has no attribute 'celery'`

**原因：**
1. **工作目录不正确** - 必须在 `privacy_lbs_backend` 目录下执行命令
2. **Python路径问题** - Celery需要能够找到 `privacy_lbs_backend` 模块

## 正确的启动方式

### 方式1：使用启动脚本（推荐）

**Windows (PowerShell):**
```powershell
cd D:\Search\privacy_lbs_backend
.\start_celery.bat
```

**Windows (CMD):**
```cmd
cd D:\Search\privacy_lbs_backend
start_celery.bat
```

**Linux/Mac:**
```bash
cd /path/to/privacy_lbs_backend
chmod +x start_celery.sh
./start_celery.sh
```

### 方式2：手动启动

**Windows (在 `privacy_lbs_backend` 目录下):**
```bash
cd D:\Search\privacy_lbs_backend
python -m celery -A privacy_lbs_backend worker --loglevel=info --pool=solo
```

**Linux/Mac (在 `privacy_lbs_backend` 目录下):**
```bash
cd /path/to/privacy_lbs_backend
celery -A privacy_lbs_backend worker --loglevel=info
```

### 方式3：使用Django管理命令（如果已配置）

```bash
cd D:\Search\privacy_lbs_backend
python manage.py celeryd
```

## 注意事项

1. **必须在正确的目录下执行**
   - 当前目录必须是 `privacy_lbs_backend`（包含 `manage.py` 的目录）
   - 不能在其他目录（如 `D:\Search`）执行

2. **Windows特殊说明**
   - Windows上建议使用 `--pool=solo` 参数
   - 或者使用 `--pool=threads` 参数

3. **确保Redis已启动**
   - Celery需要Redis作为消息代理
   - 确保Redis服务正在运行

4. **检查Python路径**
   - 确保 `privacy_lbs_backend` 模块可以被导入
   - 可以在Python中测试：`python -c "from privacy_lbs_backend import celery_app"`

## 验证启动成功

启动成功后，你应该看到类似以下的输出：
```
[INFO/MainProcess] Connected to redis://localhost:6379/0
[INFO/MainProcess] celery@hostname ready.
```

## 常见问题

### Q: 仍然报错 "Module 'privacy_lbs_backend' has no attribute 'celery'"
**A:** 检查以下几点：
1. 确保在 `privacy_lbs_backend` 目录下执行
2. 确保 `privacy_lbs_backend/__init__.py` 文件存在且包含 `from .celery import app as celery_app`
3. 确保 `privacy_lbs_backend/celery.py` 文件存在

### Q: 报错 "No module named 'django'"
**A:** 确保已激活虚拟环境并安装了所有依赖：
```bash
# Windows
venv\Scripts\activate
pip install -r requirements.txt

# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
```

### Q: 报错 "Error: No module named 'redis'"
**A:** 确保已安装Redis客户端：
```bash
pip install redis
```

