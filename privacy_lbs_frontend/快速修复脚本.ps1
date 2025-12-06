# 快速诊断和修复脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "地图加载问题诊断" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$envFile = ".env.development"

# 1. 检查文件是否存在
Write-Host "1. 检查文件..." -ForegroundColor Yellow
if (Test-Path $envFile) {
    Write-Host "   ✅ 文件存在" -ForegroundColor Green
    
    # 2. 检查文件内容
    Write-Host ""
    Write-Host "2. 检查文件内容..." -ForegroundColor Yellow
    $content = Get-Content $envFile -Raw
    
    if ($content -match "VITE_MAPBOX_ACCESS_TOKEN\s*=\s*(.+)") {
        $token = $matches[1].Trim()
        
        Write-Host "   Token值（前20字符）: $($token.Substring(0, [Math]::Min(20, $token.Length)))..." -ForegroundColor Gray
        
        # 检查Token格式
        if ($token -match '^pk\.') {
            Write-Host "   ✅ Token格式正确（以pk.开头）" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Token格式错误（应该以pk.开头）" -ForegroundColor Red
        }
        
        # 检查是否为默认值
        if ($token -match 'your_token_here|你的真实令牌|your_mapbox_token') {
            Write-Host "   ❌ Token还是默认值，需要替换为真实Token" -ForegroundColor Red
            Write-Host ""
            Write-Host "   获取Token: https://account.mapbox.com/" -ForegroundColor Cyan
        } else {
            Write-Host "   ✅ Token不是默认值" -ForegroundColor Green
        }
        
        # 检查是否有引号
        if ($token -match '^["\''].*["\'']$') {
            Write-Host "   ⚠️  Token值包含引号，这可能导致问题" -ForegroundColor Yellow
            Write-Host "   建议：移除引号" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host "   ❌ 未找到 VITE_MAPBOX_ACCESS_TOKEN 配置" -ForegroundColor Red
    }
    
    # 显示完整内容（隐藏敏感部分）
    Write-Host ""
    Write-Host "3. 文件内容预览:" -ForegroundColor Yellow
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "VITE_MAPBOX_ACCESS_TOKEN") {
            $line = $_ -replace "(VITE_MAPBOX_ACCESS_TOKEN=)(.{20}).*", '$1$2...'
            Write-Host "   $line" -ForegroundColor Gray
        } else {
            Write-Host "   $_" -ForegroundColor Gray
        }
    }
    
} else {
    Write-Host "   ❌ 文件不存在" -ForegroundColor Red
    Write-Host ""
    Write-Host "   创建文件..." -ForegroundColor Yellow
    @"
# Mapbox访问令牌
VITE_MAPBOX_ACCESS_TOKEN=pk.your_mapbox_token_here

# 后端Django API基础地址
VITE_API_BASE_URL=http://127.0.0.1:8000/api

# WebSocket服务器地址
VITE_WS_URL=ws://127.0.0.1:8000/ws/query_updates/
"@ | Out-File -FilePath $envFile -Encoding utf8
    Write-Host "   ✅ 已创建文件，请填入真实的Mapbox Token" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "建议操作：" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. 确保Token是真实的Mapbox令牌（从 https://account.mapbox.com/ 获取）" -ForegroundColor White
Write-Host "2. 确保Token格式正确：VITE_MAPBOX_ACCESS_TOKEN=pk.xxx（无引号，无空格）" -ForegroundColor White
Write-Host "3. 重启开发服务器（修改.env文件后必须重启）" -ForegroundColor White
Write-Host "4. 打开浏览器控制台（F12）查看详细错误信息" -ForegroundColor White
Write-Host ""










