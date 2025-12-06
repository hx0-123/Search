"""
测试 Redis 连接
"""
import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=2)
    r.ping()
    print("✅ Redis 连接成功！")
    print(f"Redis 版本: {r.info()['redis_version']}")
except redis.ConnectionError as e:
    print(f"❌ Redis 连接失败: {e}")
    print("\n请确保 Redis 服务器正在运行。")
    print("启动方法：")
    print("1. Docker: docker run -d -p 6379:6379 redis:latest")
    print("2. WSL: redis-server")
    print("3. 或参考 REDIS_SETUP.md 文件")
except Exception as e:
    print(f"❌ 发生错误: {e}")


