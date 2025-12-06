# 创建环境变量文件

## 重要提示

由于安全原因，`.env.development` 文件无法自动创建。请按照以下步骤手动创建：

## 步骤1：创建 `.env.development` 文件

在项目根目录 `privacy_lbs_frontend/` 下创建 `.env.development` 文件，内容如下：

```ini
# Mapbox访问令牌(需去mapbox.com官网免费注册获取)
VITE_MAPBOX_ACCESS_TOKEN=pk.your_mapbox_token_here

# 后端Django API基础地址
VITE_API_BASE_URL=http://127.0.0.1:8000/api

# WebSocket服务器地址
VITE_WS_URL=ws://127.0.0.1:8000/ws/query_updates/
```

## 步骤2：获取Mapbox访问令牌

1. 访问 https://account.mapbox.com/
2. 注册/登录账号（免费）
3. 进入 **Access Tokens** 页面
4. 复制默认令牌或创建新令牌
5. 将令牌替换 `.env.development` 中的 `pk.your_mapbox_token_here`

## 步骤3：验证配置

创建文件后，运行项目：

```bash
cd D:\Search\privacy_lbs_frontend
npm run dev
```

在浏览器控制台中应该看到：
- ✅ 环境变量配置正常
- 或者 ⚠️ 环境变量配置警告（如果Mapbox令牌未配置）

## 文件位置

```
privacy_lbs_frontend/
├── .env.development      ← 需要手动创建此文件
├── src/
│   └── config/
│       └── env.ts        ← 已创建，用于访问环境变量
└── ENV_SETUP.md          ← 详细配置说明
```

## 快速创建命令（PowerShell）

在项目根目录执行：

```powershell
@"
# Mapbox访问令牌(需去mapbox.com官网免费注册获取)
VITE_MAPBOX_ACCESS_TOKEN=pk.your_mapbox_token_here

# 后端Django API基础地址
VITE_API_BASE_URL=http://127.0.0.1:8000/api

# WebSocket服务器地址
VITE_WS_URL=ws://127.0.0.1:8000/ws/query_updates/
"@ | Out-File -FilePath .env.development -Encoding utf8
```

## 注意事项

1. ✅ `.env.development` 已在 `.gitignore` 中，不会被提交到版本控制
2. ✅ 环境变量配置文件 `src/config/env.ts` 已创建
3. ⚠️ 记得将 `pk.your_mapbox_token_here` 替换为真实的Mapbox令牌










