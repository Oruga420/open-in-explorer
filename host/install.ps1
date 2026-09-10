# Installs the "Open in Explorer" native messaging host for the current user.
#
#   powershell -ExecutionPolicy Bypass -File host\install.ps1
#
# Optional: -ExtensionId <id>  adds another extension id to allowed_origins
# (use it if you loaded the extension from a copy without the manifest "key").

param(
    [string[]] $ExtensionId = @()
)

$ErrorActionPreference = "Stop"

$HostName    = "com.oruga.open_folder"
$DefaultId   = "dahclepccpmepheckhenjdkfclfhdjib"   # id fixed by manifest "key"
$HostDir     = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyScript    = Join-Path $HostDir "open_folder_host.py"
$BatPath     = Join-Path $HostDir "open_folder_host.bat"
$ManifestPath= Join-Path $HostDir "$HostName.json"

if (-not (Test-Path $PyScript)) { throw "Missing $PyScript" }

# --- locate a Python interpreter (prefer pythonw.exe: no console window) ------
$python = $null
$cmd = Get-Command python.exe -ErrorAction SilentlyContinue
if ($null -ne $cmd) {
    $pythonw = Join-Path (Split-Path -Parent $cmd.Source) "pythonw.exe"
    if (Test-Path $pythonw) { $python = $pythonw } else { $python = $cmd.Source }
}
if ($null -eq $python) {
    $cmd = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -ne $cmd) { $python = $cmd.Source }
}
if ($null -eq $python) { throw "Python not found on PATH. Install Python 3 and re-run." }
Write-Host "Python:    $python"

# --- launcher batch file ------------------------------------------------------
$bat = "@echo off`r`n`"$python`" `"$PyScript`" %*`r`n"
[System.IO.File]::WriteAllText($BatPath, $bat, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Launcher:  $BatPath"

# --- native messaging manifest -----------------------------------------------
$ids = @($DefaultId) + $ExtensionId | Select-Object -Unique
$origins = ($ids | ForEach-Object { '    "chrome-extension://' + $_ + '/"' }) -join ",`r`n"
$escapedBat = $BatPath.Replace('\', '\\')
$json = @"
{
  "name": "$HostName",
  "description": "Open in Explorer - opens a Windows path in File Explorer",
  "path": "$escapedBat",
  "type": "stdio",
  "allowed_origins": [
$origins
  ]
}
"@
[System.IO.File]::WriteAllText($ManifestPath, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Host "Manifest:  $ManifestPath"

# --- register with every Chromium browser present -----------------------------
$browsers = @{
    "Chrome" = "HKCU:\Software\Google\Chrome\NativeMessagingHosts\$HostName"
    "Edge"   = "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\$HostName"
    "Brave"  = "HKCU:\Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\$HostName"
}
foreach ($name in $browsers.Keys) {
    $key = $browsers[$name]
    New-Item -Path $key -Force | Out-Null
    Set-ItemProperty -Path $key -Name "(default)" -Value $ManifestPath
    Write-Host "Registered $name -> $key"
}

Write-Host ""
Write-Host "Done. Allowed extension ids:"
$ids | ForEach-Object { Write-Host "  $_" }
Write-Host "Load the extension folder at chrome://extensions (Developer mode > Load unpacked),"
Write-Host "then restart Chrome so it picks up the new host registration."
