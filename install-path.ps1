# AppTalentNavi — PATH に登録して「appnavi」で起動できるようにする
# 使い方: exe があるフォルダ（または dist があるプロジェクトフォルダ）で PowerShell を開き:
#   .\install-path.ps1
# 実行後、新しい PowerShell を開いて「appnavi」と打つと起動します。
#
# 「スクリプトの実行が無効です」と出る場合:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
# を1回実行してから、再度 .\install-path.ps1 を実行してください。

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$distExe = Join-Path $projectRoot "dist\AppTalentNavi.exe"
$sameDirExe = Join-Path $projectRoot "AppTalentNavi.exe"
$installDir = Join-Path $env:LOCALAPPDATA "AppTalentNavi"

# 開発時: dist\AppTalentNavi.exe / リリースZIP解凍後: 同じフォルダの AppTalentNavi.exe
$srcExe = $null
if (Test-Path $distExe) {
    $srcExe = $distExe
} elseif (Test-Path $sameDirExe) {
    $srcExe = $sameDirExe
}
if (-not $srcExe) {
    Write-Host "  AppTalentNavi.exe が見つかりません。"
    Write-Host "  このスクリプトを、exe があるフォルダ（または dist があるプロジェクトフォルダ）で実行してください。"
    exit 1
}

New-Item -ItemType Directory -Force -Path $installDir | Out-Null
Copy-Item -Path $srcExe -Destination (Join-Path $installDir "AppTalentNavi.exe") -Force

$cmdContent = @"
@echo off
"%~dp0AppTalentNavi.exe" %*
"@
Set-Content -Path (Join-Path $installDir "appnavi.cmd") -Value $cmdContent -Encoding ASCII

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$installDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$installDir", "User")
    Write-Host "  PATH に $installDir を追加しました。"
} else {
    Write-Host "  PATH には既に登録済みです。"
}

Write-Host ""
Write-Host "  ╔══════════════════════════════════════╗"
Write-Host "  ║  インストール完了                     ║"
Write-Host "  ╚══════════════════════════════════════╝"
Write-Host ""
Write-Host "  新しい PowerShell を開き、どこからでも次のコマンドで起動できます:"
Write-Host "    appnavi"
Write-Host ""
