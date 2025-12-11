# PowerShell Script to Install Flutter
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "      Installing Flutter SDK              " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$FLUTTER_URL = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.16.9-stable.zip"
$INSTALL_DIR = "C:\src\flutter"
$ZIP_PATH = "$env:TEMP\flutter.zip"

# 1. Create Directory
if (-not (Test-Path "C:\src")) {
    New-Item -ItemType Directory -Force -Path "C:\src" | Out-Null
}

# 2. Download
Write-Host "[1/4] Downloading Flutter (This is large ~1GB)..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $FLUTTER_URL -OutFile $ZIP_PATH

# 3. Extract
Write-Host "[2/4] Extracting to C:\src\flutter..." -ForegroundColor Yellow
Expand-Archive -LiteralPath $ZIP_PATH -DestinationPath "C:\src" -Force

# 4. Add to PATH
Write-Host "[3/4] Adding to User PATH..." -ForegroundColor Yellow
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*C:\src\flutter\bin*") {
    $newPath = "$currentPath;C:\src\flutter\bin"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "      Added to PATH. Please restart terminal to use 'flutter'." -ForegroundColor Green
} else {
    Write-Host "      Already in PATH." -ForegroundColor Green
}

# Cleanup
Remove-Item $ZIP_PATH

Write-Host "[4/4] Installation Complete!" -ForegroundColor Green
Write-Host "Running 'flutter doctor'..."
& "C:\src\flutter\bin\flutter" doctor

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "DONE. You can now build apps." -ForegroundColor Cyan
