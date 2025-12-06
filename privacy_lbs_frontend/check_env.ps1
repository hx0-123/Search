# 环境变量文件检查脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "环境变量文件检查" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "D:\Search\privacy_lbs_frontend"
$parentRoot = "D:\Search"

Write-Host "1. 检查项目目录 ($projectRoot):" -ForegroundColor Yellow
if (Test-Path "$projectRoot\.env.development") {
    Write-Host "   ✅ 找到 .env.development" -ForegroundColor Green
    Write-Host "   文件内容:" -ForegroundColor Gray
    Get-Content "$projectRoot\.env.development" | ForEach-Object {
        if ($_ -match "VITE_MAPBOX_ACCESS_TOKEN") {
            $token = $_ -replace "VITE_MAPBOX_ACCESS_TOKEN=", ""
            if ($token -match "^pk\.") {
                Write-Host "   ✅ Token格式正确: $($token.Substring(0, [Math]::Min(20, $token.Length)))..." -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  Token格式可能不正确: $token" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   $_" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "   ❌ 未找到 .env.development" -ForegroundColor Red
}

Write-Host ""
Write-Host "2. 检查父目录 ($parentRoot):" -ForegroundColor Yellow
if (Test-Path "$parentRoot\.env.development") {
    Write-Host "   ⚠️  在父目录找到 .env.development" -ForegroundColor Yellow
    Write-Host "   ⚠️  注意：Vite需要在项目目录下读取环境变量！" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   解决方案：将文件复制到项目目录" -ForegroundColor Cyan
    Write-Host "   命令：Copy-Item '$parentRoot\.env.development' '$projectRoot\.env.development'" -ForegroundColor Cyan
} else {
    Write-Host "   ✅ 父目录没有 .env.development（正常）" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "建议操作：" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. 确保 .env.development 在项目目录: $projectRoot" -ForegroundColor White
Write-Host "2. 确保Token格式: VITE_MAPBOX_ACCESS_TOKEN=pk.你的令牌" -ForegroundColor White
Write-Host "3. 重启开发服务器（修改.env文件后必须重启）" -ForegroundColor White
Write-Host ""










