# fix_camera_permission.ps1
# Run this script as Administrator to grant camera access to Python/GestureControl
# Right-click this file → "Run with PowerShell" (as Admin)

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  GestureControl - Camera Permission Fix" -ForegroundColor Cyan
Write-Host "  Windows 11 Pro Security Unlock" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "How to run as Admin:" -ForegroundColor Yellow
    Write-Host "  Right-click fix_camera_permission.ps1" -ForegroundColor Yellow
    Write-Host "  -> Run with PowerShell" -ForegroundColor Yellow
    Write-Host "  -> Click Yes on the UAC prompt" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[1/4] Enabling camera access for ALL apps..." -ForegroundColor Green
$basePath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
if (-not (Test-Path $basePath)) {
    New-Item -Path $basePath -Force | Out-Null
}
Set-ItemProperty -Path $basePath -Name "Value" -Value "Allow" -Force
Write-Host "      Done." -ForegroundColor Gray

Write-Host "[2/4] Enabling camera for current user desktop apps..." -ForegroundColor Green
$userPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam"
if (-not (Test-Path $userPath)) {
    New-Item -Path $userPath -Force | Out-Null
}
Set-ItemProperty -Path $userPath -Name "Value" -Value "Allow" -Force

$nonPackaged = "$userPath\NonPackaged"
if (-not (Test-Path $nonPackaged)) {
    New-Item -Path $nonPackaged -Force | Out-Null
}
Set-ItemProperty -Path $nonPackaged -Name "Value" -Value "Allow" -Force
Write-Host "      Done." -ForegroundColor Gray

Write-Host "[3/4] Finding Python and granting camera permission..." -ForegroundColor Green
$pythonPaths = @(
    (Get-Command python -ErrorAction SilentlyContinue)?.Source,
    (Get-Command python3 -ErrorAction SilentlyContinue)?.Source,
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "C:\Python311\python.exe",
    "C:\Python310\python.exe",
    "C:\Python312\python.exe"
)

foreach ($pyPath in $pythonPaths) {
    if ($pyPath -and (Test-Path $pyPath)) {
        Write-Host "      Found Python: $pyPath" -ForegroundColor Gray
        # Encode path as registry key name (replace \ and : with #)
        $keyName = $pyPath -replace "\\", "#" -replace ":", "#"
        $pyKey = "$nonPackaged\$keyName"
        if (-not (Test-Path $pyKey)) {
            New-Item -Path $pyKey -Force | Out-Null
        }
        Set-ItemProperty -Path $pyKey -Name "Value" -Value "Allow" -Force
        Write-Host "      Permission granted for Python." -ForegroundColor Green
        break
    }
}

Write-Host "[4/4] Restarting Camera service..." -ForegroundColor Green
try {
    Stop-Service -Name "FrameServer" -Force -ErrorAction SilentlyContinue
    Start-Sleep 1
    Start-Service -Name "FrameServer" -ErrorAction SilentlyContinue
    Write-Host "      Camera service restarted." -ForegroundColor Gray
} catch {
    Write-Host "      (Camera service restart skipped - not critical)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Green
Write-Host "  DONE! Camera permissions granted." -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Close GestureControl if open" -ForegroundColor White
Write-Host "  2. Right-click run.bat -> Run as administrator" -ForegroundColor White
Write-Host "  3. Click Start in the app" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"
