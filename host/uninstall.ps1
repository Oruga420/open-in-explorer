# Removes the "Open in Explorer" native messaging host registration.
#
#   powershell -ExecutionPolicy Bypass -File host\uninstall.ps1

$ErrorActionPreference = "Stop"
$HostName = "com.oruga.open_folder"

$keys = @(
    "HKCU:\Software\Google\Chrome\NativeMessagingHosts\$HostName",
    "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\$HostName",
    "HKCU:\Software\BraveSoftware\Brave-Browser\NativeMessagingHosts\$HostName"
)
foreach ($key in $keys) {
    if (Test-Path $key) {
        Remove-Item -Path $key -Force
        Write-Host "Removed $key"
    }
}

$hostDir = Split-Path -Parent $MyInvocation.MyCommand.Path
foreach ($file in @("$HostName.json", "open_folder_host.bat")) {
    $path = Join-Path $hostDir $file
    if (Test-Path $path) { Remove-Item $path -Force; Write-Host "Removed $path" }
}

Write-Host "Done. Remove the extension itself from chrome://extensions."
