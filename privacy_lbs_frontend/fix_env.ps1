# 修复环境变量文件脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix .env.development file" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$envFile = ".env.development"
$token = ""

# 备份旧文件并尝试提取Token
if (Test-Path $envFile) {
    Copy-Item $envFile "$envFile.backup" -Force
    Write-Host "[OK] Backed up old file as .env.development.backup" -ForegroundColor Green
    
    # 尝试提取现有Token
    $content = Get-Content $envFile -Raw
    if ($content -match "VITE_MAPBOX_ACCESS_TOKEN\s*=\s*([^\r\n]+)") {
        $token = $matches[1].Trim() -replace '^["\''\s]+|["\''\s]+$', ''
        if ($token -and $token -notmatch "your_token|your_mapbox_token") {
            Write-Host "[OK] Found existing token, will keep it" -ForegroundColor Green
        } else {
            $token = ""
            Write-Host "[WARN] Token is default value, needs replacement" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "[WARN] File does not exist, will create new file" -ForegroundColor Yellow
}

# 如果没有有效Token，使用占位符
if (-not $token) {
    $token = "pk.your_mapbox_token_here"
}

# 创建新文件内容
$newContent = "VITE_MAPBOX_ACCESS_TOKEN=$token`r`nVITE_API_BASE_URL=http://127.0.0.1:8000/api`r`nVITE_WS_URL=ws://127.0.0.1:8000/ws/query_updates/"

# 使用UTF-8无BOM编码写入
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$filePath = Join-Path (Get-Location) $envFile
[System.IO.File]::WriteAllText($filePath, $newContent, $utf8NoBom)

Write-Host ""
Write-Host "[OK] File recreated with UTF-8 encoding" -ForegroundColor Green
Write-Host ""

if ($token -match "your_token|your_mapbox_token") {
    Write-Host "[WARN] Important: Please replace token with real value!" -ForegroundColor Yellow
    Write-Host "   1. Open .env.development file" -ForegroundColor White
    Write-Host "   2. Replace token with real token from https://account.mapbox.com/" -ForegroundColor White
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "1. If token is default value, replace with real token" -ForegroundColor White
Write-Host "2. Stop dev server (Ctrl+C)" -ForegroundColor White
Write-Host "3. Clear Vite cache: Remove-Item -Recurse -Force node_modules\.vite" -ForegroundColor White
Write-Host "4. Restart dev server: npm run dev" -ForegroundColor White
Write-Host "5. Refresh browser (Ctrl+F5)" -ForegroundColor White
Write-Host ""
