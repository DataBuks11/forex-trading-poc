Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ForexTrade - Full Auto Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$bridgeDir = "C:\Users\Piyush Junghare\forex-trading-poc\mt5-bridge"
$mt5Path = "C:\Program Files\MetaTrader 5\terminal64.exe"
$editorPath = "C:\Program Files\MetaTrader 5\metaeditor64.exe"
$expertsDir = "$env:APPDATA\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts"
$bridgeDir_data = "C:\mt5_bridge"

Write-Host "[1/6] Killing existing MT5..." -ForegroundColor Yellow
taskkill /F /IM terminal64.exe 2>$null
taskkill /F /IM metaeditor64.exe 2>$null
Start-Sleep 3

Write-Host "[2/6] Copying EA to MT5 Experts folder..." -ForegroundColor Yellow
Copy-Item "$bridgeDir\bridge.mq5" "$expertsDir\" -Force
New-Item -ItemType Directory -Path $bridgeDir_data -Force | Out-Null
Write-Host "       Done."

Write-Host "[3/6] Starting MT5 terminal..." -ForegroundColor Yellow
Start-Process -FilePath $mt5Path -ArgumentList "/portable"
Write-Host "       Waiting 20s for MT5 to initialize..."
Start-Sleep 20

Write-Host "[4/6] Compiling EA using MetaEditor..." -ForegroundColor Yellow
$compileArgs = "/compile:`"$expertsDir\bridge.mq5`" /log:`"$expertsDir\bridge.log`""
try {
    $proc = Start-Process -FilePath $editorPath -ArgumentList $compileArgs -Wait -NoNewWindow -PassThru
    Start-Sleep 5
    if (Test-Path "$expertsDir\bridge.ex5") {
        Write-Host "       bridge.ex5 compiled successfully!" -ForegroundColor Green
    } else {
        Write-Host "       Compilation may have failed - checking log..." -ForegroundColor Yellow
        if (Test-Path "$expertsDir\bridge.log") {
            Get-Content "$expertsDir\bridge.log" | ForEach-Object { Write-Host "         $_" }
        }
    }
} catch {
    Write-Host "       MetaEditor error: $_" -ForegroundColor Red
}

Write-Host "[5/6] Launching MT5 with EA auto-attached..." -ForegroundColor Yellow
$profileDir = "$env:APPDATA\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\Profiles"
New-Item -ItemType Directory -Path $profileDir -Force | Out-Null

# Create chart template to auto-attach EA
$templateContent = @"
<chart>
id=0
symbol=EURUSD
period=60
expert=bridge
</chart>
"@
$templateContent | Out-File -FilePath "$profileDir\bridge.chr" -Encoding ASCII -Force

Write-Host "       Restarting MT5 one final time..."
taskkill /F /IM terminal64.exe 2>$null
Start-Sleep 3
Start-Process -FilePath $mt5Path -ArgumentList "/portable"
Write-Host "       Waiting 15s for MT5 to load with EA..."
Start-Sleep 15

Write-Host "[6/6] Starting bridge..." -ForegroundColor Yellow
Write-Host ""
Set-Location $bridgeDir
$env:MT5_LOGIN = "732959"
$env:MT5_SERVER = "CXMDirect-Live"
Clear-Host
python bridge.py
