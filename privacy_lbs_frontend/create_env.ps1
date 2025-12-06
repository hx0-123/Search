# 创建 .env.development 文件的 PowerShell 脚本

$envFile = ".env.development"
$envContent = @"
# Mapbox访问令牌(需去mapbox.com官网免费注册获取)
VITE_MAPBOX_ACCESS_TOKEN=pk.your_mapbox_token_here

# 后端Django API基础地址
VITE_API_BASE_URL=http://127.0.0.1:8000/api

# WebSocket服务器地址
VITE_WS_URL=ws://127.0.0.1:8000/ws/query_updates/
"@

if (Test-Path $envFile) {
    Write-Host "⚠️  $envFile 文件已存在" -ForegroundColor Yellow
    $overwrite = Read-Host "是否覆盖? (y/n)"
    if ($overwrite -ne "y") {
        Write-Host "已取消操作" -ForegroundColor Red
        exit
    }
}

$envContent | Out-File -FilePath $envFile -Encoding utf8 -NoNewline
Write-Host "✅ $envFile 文件已创建！" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  重要提示：" -ForegroundColor Yellow
Write-Host "   1. 请将 VITE_MAPBOX_ACCESS_TOKEN 替换为真实的Mapbox令牌" -ForegroundColor Yellow
Write-Host "   2. 获取令牌: https://account.mapbox.com/" -ForegroundColor Yellow
Write-Host ""










